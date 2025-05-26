#include "symbol_table.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void initSymbolTable(SymbolTable *table) {
    table->head = NULL;
}

void insertSymbol(
    SymbolTable *table,
    const char  *name,
    const char  *scope,
    SymbolKind   kind,
    int          line,
    int          dataType
) {
    Symbol *sym = malloc(sizeof(Symbol));
    if (!sym) { perror("malloc"); exit(1); }

    sym->name     = strdup(name);
    sym->scope    = strdup(scope);
    sym->kind     = kind;
    sym->line     = line;
    sym->dataType = dataType;

    /* insert at front */
    sym->next = table->head;
    table->head = sym;
}

void dumpSymbolTable(const SymbolTable *table) {
    puts("---- Symbol Table ----");
    printf("%-12s %-10s %-6s %-5s %-5s\n",
           "Name", "Scope", "Kind", "Line", "Type");
    for (Symbol *s = table->head; s; s = s->next) {
        printf("%-12s %-10s %-6s %-5d %-5d\n",
               s->name,
               s->scope,
               s->kind == SYMBOL_VAR ? "VAR" : "FUNC",
               s->line,
               s->dataType);
    }
    puts("----------------------");
}

void printSymbolTable(const SymbolTable *table) {
    const char *kindStr;
    const char *typeStr;

    puts("======= SYMBOL TABLE =======");
    printf("%-15s %-10s %-6s %-6s %-6s\n",
           "Name", "Scope", "Kind", "Line", "Type");
    puts("-----------------------------");

    for (Symbol *s = table->head; s; s = s->next) {
        /* pick human‐friendly strings */
        kindStr = (s->kind == SYMBOL_VAR ? "VAR" : "FUNC");
        typeStr = (s->dataType == 4 /* INT */ ? "INT" : "VOID");

        printf("%-15s %-10s %-6s %-6d %-6s\n",
               s->name,
               s->scope,
               kindStr,
               s->line,
               typeStr);
    }
    puts("======= END OF TABLE =======");
}
