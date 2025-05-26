%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void ignorar_comentario();

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
"("           { return LPAREN; }
")"           { return RPAREN; }
"{"           { return LBRACE; }
"}"           { return RBRACE; }
"["           { return LBRACK; }
"]"           { return RBRACK; }
"/*"          { ignorar_comentario(); }

[0-9]+        { tokenNUM = atoi(yytext); return NUM; }
[a-zA-Z_][a-zA-Z0-9_]* { return ID; }

[ \t\r]+      { /* Ignorar espaços e quebras de linha */ }

\n            { /* Ignorar novas linhas */ }

<<EOF>>       { return 0; }

.             { printf("ERRO LÉXICO: '%s' LINHA: %i\n", yytext, yylineno); }
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
