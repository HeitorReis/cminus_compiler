#ifndef SEMANTIC_ANALYSIS_H
#define SEMANTIC_ANALYSIS_H

#include "syntax_tree.h"
#include "symbol_table.h"
#include "ir.h"
// #include "codegen.h"

extern char *currentScope;

typedef enum {
    TYPE_INT = 1,
    TYPE_VOID = 2,
    TYPE_ERROR = -1
} ExpType;

typedef struct {
    SymbolTable *symtab;
    ExpType      curRetType;   // track return‐type inside each function
    int          errorCount;
} SemanticContext;

// walk the whole program
void semanticAnalyze(AstNode *root, SymbolTable *symtab);

#endif
