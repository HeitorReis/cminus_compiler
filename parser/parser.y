%{
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include "syntax_tree.h"
  #include "node.h"
  #include "utils.h"
  #include "symbol_table.h"
  #include "semantic.h"
  
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

%%



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

