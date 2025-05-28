%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h> 
#include "parser.tab.h"   

extern int yylineno;        
int tokenNUM;               

void ignore_comment();      
%}

%option yylineno

%%

"/*"            { ignore_comment(); 
                printf("[LEX][%d] SKIP_COMMENT\n", yylineno);
                }

"if"           { printf("[LEX][%d] IF       -> '%s'\n", yylineno, yytext); return IF; }
"else"         { printf("[LEX][%d] ELSE     -> '%s'\n", yylineno, yytext); return ELSE; }
"while"        { printf("[LEX][%d] WHILE    -> '%s'\n", yylineno, yytext); return WHILE; }
"return"       { printf("[LEX][%d] RETURN   -> '%s'\n", yylineno, yytext); return RETURN; }
"int"          { printf("[LEX][%d] INT      -> '%s'\n", yylineno, yytext); return INT; }
"void"         { printf("[LEX][%d] VOID     -> '%s'\n", yylineno, yytext); return VOID; }
"=="          { printf("[LEX][%d] EQ       -> '%s'\n", yylineno, yytext); return EQ; }
"!="          { printf("[LEX][%d] NEQ      -> '%s'\n", yylineno, yytext); return NEQ; }
"<="          { printf("[LEX][%d] LTE      -> '%s'\n", yylineno, yytext); return LTE; }
"<"           { printf("[LEX][%d] LT       -> '%s'\n", yylineno, yytext); return LT; }
">="          { printf("[LEX][%d] GTE      -> '%s'\n", yylineno, yytext); return GTE; }
">"           { printf("[LEX][%d] GT       -> '%s'\n", yylineno, yytext); return GT; }
"="           { printf("[LEX][%d] ASSIGN   -> '%s'\n", yylineno, yytext); return ASSIGN; }
"+"           { printf("[LEX][%d] PLUS     -> '%s'\n", yylineno, yytext); return PLUS; }
"-"           { printf("[LEX][%d] MINUS    -> '%s'\n", yylineno, yytext); return MINUS; }
"*"           { printf("[LEX][%d] TIMES    -> '%s'\n", yylineno, yytext); return TIMES; }
"%"         { printf("[LEX][%d] MOD      -> '%s'\n", yylineno, yytext); return MOD; }  
"/"          { printf("[LEX][%d] DIV      -> '%s'\n", yylineno, yytext); return DIV; }
";"           { printf("[LEX][%d] SEMI     -> '%s'\n", yylineno, yytext); return SEMICOLON; }
","           { printf("[LEX][%d] COMMA    -> '%s'\n", yylineno, yytext); return COMMA; }
"("           { printf("[LEX][%d] LPAREN   -> '%s'\n", yylineno, yytext); return LPAREN; }
")"           { printf("[LEX][%d] RPAREN   -> '%s'\n", yylineno, yytext); return RPAREN; }
"{"           { printf("[LEX][%d] LBRACE   -> '%s'\n", yylineno, yytext); return LBRACE; }
"}"           { printf("[LEX][%d] RBRACE   -> '%s'\n", yylineno, yytext); return RBRACE; }
"["           { printf("[LEX][%d] LBRACK   -> '%s'\n", yylineno, yytext); return LBRACK; }
"]"           { printf("[LEX][%d] RBRACK   -> '%s'\n", yylineno, yytext); return RBRACK; }

[0-9]+        { 
                tokenNUM = atoi(yytext);
                yylval.ival = atoi(yytext);
                printf("[LEX][%d] NUM      -> '%s' (%d)\n", yylineno, yytext, tokenNUM);
                return NUM;
                }

[a-zA-Z_][a-zA-Z0-9_]* {
                printf("[LEX][%d] ID       -> '%s'\n", yylineno, yytext);
                yylval.sval = strdup(yytext);
                return ID;
                }

[ \t\r]+      { /* skip whitespace */ }
\n            { /* skip newline; yylineno auto-incremented */ }

<<EOF>>       { printf("[LEX][%d] EOF\n", yylineno); return 0; }

.             { fprintf(stderr, "[LEX][%d] ERROR: unexpected '%s'\n", yylineno, yytext); }

%%

void ignore_comment() {
    int c;
    while ((c = input()) != 0) {
        if (c == '*') {
            int d = input();
            if (d == '/') break;
            unput(d);
        }
        if (c == '\n') yylineno++;
    }
}