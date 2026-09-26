#ifndef SEMANTIC_ANALYSIS_H
#define SEMANTIC_ANALYSIS_H

#include "syntax_tree.h"
#include "symbol_table.h"

extern char *currentScope;

typedef enum {
    TYPE_INT = 1,
    TYPE_VOID = 2,
    TYPE_ARRAY = 3,
    TYPE_ERROR = -1
} ExpType;

typedef struct {
    int error_count;
    int missing_main;
} SemanticReport;

SemanticReport semanticAnalyze(AstNode *root, SymbolTable *symtab);

#endif
