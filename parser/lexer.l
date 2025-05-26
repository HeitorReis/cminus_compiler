%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser.tab.h"
#include "syntax_tree.h"
#include "node.h"

void ignorar_comentario();
extern int yylineno; // Variável global de linha
extern FILE *input_file; // Adicione esta linha para declarar input_file
extern char *expName; // Variável global para armazenar o nome do identificador
extern char *variableName; // Variável global para armazenar o nome do array
extern char *currentScope;
extern functionStack **functionStackRef;
extern FunctionDeclStack **functionDeclStackRef;

int tokenNUM;
int openBraces = 0;

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
    if(expName) {
        printf("-----------> pushing Function Stack >>%s<< - >>%i<<\n", expName, yylineno);
        pushFunctionStack(functionStackRef, expName, yylineno);
        printf("Current stack:\n");
        printFunctionStack(*functionStackRef);
        printf("\n");

    } else {
        printf("-----------> pushing Function Stack >>%s<< - >>%i<<\n", expName, yylineno);
        pushFunctionStack(functionStackRef, "global", yylineno);
        printf("Current stack:\n");
        printFunctionStack(*functionStackRef);
        printf("\n");
    }
    return LPAREN; 
}
")"           {
    printf("-----------> popping Function Stack\n");
    popFunctionStack(functionStackRef);
    printf("Current stack:\n");
    printFunctionStack(*functionStackRef);
    printf("\n");
    return RPAREN;
}
"{"           { openBraces++;
    #if DEBUG_FUNCTION_STACK
        printf("-----------> entering brace, nesting now = %d\n", openBraces);
    #endif
    if (openBraces == 1) {
        #if DEBUG_FUNCTION_STACK
            printf("-----------> PUSH Function Declaration >>%s<< at line %d\n",
                    expName ? expName : "<unnamed>", yylineno);
        #endif
        pushFunctionDecl(functionDeclStackRef, expName, yylineno);
        #if DEBUG_FUNCTION_STACK
            printFunctionDeclStack(*functionDeclStackRef);
        #endif
        currentScope = strdup(getCurrentFunctionName(*functionDeclStackRef));
        #if DEBUG_FUNCTION_STACK
            printf("-----------> new currentScope = %s\n\n", currentScope);
        #endif
    }
    return LBRACE;
}
"}"  {
    openBraces--;
    /* always print nesting if debug is on */
    #if DEBUG_FUNCTION_STACK
        printf("-----------> exiting brace, nesting now = %d\n", openBraces);
    #endif
    /* only pop on the *closing* brace of a function */
    if (openBraces == 0) {
        /* show what we’re popping */
        #if DEBUG_FUNCTION_STACK
            printf("-----------> POP Function Declaration >>%s<<\n",
                    getCurrentFunctionName(*functionDeclStackRef));
        #endif
        popFunctionDecl(functionDeclStackRef);
        /* dump the whole decl-stack */
        #if DEBUG_FUNCTION_STACK
            printFunctionDeclStack(*functionDeclStackRef);
        #endif
        {
            char *prev = getCurrentFunctionName(*functionDeclStackRef);
            if (prev) {
                currentScope = strdup(prev);
                #if DEBUG_FUNCTION_STACK
                    printf("-----------> restored currentScope = %s\n\n",
                            currentScope);
                #endif
            } else {
                currentScope = "global";
                #if DEBUG_FUNCTION_STACK
                    printf("-----------> restored currentScope = global\n\n");
                #endif
            }
        }
    }
    return RBRACE;
}
"["           { 
    variableName = strdup(expName); 
    return LBRACK;
}
"]"           { return RBRACK; }
"/*"          { printf("Ignorando comentário...");ignorar_comentario();printf("Comentário ignorado.\n\n"); }

[0-9]+        { tokenNUM = atoi(yytext);
    return NUM; }
[a-zA-Z_][a-zA-Z0-9_]* {
    printf("-----> ID found: %s   |   scope: %s\n", yytext, currentScope);
    expName = strdup(yytext);
    return ID;
} // Assign value to expName for identifiers

[ \t\r]+    { /* Ignorar espaços e quebras de linha */ }

\n            { /*yylineno++;*/ }

<<EOF>>  { return 0; }

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
