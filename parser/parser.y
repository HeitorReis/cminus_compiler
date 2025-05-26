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

  extern functionStack **functionStackRef;
  extern FunctionDeclStack **functionDeclStackRef;

  extern int tokenNUM;
  extern int parseResult;

  extern char *currentScope;
  extern char *expName;
  extern int functionCurrentLine;
  extern char *variableName;

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

//   yydebug = 1;
//   %debug
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
%token ELSE 27


%%

program:
    declaration_list {
        printf("Program parsed successfully.\n");
        syntax_tree = $1;
    }
    ;

declaration_list:
    declaration_list declaration {
        $$ = traversal($1, $2);
    }
    | declaration {
        $$ = $1;
    }
    ;

declaration:
    var_declaration {
        $$ = $1;
    }
    | fun_declaration {
        $$ = $1;
    }
    ;

var_declaration:
    type_specifier ID SEMICOLON {
        $$ = createDeclVarNode(declVar, $1);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, $1->type);
    }
  | type_specifier ID LBRACK NUM RBRACK SEMICOLON {
        $$ = createArrayDeclVarNode(declVar, $1, tokenNUM);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, $1->type);
    }
    ;

type_specifier:
    INT {
        $$ = createDeclNode(declIdType); $$->type = Integer;
    }
    | VOID {
        $$ = createDeclNode(declIdType); $$->type = Void;
    }
    ;

fun_declaration:
    type_specifier ID LPAREN params RPAREN compound_decl {
        /* 1) Announce & push the new function’s name */
        printf("Function declaration: %s at line %d\n", expName, yylineno);
        pushFunctionDecl(functionDeclStackRef, expName, yylineno);
        currentScope = strdup(expName);

        /* 2) Build the function‐declaration node while the name is still on the stack */
        $$ = createDeclFuncNode(functionDeclStackRef,
                                declFunc,
                                $1,    /* return-type node */
                                $4,    /* params */
                                $6);   /* body */

        /* 3) Pop it and restore the enclosing scope */
        popFunctionDecl(functionDeclStackRef);
        {
            const char *prev = getCurrentFunctionName(*functionDeclStackRef);
            currentScope = prev ? strdup(prev) : strdup("global");
        }
    }
    ;

params:
    param_list {
        $$ = $1;
    }
    | VOID {
        $$ = createEmptyParams(expId);
    }
    ;

param_list:
    param_list COMMA param {
        $$ = traversal($1, $3);
    }
    | param {
        $$ = $1;
    }
    ;

param:
    type_specifier ID {
        $$ = createDeclVarNode(declVar, $1);
        insertSymbolInTable(expName, currentScope, VAR, yylineno, $1->type);
    }
    | type_specifier ID LBRACK RBRACK {
        $$ = createArrayArg(declVar, $1);
        insertSymbolInTable(expName, currentScope, ARRAY, yylineno, $1->type);
    }
    ;

compound_decl:
    LBRACE local_declarations statement_list RBRACE {
        $$ = traversal($2, $3);
    }
;

local_declarations:
    local_declarations var_declaration {
        $$ = traversal($1, $2);
    }
    | /* empty */ {
        $$ = NULL;
    }
    ;

statement_list:
    statement_list statement {
        $$ = traversal($1, $2);
    }
    | /* empty */ {
        $$ = NULL;
    }
    ;

statement:
    matched_stmt
  | unmatched_stmt
;

/* Safely matched IF with ELSE or non-IF statements */
matched_stmt:
    IF LPAREN expression RPAREN matched_stmt ELSE matched_stmt {
        $$ = createIfStmt(stmtIf, $3, $5, $7);
    }
  | other_stmt {
        $$ = $1;
    }
;

/* Potentially dangling IFs */
unmatched_stmt:
    IF LPAREN expression RPAREN statement {
        $$ = createIfStmt(stmtIf, $3, $5, NULL);
    }
  | IF LPAREN expression RPAREN matched_stmt ELSE unmatched_stmt {
        $$ = createIfStmt(stmtIf, $3, $5, $7);
    }
;

/* All other kinds of statements */
other_stmt:
    expression_decl {
        $$ = $1;
    }
  | compound_decl {
        $$ = $1;
    }
  | iteration_decl {
        $$ = $1;
    }
  | return_decl {
        $$ = $1;
    }
;

expression_decl:
    expression SEMICOLON {
        $$ = $1;
    }
    ;


iteration_decl:
    WHILE LPAREN expression RPAREN statement {
        $$ = createWhileStmt(stmtWhile, $3, $5);
    }
    ;

return_decl:
    RETURN SEMICOLON {
        $$ = createStmtNode(stmtReturn);
    }
    | RETURN expression SEMICOLON {
        $$ = createStmtNode(stmtReturn); $$->child[0] = $2;
    }
    ;

expression:
    var ASSIGN expression {
        $$ = createAssignStmt(stmtAttrib, $1, $3); $$->op = ASSIGN;
    }
    | simple_expression {
        $$ = $1;
    }
    ;

var:
    ID {
        $$ = createExpVar(expId);
        $$->line = yylineno;
        insertSymbolInTable(expName, currentScope, VAR, yylineno, Integer);
    }
    | ID LBRACK expression RBRACK {
        $$ = createArrayExpVar(expId, $3);
        $$->line = yylineno;
        insertSymbolInTable(variableName, currentScope, ARRAY, yylineno, Integer);
    }
    ;

simple_expression:
    sum_expression relational sum_expression {
        $$ = createExpOp(expOp, $1, $3); $$->op = $2->op;
    }
    | sum_expression {
        $$ = $1;
    }
    ;

relational:
    LT  { $$ = createExpNode(expId); $$->op = LT;  $$->line = yylineno; }
    | LTE { $$ = createExpNode(expId); $$->op = LTE; $$->line = yylineno; }
    | GT  { $$ = createExpNode(expId); $$->op = GT;  $$->line = yylineno; }
    | GTE { $$ = createExpNode(expId); $$->op = GTE; $$->line = yylineno; }
    | EQ  { $$ = createExpNode(expId); $$->op = EQ;  $$->line = yylineno; }
    | NEQ { $$ = createExpNode(expId); $$->op = NEQ; $$->line = yylineno; }
    ;

sum_expression:
    sum_expression sum term {
        $$ = createExpOp(expOp, $1, $3); $$->op = $2->op;
    }
    | term {
        $$ = $1;
    }
    ;

sum:
    PLUS  { $$ = createExpNode(expId); $$->op = PLUS; }
    | MINUS { $$ = createExpNode(expId); $$->op = MINUS; }
    ;

term:
    term mult factor {
        $$ = createExpOp(expOp, $1, $3); $$->op = $2->op;
    }
    | factor {
        $$ = $1;
    }
    ;

mult:
    TIMES { $$ = createExpNode(expId); $$->op = TIMES; }
    | DIV   { $$ = createExpNode(expId); $$->op = DIV;   }
    ;

factor:
    LPAREN expression RPAREN {
        $$ = $1;
    }
    | var {
        $$ = $1;
    }
    | call {
        $$ = $1;
    }
    | NUM {
        $$ = createExpNum(expNum);
    }
    ;

call:
    ID LPAREN args RPAREN {
        $$ = createExpCallNode(strdup(expName), $3);
        $$->line = yylineno;
    }
    ;

args:
    arg_list {
        $$ = $1;
    }
    | /* empty */ {
        $$ = NULL;
    }
    ;

arg_list:
    arg_list COMMA expression {
        $$ = traversal($1, $3); argsCount++;
    }
    | expression {
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
    extern int yydebug;
    // yydebug = 1;

    printf("Parsing...\n");
    parseResult = yyparse();
    if (parseResult == 0) {
        printf("Parsing completed successfully.\n");
    } else {
        printf("Parsing failed.\n");
    } 
    return syntax_tree; 
}

