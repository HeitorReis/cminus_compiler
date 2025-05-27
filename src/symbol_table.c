#include "symbol_table.h"
#include "parser.tab.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TYPE_INT 1
#define TYPE_VOID 2

static Symbol *findSymbol(SymbolTable *table, const char *name, const char *scope) {
    for (Symbol *s = table->head; s; s = s->next) {
        if (strcmp(s->name, name) == 0 && strcmp(s->scope, scope) == 0)
            return s;
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
    int          dataType
) {
    Symbol *sym = findSymbol(table, name, scope);
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
        sym->dataType = dataType;
        /* first declLines node */
        LineNode *dln = malloc(sizeof(*dln));
        if (!dln) { perror("malloc"); exit(1); }
        dln->line = declLine;
        dln->next = NULL;
        sym->declLines = dln;
        sym->useLines  = NULL;
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
    printf(
        "[DEBUG] useSymbol: '%s' in scope '%s' at line %d\n",
        name, 
        scope, 
        useLine
    );
    Symbol *sym = findSymbol(table, name, scope);
    if (!sym) {
        yyerror("use of undeclared identifier");
    return;
    }
    LineNode *ln = malloc(sizeof(*ln));
    if (!ln) { perror("malloc"); exit(1); }
    ln->line = useLine;
    ln->next = sym->useLines;
    sym->useLines = ln;
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
        typeStr = (s->dataType == TYPE_INT ? "INT" : "VOID");

        /* Print basic info */
        printf("%-15s %-10s %-6s ", s->name, s->scope, kindStr);

        /* Print all declaration lines as comma-separated */
        for (LineNode *ln = s->declLines; ln; ln = ln->next) {
            printf("%d", ln->line);
            if (ln->next) printf(",");
        }

        printf(" \t");

        /* Print all use lines as comma-separated */
        for (LineNode *ln = s->useLines; ln; ln = ln->next) {
            printf("%d", ln->line);
            if (ln->next) printf(",");
        }

        printf(" \t%-6s\n", typeStr);
    }

    puts("======= END OF TABLE =======");
}