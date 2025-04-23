// semantic.h
#ifndef SEMANTIC_ANALYSIS_H
#define SEMANTIC_ANALYSIS_H

#include "symbol_table.h"
#include "node.h"

// A linked list of error messages
typedef struct ErrorNode {
    char *message;
    struct ErrorNode *next;
} ErrorNode;

// Carries the symbol table and collected errors
typedef struct {
    SymbolTable symbols;
    ErrorNode *errors;
} SemanticContext;

// Initialize symbol table & error list
void initSemanticContext(SemanticContext *ctx);

// Install built-in functions and check for main()
void prepareBuiltInsAndMain(SemanticContext *ctx);

// Entry point: performs full semantic analysis (calls below)
void semanticAnalysis(treeNode *root);

// Recursively walk the AST from a given node & scope
void analyzeNode(treeNode *n, SemanticContext *ctx, const char *scope);

// Report (collect) an error (printf-style)
void reportError(SemanticContext *ctx, const char *fmt, ...);

// After analysis, print all errors (or success)
void printSemanticResults(SemanticContext *ctx);

#endif // SEMANTIC_ANALYSIS_H
