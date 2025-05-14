%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "syntax_tree.h"
#include "node.h"
#include "utils.h"
#include "symbol_table.h"
#include "semantic.h"

treeNode    *syntax_tree;
SymbolTable  tabela;

extern int   tokenNUM;
extern int   parseResult;
extern int   yylineno;
extern char *yytext;

/* variáveis vindas de syntax_tree.c */
extern char *expName;
extern char *variableName;
extern char *currentScope;
extern int   functionCurrentLine;

/* armazenamento temporário do lexema de ID */
char *savedId;

void insertSymbolInTable(char *name, char *scope,
                         SymbolType type, int line,
                         primitiveType dataType) {
    Symbol *s = findSymbol(&tabela, name, scope);
    if (s) addLine(s, line);
    else  insertSymbol(&tabela, name, scope, type, line, dataType);
}
%}

/* — Valor-semântico: nó da AST, lexema de ID, ou número — */
%union {
    struct treeNode *node;
    char     *string;
    int       num;
}

/* — Tokens com seus tipos — */
%token <string> ID
%token <num>    NUM
%token          IF WHILE RETURN INT VOID
%token          PLUS MINUS TIMES DIV ASSIGN
%token          EQ NEQ LT LTE GT GTE
%token          SEMICOLON COMMA LPAREN RPAREN
%token          LBRACE RBRACE LBRACK RBRACK

/* — Não-terminais que produzem nós da AST — */
%type <node>
    programa declaracao_lista declaracao
    tipo_especificador var_declaracao fun_declaracao
    params param_lista param
    composto_decl local_declaracoes statement_lista statement
    expressao_decl selecao_decl iteracao_decl retorno_decl
    expressao args arg_lista

/* — Precedência e associatividade — */
%right    ASSIGN
%left     EQ NEQ
%left     LT LTE GT GTE
%left     PLUS MINUS
%left     TIMES DIV
%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%%

programa
  : declaracao_lista
      { syntax_tree = $1; }
  ;

declaracao_lista
  : declaracao_lista declaracao
      { $$ = traversal($1, $2); }
  | declaracao
      { $$ = $1; }
  ;

declaracao
  : var_declaracao
      { $$ = $1; }
  | fun_declaracao
      { $$ = $1; }
  ;

/* — tipo int ou void — */
tipo_especificador
  : INT
      { $$ = createDeclNode(declIdType);
        $$->type = Integer; }
  | VOID
      { $$ = createDeclNode(declIdType);
        $$->type = Void; }
  ;

/* — declaração de variável — */
var_declaracao
  : tipo_especificador ID SEMICOLON
      {
        /* só lexemas verdadeiros de ID em savedId */
        savedId = strdup($2);
        $$ = createDeclVarNode(declVar, $1);
        $$->key.name = savedId;
        $$->line     = yylineno;
        insertSymbolInTable(savedId,
                            currentScope,
                            VAR,
                            yylineno,
                            $1->type);
      }
  | tipo_especificador ID LBRACK NUM RBRACK SEMICOLON
      {
        savedId = strdup($2);
        $$ = createArrayDeclVarNode(expNum, declVar, $1);
        $$->key.name = savedId;
        $$->line     = yylineno;
        insertSymbolInTable(savedId,
                            currentScope,
                            ARRAY,
                            yylineno,
                            $1->type);
      }
  ;

/* — declaração de função — */
fun_declaracao
  : tipo_especificador ID LPAREN params RPAREN composto_decl
      {
        savedId = strdup($2);
        $$ = createDeclFuncNode(declFunc,
                                     $1,
                                     $4,
                                     $6);
        functionCurrentLine = yylineno;
        currentScope        = strdup(savedId);
        insertSymbolInTable(savedId,
                            "global",
                            FUNC,
                            functionCurrentLine - 1,
                            $1->type);
      }
  ;

/* — parâmetros — */
params
  : param_lista
      { $$ = $1; }
  | VOID
      { $$ = createEmptyParams(expId); }
  | /* empty */
      { $$ = NULL; }
  ;

param_lista
  : param_lista COMMA param
      { $$ = traversal($1, $3); }
  | param
      { $$ = $1; }
  ;

param
  : tipo_especificador ID
      {
        savedId = strdup($2);
        $$ = createDeclVarNode(declVar, $1);
        insertSymbolInTable(savedId,
                            currentScope,
                            VAR,
                            yylineno,
                            $1->type);
      }
  | tipo_especificador ID LBRACK RBRACK
      {
        savedId = strdup($2);
        $$ = createArrayArg(declVar, $1);
        insertSymbolInTable(savedId,
                            currentScope,
                            ARRAY,
                            yylineno,
                            $1->type);
      }
  ;

/* — bloco — */
composto_decl
  : LBRACE local_declaracoes statement_lista RBRACE
      { $$ = traversal($2, $3); }
  ;

/* — declarações locais — */
local_declaracoes
  : local_declaracoes var_declaracao
      { $$ = traversal($1, $2); }
  | /* empty */
      { $$ = NULL; }
  ;

/* — lista de statements — */
statement_lista
  : statement_lista statement
      { $$ = traversal($1, $2); }
  | /* empty */
      { $$ = NULL; }
  ;

/* — statements — */
statement
  : expressao_decl
      { $$ = $1; }
  | composto_decl
      { $$ = $1; }
  | selecao_decl
      { $$ = $1; }
  | iteracao_decl
      { $$ = $1; }
  | retorno_decl
      { $$ = $1; }
  ;

/* — expressão seguida de ponto‐e‐vírgula — */
expressao_decl
  : expressao SEMICOLON
      { $$ = $1; }
  ;

/* — if / if-else — */
selecao_decl
  : IF LPAREN expressao RPAREN statement %prec LOWER_THAN_ELSE
      { $$ = createIfStmt(stmtIf,
                                $3,
                                $5,
                                NULL); }
  | IF LPAREN expressao RPAREN statement ELSE statement
      { $$ = createIfStmt(stmtIf,
                                $3,
                                $5,
                                $7); }
  ;

/* — while — */
iteracao_decl
  : WHILE LPAREN expressao RPAREN statement
      { $$ = createWhileStmt(stmtWhile,
                                   $3,
                                   $5); }
  ;

/* — return — */
retorno_decl
  : RETURN SEMICOLON
      { $$ = createStmtNode(stmtReturn); }
  | RETURN expressao SEMICOLON
      {
        $$ = createStmtNode(stmtReturn);
        $$->child[0] = $2;
      }
  ;

/* — expressões — */
expressao
  : ID LPAREN args RPAREN
      {
        $$ = createExpCallNode($1,
                                    $3);
        $$->line = yylineno;
      }
  | ID
      {
        $$ = createExpVar(expId);
        $$->key.name = $1;
        $$->line     = yylineno;
      }
  | NUM
      {
        $$ = createExpNum(expNum);
        $$->key.value = $1;
        $$->line      = yylineno;
      }
  | LPAREN expressao RPAREN
      { $$ = $2; }
  | expressao ASSIGN expressao
      {
        $$ = createAssignStmt(stmtAttrib,
                                   $1,
                                   $3);
        $$->key.op = ASSIGN;
      }
  | expressao PLUS expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = PLUS;
      }
  | expressao MINUS expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = MINUS;
      }
  | expressao TIMES expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = TIMES;
      }
  | expressao DIV expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = DIV;
      }
  | expressao EQ expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = EQ;
      }
  | expressao NEQ expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = NEQ;
      }
  | expressao LT expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = LT;
      }
  | expressao LTE expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = LTE;
      }
  | expressao GT expressao
      { 
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = GT;
      }
  | expressao GTE expressao
      {
        $$ = createExpOp(expOp,
                              $1,
                              $3);
        $$->key.op = GTE;
      }
  ;

/* — lista de argumentos — */
args
  : arg_lista
      { $$ = $1; }
  | /* empty */
      { $$ = NULL; }
  ;

arg_lista
  : arg_lista COMMA expressao
      { $$ = traversal($1, $3); }
  | expressao
      { $$ = $1; }
  ;

%%

int yyerror(const char *msg) {
    fprintf(stderr, "(!) ERRO SINTÁTICO: Linha %d, Token `%s`\n",
            yylineno, yytext);
    return 1;
}

treeNode *parse(void) {
    parseResult = yyparse();
    return syntax_tree;
}
