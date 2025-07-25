#include "symbol_table.h"
#include "parser.tab.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TYPE_INT 1
#define TYPE_VOID 2
#define TYPE_ARRAY 3

static Symbol *findSymbol(
    SymbolTable *table, 
    const char *name, 
    const char *scope
) {
    for (Symbol *s = table->head; s; s = s->next) {
        if (strcmp(s->name, name) == 0 && strcmp(s->scope, scope) == 0)
            return s;
    }
    return NULL;
}

Symbol *getSymbol(
    SymbolTable *table, 
    const char *name, 
    const char *scope
) {
    Symbol *s = findSymbol(table, name, scope);
    if (s) return s;
    if (strcmp(scope, "global") != 0) {
        return findSymbol(table, name, "global");
    }
    return NULL;
}

void initSymbolTable(SymbolTable *table) {
    table->head = NULL;
}

/* record a declaration (and allow multiple declLines) */
void declareSymbol(
    SymbolTable *table,
    const char  *name,
    const char  *scope,
    SymbolKind   kind,
    int          declLine,
    int          dataType,
    int         array_size
) {
    Symbol *sym = getSymbol(table, name, scope);
    if (sym) {
        /* existing symbol → append another declLine */
        yyerror("redeclared identifier");
    } else {
        /* brand-new symbol */
        sym = malloc(sizeof(*sym));
        if (!sym) { perror("malloc"); exit(1); }
        sym->name     = strdup(name);
        sym->scope    = strdup(scope);
        sym->kind     = kind;
        sym->array_size = array_size;
        if (array_size > 0) {
            sym->dataType = TYPE_ARRAY; // O tipo principal é VETOR
            sym->baseType = dataType;   // O tipo base é o que foi passado (INT)
        } else {
            sym->dataType = dataType;   // O tipo principal é o que foi passado (INT)
            sym->baseType = 0;          // Não aplicável para não-vetores
        }
        /* first declLines node */
        LineNode *dln = malloc(sizeof(*dln));
        if (!dln) { perror("malloc"); exit(1); }
        dln->line = declLine;
        dln->next = NULL;
        sym->declLines = dln;
        sym->useLines  = NULL;
        sym->paramCount = 0;  /* no params yet */
        sym->paramTypes = NULL; /* no param types yet */
        /* insert into table head */
        sym->next      = table->head;
        table->head    = sym;
    }
}

/* record a use (or error if undeclared) */
void useSymbol(
    SymbolTable *table,
    const char  *name,
    const char  *scope,
    int          useLine
) {
    Symbol *sym = getSymbol(table, name, scope);
    if (!sym) {
        yyerror("use of undeclared identifier");
    return;
    }
    LineNode *ln = malloc(sizeof(*ln));
    if (!ln) { perror("malloc"); exit(1); }
    ln->line = useLine;
    ln->next = sym->useLines;
    sym->useLines = ln;
    printf(
        "[SYM_TABLE DBG] useSymbol: '%s' in scope '%s' at line %d\n",
        name, 
        scope, 
        useLine
    );
}

void setFunctionParams(
    SymbolTable *table,
    const char *name,
    const char *scope,
    int paramCount,
    int *paramTypes
) {
    Symbol *sym = getSymbol(table, name, scope);
    if (!sym || sym->kind != SYMBOL_FUNC) return;
    sym->paramCount = paramCount;
    sym->paramTypes = malloc(paramCount * sizeof(int));
    if (!sym->paramTypes) { perror("malloc"); exit(1); }
    memcpy(sym->paramTypes, paramTypes, paramCount * sizeof(int));
    printf(
        "[SYM_TABLE DBG] setFunctionParams: '%s' in scope '%s' with %d params\n",
        name, 
        scope, 
        paramCount
    );
}

int getParamCount(
    SymbolTable *table,
    const char *name,
    const char *scope
) {
    Symbol *sym = getSymbol(table, name, scope);
    return sym ? sym->paramCount : -1;
}

int getParamType(
    SymbolTable *table,
    const char *name,
    const char *scope,
    int index
) {
    Symbol *sym = getSymbol(table, name, scope);
    if (!sym || index < 0 || index >= sym->paramCount) {
        return -1; // invalid request
    }
    return sym->paramTypes[index];
}

void printSymbolTable(const SymbolTable *table) {
    const char *kindStr, *typeStr;

    puts("======= SYMBOL TABLE =======");
    printf(
        "%-15s %-10s %-6s %-20s %-20s %-6s\n",
        "Name", "Scope", "Kind", "Decl Lines", "Use Lines", "Type"
    );
    puts("--------------------------------------------------------------------------");

    for (Symbol *s = table->head; s; s = s->next) {
        kindStr = (s->kind == SYMBOL_VAR ? "VAR" : "FUNC");

        /* Print basic info */
        printf("%-15s %-10s %-6s ", s->name, s->scope, kindStr);
        printf(" \t");


        if (s->dataType == TYPE_ARRAY) {
            const char* baseTypeStr = (s->baseType == TYPE_INT) ? "INT" : "?";
            // Imprime no formato "ARRAY(10, INT)"
            printf("ARRAY(%d, %s)\n", s->array_size, baseTypeStr);
        } else {
            // Comportamento antigo para INT e VOID
            const char *typeStr = (s->dataType == TYPE_INT ? "INT" : "VOID");
            printf("%-6s\n", typeStr);
        }
    }

    puts("======= END OF TABLE =======");
}