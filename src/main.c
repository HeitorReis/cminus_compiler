#include <stdio.h>
#include <stdlib.h>
#include "syntax_tree.h"
#include "symbol_table.h"
#include "utils.h"
#include "node.h"

// Declarações externas geradas pelo Bison
extern int yyparse();
extern FILE *yyin;

// Raiz da árvore sintática gerada pelo parser
extern treeNode *syntax_tree;

//Raiz da tabela de simbolos
extern SymbolTable tabela;

int parseResult;
int erro_lexico;

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s <arquivo_de_entrada>\n", argv[0]);
        return EXIT_FAILURE;
    }

    // Abrir o arquivo de entrada
    yyin = fopen(argv[1], "r");
    if (!yyin) {
        perror("Erro ao abrir o arquivo de entrada");
        return EXIT_FAILURE;
    }

    // Executar o parser
    printf("Analisando o arquivo: %s\n", argv[1]);
    syntax_tree = parse();
    if(parseResult == 0 && erro_lexico == 0){
        printf("Análise sintática concluída com sucesso.\n");
        printf("Árvore sintática gerada:\n");
        printSyntaxTree(syntax_tree); // Imprime a árvore sintática
    } else {
        return EXIT_SUCCESS;
    }

    //construir tabela de simbolos
    printf("Tabela de Símbolos:\n");
    printSymbolTable(&tabela);

    //semanticAnalysis();


    // Fechar o arquivo de entrada
    fclose(yyin);

    return EXIT_SUCCESS;
}
