#include <stdio.h>
#include <stdlib.h>
#include "parser.tab.h"
#include "src/symbol_table.h"
#include "src/utils.h"
#include "src/syntax_tree.h"
#include "src/semantic.h"

AstNode *syntax_tree; /* Global AST root node */

SymbolTable symtab;  /* Global symbol table */

extern FILE *yyin;        /* Flex’s input file pointer */

int main(int argc, char **argv) {
    /* 1. Check command‐line arguments */
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input_file>\n", argv[0]);
        return EXIT_FAILURE;
    }

    /* 2. Open the input file for the lexer */
    yyin = fopen(argv[1], "r");
    if (!yyin) {
        perror("Error opening file");
        return EXIT_FAILURE;
    }

    /* 2.5 Initialize the symbol table and scope stack */
    printf("Initializing symbol table and scope stack...\n");
    initScopeStack();
    initSymbolTable(&symtab);

    /* 3. Run the parser (which will invoke the lexer internally) */
    printf("Parsing '%s'...\n", argv[1]);
    int parseResult = yyparse();

    /* 4. Report and clean up */
    if (parseResult == 0) {
        printf("Parse successful.\n");
        printSymbolTable(&symtab);
        printf("Symbol table printed successfully.\n");
    } else {
        fprintf(stderr, "Parse failed with code %d.\n", parseResult);
    }

    if (syntax_tree) {
        printf("\n=== AST ===\n");
        printAst(syntax_tree, 0);
    }

    semanticAnalyze(syntax_tree, &symtab);

    if (syntax_tree) {
        freeAst(syntax_tree);
    }

    fclose(yyin);
    return parseResult == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
