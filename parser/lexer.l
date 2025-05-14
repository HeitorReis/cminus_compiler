%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser.tab.h"
#include "node.h"

void ignorar_comentario();
extern int yylineno; // Variável global de linha
extern FILE *input_file; // Adicione esta linha para declarar input_file
extern char *expName; // Variável global para armazenar o nome do identificador
extern char *functionName; // Variável global para armazenar o nome da função
extern char *variableName; // Variável global para armazenar o nome do array
extern int functionCurrentLine;
extern char *currentScope;
extern char *argName;
extern int erro_lexico;
char expLine;
int tokenNUM;
int openBraces = 0;

#define CPY_TK strncpy(token_str, yytext, TOKEN_LEN);
%}

%option yylineno

%%
"if"          { return IF; }
"else"        { return ELSE; }
"while"       { return WHILE; }
"return"      { return RETURN; }
"int"         { return INT; }
"void"        { return VOID; }
"=="          { return EQ; }
"!="          { return NEQ; }
"<"           { return LT; }
"<="          { return LTE; }
">"           { return GT; }
">="          { return GTE; }
"="           { return ASSIGN; }
"+"           { return PLUS; }
"-"           { return MINUS; }
"*"           { return TIMES; }
"/"           { return DIV; }
";"           { return SEMICOLON; }
","           { return COMMA; }
"("           { 
    if (openBraces == 0) {
        functionCurrentLine = yylineno; 
        functionName = strdup(expName);
        if (openBraces == 0) {
            currentScope = strdup(functionName);
        }
    }
    argName = strdup(functionName);
    return LPAREN; }
")"           { return RPAREN; }
"{"           { 
    openBraces++;
    if (openBraces == 1) {
        functionCurrentLine = yylineno;
        currentScope = strdup(functionName);
        // printf("Scope: %s\n", currentScope);
        // printf("Function name: %s\n", functionName);
    }
    return LBRACE; }
"}"           {
    //yylineno++; 
    if (openBraces > 0){
        openBraces--;
    }
    if (openBraces == 0) {
        currentScope = "global";
    }
    return RBRACE; }
"["           { 
    variableName = strdup(expName); 
    return LBRACK; }
"]"           { return RBRACK; }
"/*"          { ignorar_comentario(); }

[0-9]+        { tokenNUM = atoi(yytext);
    return NUM; }
[a-zA-Z_][a-zA-Z0-9_]* {
    // printf("ID: %s   |   scope: %s\n", yytext, currentScope);
    expLine = yylineno;
    expName = strdup(yytext);
    return ID;
} // Assign value to expName for identifiers

[ \t\r]+    { /* Ignorar espaços e quebras de linha */ }

\n            { /*yylineno++;*/ }

<<EOF>>  { return 0; }

.             { printf("ERRO LÉXICO: '%s' LINHA: %i\n", yytext, yylineno); erro_lexico = 1; }
%%

// Função para ignorar comentários
void ignorar_comentario() {
    int c;
    while (1) {
        c = input();
        if (c == '*') {
            c = input();
            if (c == '/') break;
        }
        if (c == 0 || c == EOF) break;  // prevent infinite loop at EOF
    }
}
