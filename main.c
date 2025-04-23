#include <stdio.h>
#include <stdlib.h>
#include "syntax_tree.h"
#include "symbol_table.h"
#include "utils.h"
#include "node.h"
#include "semantic.h"      

extern int yyparse();
extern FILE *yyin;

extern treeNode *syntaxTree;
extern SymbolTable tabela;
extern int parseResult;
extern int erro_lexico;

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: %s <arquivo_de_entrada>\n", argv[0]);
        return EXIT_FAILURE;
    }

    yyin = fopen(argv[1], "r");
    if (!yyin) {
        perror("Erro ao abrir o arquivo de entrada");
        return EXIT_FAILURE;
    }

    printf("Analisando o arquivo: %s\n", argv[1]);
    syntaxTree = parse();
    if (parseResult != 0 || erro_lexico != 0) {
        fclose(yyin);
        return EXIT_FAILURE;
    }

    printf("Análise sintática concluída com sucesso.\n");
    printf("Árvore sintática gerada:\n");
    printSyntaxTree(syntaxTree);

    // Build and print the symbol table
    printf("Tabela de Símbolos:\n");
    printSymbolTable(&tabela);

   // === RUN SEMANTIC ANALYSIS ===
    semanticAnalysis(syntaxTree);
   // If there are errors, semanticAnalysis will print them and exit.
   // Otherwise it prints success and we continue.

    fclose(yyin);
    return EXIT_SUCCESS;
}
