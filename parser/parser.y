%{
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include "syntax_tree.h"
  #include "node.h"
  #include "utils.h"
  #include "symbol_table.h"
  #include "semantic.h"

  treeNode *syntax_tree;
  SymbolTable tabela;

  extern int tokenNUM;
  extern int parseResult;
  extern int yylineno;
  extern char *yytext;

  extern char *currentScope;
  extern int   functionCurrentLine;

  /* Para armazenar o nome de IDs válidos */
  char *savedId;

  void insertSymbolInTable(char *name, char *scope,
                           SymbolType type, int line,
                           primitiveType dataType) {
    Symbol *s = findSymbol(&tabela, name, scope);
    if (s) addLine(s, line);
    else  insertSymbol(&tabela, name, scope, type, line, dataType);
  }
%}

%union {
  struct treeNode *node;
  int             num;
  char           *string;
}

/* Tokens */
%token IF WHILE RETURN INT VOID
%token <num> NUM
%token <string> ID
%token PLUS MINUS TIMES DIV ASSIGN
%token EQ NEQ LT LTE GT GTE
%token SEMICOLON COMMA
%token LPAREN RPAREN LBRACE RBRACE LBRACK RBRACK

/* Nonterminals */
%type <node> programa declaracao_lista declaracao
%type <node> tipo_especificador var_declaracao fun_declaracao params param_lista param composto_decl
%type <node> local_declaracoes statement_lista statement expressao_decl selecao_decl iteracao_decl retorno_decl
%type <node> expressao args arg_lista

/* Precedência e associatividade */
%right ASSIGN
%left EQ NEQ
%left LT LTE GT GTE
%left PLUS MINUS
%left TIMES DIV
%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%%

programa
  : declaracao_lista
      { syntax_tree = $1.node; }
  ;

declaracao_lista
  : declaracao_lista declaracao
      { $$.node = traversal($1.node, $2.node); }
  | declaracao
      { $$.node = $1.node; }
  ;

declaracao
  : var_declaracao
      { $$.node = $1.node; }
  | fun_declaracao
      { $$.node = $1.node; }
  ;

/* — tipo int ou void — */
tipo_especificador
  : INT
      { $$.node = createDeclNode(declIdType);
        $$.node->type = Integer; }
  | VOID
      { $$.node = createDeclNode(declIdType);
        $$.node->type = Void; }
  ;

/* — declaração de variável — */
var_declaracao
  : tipo_especificador ID SEMICOLON
      {
        $$.node = createDeclVarNode(declVar, $1.node);
        $$.node->key.name = $2.string;
        $$.node->line     = yylineno;
        insertSymbolInTable($2.string,
                            currentScope,
                            VAR,
                            yylineno,
                            $1.node->type);
      }
  | tipo_especificador ID LBRACK NUM RBRACK SEMICOLON
      {
        $$.node = createArrayDeclVarNode(expNum, declVar, $1.node);
        $$.node->key.name = $2.string;
        $$.node->key.value = $4.num;
        $$.node->line     = yylineno;
        insertSymbolInTable($2.string,
                            currentScope,
                            ARRAY,
                            yylineno,
                            $1.node->type);
      }
  ;

/* — declaração de função — */
fun_declaracao
  : tipo_especificador ID LPAREN
      {
        functionCurrentLine = yylineno;
        currentScope = strdup($2.string);
      }
    params RPAREN composto_decl
      {
        $$.node = createDeclFuncNode(declFunc,
                                     $1.node,
                                     $5.node,
                                     $7.node);
        insertSymbolInTable($2.string,
                            "global",
                            FUNC,
                            functionCurrentLine,
                            $1.node->type);
      }
  ;

/* — parâmetros — */
params
  : param_lista
      { $$.node = $1.node; }
  | VOID
      { $$.node = createEmptyParams(expId); }
  | /* empty */
      { $$.node = NULL; }
  ;

param_lista
  : param_lista COMMA param
      { $$.node = traversal($1.node, $3.node); }
  | param
      { $$.node = $1.node; }
  ;

param
  : tipo_especificador ID
      {
        $$.node = createDeclVarNode(declVar, $1.node);
        $$.node->key.name = $2.string;
        $$.node->line = yylineno;
        insertSymbolInTable($2.string,
                            currentScope,
                            VAR,
                            yylineno,
                            $1.node->type);
      }
  | tipo_especificador ID LBRACK RBRACK
      {
        $$.node = createArrayArg(declVar, $1.node);
        $$.node->key.name = $2.string;
        $$.node->line = yylineno;
        insertSymbolInTable($2.string,
                            currentScope,
                            ARRAY,
                            yylineno,
                            $1.node->type);
      }
  ;

/* — bloco — */
composto_decl
  : LBRACE local_declaracoes statement_lista RBRACE
      { $$.node = traversal($2.node, $3.node); }
  ;

/* — declarações locais — */
local_declaracoes
  : local_declaracoes var_declaracao
      { $$.node = traversal($1.node, $2.node); }
  | /* empty */
      { $$.node = NULL; }
  ;

/* — lista de statements — */
statement_lista
  : statement_lista statement
      { $$.node = traversal($1.node, $2.node); }
  | /* empty */
      { $$.node = NULL; }
  ;

/* — statements — */
statement
  : expressao_decl     { $$.node = $1.node; }
  | composto_decl       { $$.node = $1.node; }
  | selecao_decl        { $$.node = $1.node; }
  | iteracao_decl       { $$.node = $1.node; }
  | retorno_decl        { $$.node = $1.node; }
  ;

/* — expressão seguida de ponto‐e‐vírgula — */
expressao_decl
  : expressao SEMICOLON
      { $$.node = $1.node; }
  ;

/* — if / if‐else — */
selecao_decl
  : IF LPAREN expressao RPAREN statement %prec LOWER_THAN_ELSE
      { $$.node = createIfStmt(stmtIf,
                                $3.node,
                                $5.node,
                                NULL); }
  | IF LPAREN expressao RPAREN statement ELSE statement
      { $$.node = createIfStmt(stmtIf,
                                $3.node,
                                $5.node,
                                $7.node); }
  ;

/* — while — */
iteracao_decl
  : WHILE LPAREN expressao RPAREN statement
      { $$.node = createWhileStmt(stmtWhile,
                                   $3.node,
                                   $5.node); }
  ;

/* — return — */
retorno_decl
  : RETURN SEMICOLON
      { $$.node = createStmtNode(stmtReturn); }
  | RETURN expressao SEMICOLON
      {
        $$.node = createStmtNode(stmtReturn);
        $$.node->child[0] = $2.node;
      }
  ;

/* — expressões — */
expressao
  : ID LPAREN args RPAREN
      {
        $$.node = createExpCallNode($1.string, $3.node);
        $$.node->line = yylineno;
      }
  | ID
      {
        $$.node = createExpVar(expId);
        $$.node->key.name = $1.string;
        $$.node->line     = yylineno;
      }
  | NUM
      {
        $$.node = createExpNum(expNum);
        $$.node->key.value = $1.num;
        $$.node->line      = yylineno;
      }
  | LPAREN expressao RPAREN
      { $$.node = $2.node; }
  | expressao ASSIGN expressao
      {
        $$.node = createAssignStmt(stmtAttrib,
                                   $1.node,
                                   $3.node);
        $$.node->key.op = ASSIGN;
      }
  | expressao PLUS expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = PLUS;
      }
  | expressao MINUS expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = MINUS;
      }
  | expressao TIMES expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = TIMES;
      }
  | expressao DIV expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = DIV;
      }
  | expressao EQ expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = EQ;
      }
  | expressao NEQ expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = NEQ;
      }
  | expressao LT expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = LT;
      }
  | expressao LTE expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = LTE;
      }
  | expressao GT expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = GT;
      }
  | expressao GTE expressao
      {
        $$.node = createExpOp(expOp,
                              $1.node,
                              $3.node);
        $$.node->key.op = GTE;
      }
  ;

/* — lista de argumentos — */
args
  : arg_lista        { $$.node = $1.node; }
  | /* empty */      { $$.node = NULL; }
  ;

arg_lista
  : arg_lista COMMA expressao
      { $$.node = traversal($1.node, $3.node); }
  | expressao
      { $$.node = $1.node; }
  ;

%%

/* Função de tratamento de erros sintáticos */
int yyerror(const char *msg) {
    (void)msg;  /* evitamos warning de parâmetro não usado */
    fprintf(stderr,
            "(!) ERRO SINTÁTICO: Linha %d, Token `%s`\n",
            yylineno, yytext);
    return 1;
}

/* Inicia a análise sintática e retorna a árvore */
treeNode *parse(void) {
    parseResult = yyparse();
    return syntax_tree;
}
