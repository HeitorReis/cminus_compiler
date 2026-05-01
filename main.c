#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <sys/stat.h>
#include "parser.tab.h"
#include "src/analysis_state.h"
#include "src/symbol_table.h"
#include "src/utils.h"
#include "src/syntax_tree.h"
#include "src/semantic.h"
// #include "src/codegen.h"
#include "src/ir.h"

AstNode *syntax_tree; /* Global AST root node */

SymbolTable symtab;  /* Global symbol table */

extern FILE *yyin;        /* Flex’s input file pointer */

void declareBuiltins(SymbolTable *table);
static void ensureOutputDirs(void);
static void ensureDir(const char *path);
static void writeAstFile(const AstNode *root);
static void writeSymbolTableFile(const SymbolTable *table);

static const char *const IR_OUTPUT_PATH = "docs/generated/intermediate/semantic/ir/generated_IR.txt";
static const char *const AST_OUTPUT_DIR = "docs/generated/frontend/syntax_tree";
static const char *const AST_OUTPUT_PATH = "docs/generated/frontend/syntax_tree/ast.txt";
static const char *const SYMBOL_TABLE_OUTPUT_DIR = "docs/generated/frontend/symbol_table";
static const char *const SYMBOL_TABLE_OUTPUT_PATH = "docs/generated/frontend/symbol_table/symbol_table.txt";

int main(int argc, char **argv) {
    int exit_status = EXIT_SUCCESS;

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

    resetAnalysisState();
    syntax_tree = NULL;
    ensureOutputDirs();
    remove(IR_OUTPUT_PATH);

    /* 2.5 Initialize the symbol table and scope stack */
    printf("Initializing symbol table and scope stack...\n");
    initScopeStack();
    initSymbolTable(&symtab);
    declareBuiltins(&symtab);
    printf("Symbol table initialized successfully.\n");

    /* 3. Run the parser (which will invoke the lexer internally) */
    printf("Parsing '%s'...\n", argv[1]);
    int parseResult = yyparse();

    if (gAnalysisState.lexical_error_count > 0) {
        fprintf(stderr, "Lexical analysis failed with %d error(s).\n",
                gAnalysisState.lexical_error_count);
        exit_status = EXIT_FAILURE;
        goto cleanup;
    }

    if (gAnalysisState.syntax_error_count > 0) {
        fprintf(stderr, "Syntactic analysis failed with %d error(s).\n",
                gAnalysisState.syntax_error_count);
        exit_status = EXIT_FAILURE;
        goto cleanup;
    }

    if (parseResult != 0) {
        fprintf(stderr, "Parse failed with code %d.\n", parseResult);
        exit_status = EXIT_FAILURE;
        goto cleanup;
    }

    printf("Parse successful.\n");

    if (syntax_tree) {
        printf("\n=== AST ===\n");
        printAst(syntax_tree, 0);
        writeAstFile(syntax_tree);
    }

    if (syntax_tree) {
        SemanticReport report = semanticAnalyze(syntax_tree, &symtab);

        if (report.error_count > 0) {
            fprintf(stderr, "Semantic analysis failed with %d error(s).\n",
                    report.error_count);
            exit_status = EXIT_FAILURE;
        }

        if (report.missing_main) {
            fprintf(stderr, "Semantic analysis failed: missing global function 'main'.\n");
            exit_status = EXIT_FAILURE;
        }

        printSymbolTable(&symtab);
        writeSymbolTableFile(&symtab);
    }

cleanup:
    if (syntax_tree) {
        freeAst(syntax_tree);
    }

    fclose(yyin);
    return exit_status;
}

void declareBuiltins(SymbolTable *table) {
    declareSymbol(table, "input",  "global", SYMBOL_FUNC, 0, TYPE_INT, 0);
    setFunctionParams(table, "input",  "global", 0, NULL);

    declareSymbol(table, "output", "global", SYMBOL_FUNC, 0, TYPE_VOID, 0);
    int p[1] = { TYPE_INT };
    setFunctionParams(table, "output", "global", 1, p);
}

static void ensureDir(const char *path) {
    if (mkdir(path, 0777) != 0 && errno != EEXIST) {
        fprintf(stderr, "Warning: could not create directory '%s': %s\n", path, strerror(errno));
    }
}

static void ensureOutputDirs(void) {
    ensureDir("docs");
    ensureDir("docs/generated");
    ensureDir("docs/generated/frontend");
    ensureDir(AST_OUTPUT_DIR);
    ensureDir(SYMBOL_TABLE_OUTPUT_DIR);
    ensureDir("docs/generated/intermediate");
    ensureDir("docs/generated/intermediate/semantic");
    ensureDir("docs/generated/intermediate/semantic/ir");
}

static void writeAstFile(const AstNode *root) {
    FILE *out = fopen(AST_OUTPUT_PATH, "w");
    if (!out) {
        fprintf(stderr, "Warning: could not write AST file '%s': %s\n", AST_OUTPUT_PATH, strerror(errno));
        return;
    }

    printAstToStream(out, root, 0);
    fclose(out);
    printf("AST has been saved to: %s\n", AST_OUTPUT_PATH);
}

static void writeSymbolTableFile(const SymbolTable *table) {
    FILE *out = fopen(SYMBOL_TABLE_OUTPUT_PATH, "w");
    if (!out) {
        fprintf(stderr, "Warning: could not write symbol table file '%s': %s\n", SYMBOL_TABLE_OUTPUT_PATH, strerror(errno));
        return;
    }

    printSymbolTableToStream(out, table);
    fclose(out);
    printf("Symbol table has been saved to: %s\n", SYMBOL_TABLE_OUTPUT_PATH);
}
