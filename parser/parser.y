%{
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include "symbol_table.h"

    extern int yylineno;
    extern char *yytext;

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
%token MOD 28

%%

program
    : declaration_list
    ;

declaration_list
    : declaration_list declaration
    | declaration
    ;

declaration
    : var_declaration
    | fun_declaration
    ;


var_declaration:
    type_specifier ID SEMICOLON {
        insertSymbol(
            &symtab,
            $2, // variable name
            currentScope,
            SYMBOL_VAR,
            yylineno,
            $1 // type specifier
            );
        free($2);
    };

type_specifier
    : INT
    | VOID
    ;

fun_declaration
    : type_specifier ID LPAREN params RPAREN compound_stmt
    ;

params
    : param_list
    | VOID
    ;

param_list
    : param_list COMMA param
    | param
    ;

param
    : type_specifier ID
    | type_specifier ID LBRACK RBRACK
    ;

compound_stmt
    : LBRACE local_declarations statement_list RBRACE
    ;

local_declarations
    : local_declarations var_declaration
    | /* empty */
    ;

statement_list
    : statement_list statement
    | /* empty */
    ;

statement
    : expression_stmt
    | compound_stmt
    | selection_stmt
    | iteration_stmt
    | return_stmt
    ;

expression_stmt
    : expression SEMICOLON
    | SEMICOLON
    ;

selection_stmt
    : IF LPAREN expression RPAREN statement
    | IF LPAREN expression RPAREN statement ELSE statement
    ;

iteration_stmt
    : WHILE LPAREN expression RPAREN statement
    ;

return_stmt
    : RETURN SEMICOLON
    | RETURN expression SEMICOLON
    ;

expression
    : var ASSIGN expression
    | simple_expression
    ;

var
    : ID
    | ID LBRACK expression RBRACK
    ;

simple_expression
    : additive_expression relop additive_expression
    | additive_expression
    ;

relop
    : LTE
    | LT
    | GT
    | GTE
    | EQ
    | NEQ
    ;

additive_expression
    : additive_expression addop term
    | term
    ;

addop
    : PLUS
    | MINUS
    ;

term
    : term mulop factor
    | factor
    ;

mulop
    : TIMES
    | DIV
    | MOD
    ;

factor
    : LPAREN expression RPAREN
    | var
    | call
    | NUM
    ;

call
    : ID LPAREN args RPAREN
    ;

args
    : arg_list
    | /* empty */
    ;

arg_list
    : arg_list COMMA expression
    | expression
    ;

%%

int yyerror(char *msg) {
    fprintf(
        stderr, "Syntax error at line %d: unexpected '%s'\n",
        yylineno, yytext
        );
    return 1;
}

int parse() {
    initSymbolTable(&symtab);
    printf("Starting syntax analysis...\n");
    int res = yyparse();
    if (res == 0) {
        printf("Syntax analysis completed successfully.\n");
        dumpSymbolTable(&symtab);
    }
    return res;
}

