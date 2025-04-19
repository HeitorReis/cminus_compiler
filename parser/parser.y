%{
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include "syntax_tree.h"
  #include "node.h"
  #include "utils.h"
  #include "symbol_table.h"
  
  treeNode *syntax_tree;
  SymbolTable tabela;

  extern int tokenNUM;
  extern int parseResult;

  extern char *functionName;
  extern char *currentScope;
  extern char *expName;
  extern int functionCurrentLine;
  extern char *variableName;

  extern char *argName;

  extern int yylineno;
  extern char *yytext;

  void insertSymbolInTable(char *name, char *scope, SymbolType type, int line, primitiveType dataType) {
    Symbol *symbol = findSymbol(&tabela, name, scope);
    if (symbol) {
        addLine(symbol, line);
    } else {
        insertSymbol(&tabela, name, scope, type, line, dataType);
    }
  }
%}

/* Tokens */
%token IF 1 
%token WHILE 2 
%token RETURN 3
%token INT 4 
%token VOID 5 
%token NUM 6 
%token ID 7
%token EQ 8
%token NEQ 9 
%token LT 10
%token LTE 11
%token GT 12
%token GTE 13
%token PLUS 14 
%token MINUS 15 
%token TIMES 16
%token DIV 17
%token ASSIGN 18 
%token SEMICOLON 19
%token COMMA 20
%token LPAREN 21
%token RPAREN 22
%token LBRACE 23
%token RBRACE 24
%token LBRACK 25
%token RBRACK 26
%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%%

programa:
    declaracao_lista {
        syntax_tree = $1;
    }
    ;

declaracao_lista:
    declaracao_lista declaracao {
        $$ = traversal($1, $2);
    }
    | declaracao {
        $$ = $1;;
    }
    ;

declaracao:
    var_declaracao {
        $$ = $1;;
    }
    | fun_declaracao {
        $$ = $1;;
    }
    ;

var_declaracao:
    tipo_especificador ID SEMICOLON {
        $$ = createDeclVarNode(declVar, $1);
        $$->key.name = strdup(yytext);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, $1->type);
    }
    | tipo_especificador ID LBRACK NUM RBRACK SEMICOLON {
        $$ = createArrayDeclVarNode(expNum, declVar, $1);
        $$->key.name = strdup(yytext);
        $$->line = yylineno;
        insertSymbolInTable(expName , currentScope, ARRAY, yylineno, $1->type);
    }

tipo_especificador:
    INT {
        $$ = createDeclNode(declIdType); $$->type = Integer;
    }
    | VOID {
        $$ = createDeclNode(declIdType); $$->type = Void;
    }
    ;

fun_declaracao:
    tipo_especificador ID LPAREN params RPAREN composto_decl {
        $$ = createDeclFuncNode(declFunc, $1, $4, $6); paramsCount = 0;
        int funcLine = functionCurrentLine;
        currentScope = strdup(yytext); // Atualiza o escopo para o nome da função
        insertSymbolInTable(functionName, "global", FUNC, funcLine - 1, $1->type); // Insere a função na tabela de símbolos
    }
    ;


params:
    param_lista {
        $$ = $1;
    }
    | VOID {
        $$ = createEmptyParams(expId);
    }
    ;

param_lista:
    param_lista COMMA param {
        $$ = traversal($1, $3);
    }
    | param {
        $$ = $1;
    }
    ;

param:
    tipo_especificador ID {
        $$ = createDeclVarNode(declVar, $1);
        insertSymbolInTable(expName, currentScope, VAR, yylineno, $1->type); // Insere o parâmetro na tabela de símbolos
    }
    | tipo_especificador ID LBRACK RBRACK {
        $$ = createArrayArg(declVar, $1);
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, $1->type); // Insere o parâmetro array na tabela de símbolos
    }
    ;

composto_decl:
    LBRACE local_declaracoes statement_lista RBRACE {
        $$ = traversal($2, $3);
    }
    | SEMICOLON {
        $$ = NULL;
    }
    | LBRACE local_declaracoes statement_lista fun_declaracao RBRACE {
        $$ = traversal(traversal($2, $3), $4);
    }
    | LBRACE local_declaracoes fun_declaracao statement_lista RBRACE {
        $$ = traversal(traversal($2, $3), $4);
    }
    ;

local_declaracoes:
    local_declaracoes var_declaracao {
        $$ = traversal($1, $2);
    }
    | /* vazio */ {
        $$ = NULL;
    }
    ;

statement_lista:
    statement_lista statement {
        $$ = traversal($1, $2);
    }
    | /* vazio */ {
        $$ = NULL;
    }
    ;

statement:
    expressao_decl {
        $$ = $1;
    }
    | composto_decl {
        $$ = $1;
    }
    | selecao_decl {
        $$ = $1;
    }
    | iteracao_decl {
        $$ = $1;
    }
    | retorno_decl {
        $$ = $1;
    }
    ;

expressao_decl:
    expressao SEMICOLON {
        $$ = $1;
    }
    ;

selecao_decl:
    IF LPAREN expressao RPAREN statement %prec LOWER_THAN_ELSE {
        $$ = createIfStmt(stmtIf, $3, $5, NULL);
    }
    | IF LPAREN expressao RPAREN statement ELSE statement {
        $$ = createIfStmt(stmtIf, $3, $5, $7);
    }
    ;

iteracao_decl:
    WHILE LPAREN expressao RPAREN statement {
        $$ = createWhileStmt(stmtWhile, $3, $5);
    }
    ;

retorno_decl:
    RETURN SEMICOLON {
        $$ = createStmtNode(stmtReturn);
    }
    | RETURN expressao SEMICOLON {
        $$ = createStmtNode(stmtReturn); $$->child[0] = $2;
    }
    ;

expressao:
    var ASSIGN expressao {
        $$ = createAssignStmt(stmtAttrib, $1, $3); $$->key.op = ASSIGN;
    }
    | simples_expressao {
        $$ = $1;
    }
    ;

var:
    ID {
        $$ = createExpVar(expId);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, Integer);
    }
    | ID LBRACK expressao RBRACK {
        $$ = createArrayExpVar(expId, $3);
        $$->line = yylineno;
        insertSymbolInTable(variableName, currentScope, ARRAY, yylineno, Integer);
    }

simples_expressao:
    soma_expressao relacional soma_expressao {
        $$ = createExpOp(expOp, $1, $3); $$->key.op = $2->key.op;
    }
    | soma_expressao {
        $$ = $1;
    }
    ;

relacional:
    LT { $$ = createExpNode(expId); $$->key.op = LT; $$->line = yylineno; }
    | LTE { $$ = createExpNode(expId); $$->key.op = LTE; $$->line = yylineno; }
    | GT { $$ = createExpNode(expId); $$->key.op = GT; $$->line = yylineno; }
    | GTE { $$ = createExpNode(expId); $$->key.op = GTE; $$->line = yylineno; }
    | EQ { $$ = createExpNode(expId); $$->key.op = EQ; $$->line = yylineno; }
    | NEQ { $$ = createExpNode(expId); $$->key.op = NEQ; $$->line = yylineno; }
    ;

soma_expressao:
    soma_expressao soma termo {
        $$ = createExpOp(expOp, $1, $3); $$->key.op = $2->key.op;
    }
    | termo {
        $$ = $1;
    }
    ;

soma:
    PLUS { $$ = createExpNode(expId); $$->key.op = PLUS; }
    | MINUS { $$ = createExpNode(expId); $$->key.op = MINUS; }
    ;

termo:
    termo mult fator {
        $$ = createExpOp(expOp, $1, $3); $$->key.op = $2->key.op;
    }
    | fator {
        $$ = $1;
    }
    ;

mult:
    TIMES { $$ = createExpNode(expId); $$->key.op = TIMES; }
    | DIV { $$ = createExpNode(expId); $$->key.op = DIV; }
    ;

fator:
    LPAREN expressao RPAREN {
        $$ = $1;
    }
    | var {
        $$ = $1;
    }
    | ativacao {
        $$ = $1;
    }
    | NUM {
        $$ = createExpNum(expNum);
    }
    ;

ativacao:
    ID LPAREN args RPAREN {
        $$ = createActivationFunc(stmtFunc, $4);
        $$->line = yylineno;
        insertSymbolInTable(functionName, "global", FUNC, yylineno, Integer);
    }
    ;

args:
    arg_lista {
        $$ = $1;
    }
    | /* vazio */ {
        $$ = NULL;
    }
    ;

arg_lista:
    arg_lista COMMA expressao {
        $$ = traversal($1, $3); argsCount++;
    }
    | expressao {
        $$ = $1; argsCount++;
    }
    | param { 
        $$ = $1; argsCount++;
    }
    ;

%%


int yyerror(char *errorMsg) {
  printf("(!) ERRO SINTATICO: Linha: %d | Token: %s\n", yylineno, yytext);
  return 1;
}

treeNode *parse() {

    parseResult = yyparse(); 
    return syntax_tree; 
}
