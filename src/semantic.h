#ifndef SEMANTIC_ANALYSIS_H
#define SEMANTIC_ANALYSIS_H

#include "syntax_tree.h"
#include "symbol_table.h"

typedef enum {
    TYPE_INT,
    TYPE_VOID,
    TYPE_ERROR
} ExpType;

typedef struct {
    SymbolTable *symtab;
    ExpType      curRetType;   // track return‐type inside each function
    int          errorCount;
} SemanticContext;

// walk the whole program
void semanticAnalyze(AstNode *root, SymbolTable *symtab);

#endif
