#include "symbol_table.h"
#include "utils.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TYPE_INT 1
#define TYPE_VOID 2
#define TYPE_ARRAY 3

static void appendLine(LineNode **head, int line) {
    LineNode *node = malloc(sizeof(*node));
    if (!node) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }

    node->line = line;
    node->next = NULL;

    if (!*head) {
        *head = node;
        return;
    }

    LineNode *tail = *head;
    while (tail->next) {
        tail = tail->next;
    }
    tail->next = node;
}

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
    if (!table || !name || !scope) {
        return NULL;
    }
    return findSymbol(table, name, scope);
}

Symbol *resolveSymbol(
    SymbolTable *table,
    const char *name,
    const char *scope
) {
    if (!table || !name) {
        return NULL;
    }

    if (scope && isScopeActive(scope)) {
        for (int index = getScopeDepth() - 1; index >= 0; --index) {
            const char *active_scope = getScopeNameAt(index);
            Symbol *symbol = findSymbol(table, name, active_scope);
            if (symbol) {
                return symbol;
            }
        }
    }

    if (scope) {
        Symbol *symbol = findSymbol(table, name, scope);
        if (symbol) {
            return symbol;
        }
    }

    return findSymbol(table, name, "global");
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
    int          array_size
) {
    Symbol *sym = getSymbol(table, name, scope);
    if (sym) {
        appendLine(&sym->declLines, declLine);
    } else {
        /* brand-new symbol */
        sym = malloc(sizeof(*sym));
        if (!sym) {
            perror("malloc");
            exit(EXIT_FAILURE);
        }
        sym->name     = strdup(name);
        sym->scope    = strdup(scope);
        sym->kind     = kind;
        
        sym->array_size = array_size;
        
        if (kind == SYMBOL_FUNC) {
            sym->dataType = dataType; // Para funções, dataType é o tipo de retorno
            sym->baseType = 0;        // Não se aplica
        } else { // kind == SYMBOL_VAR
            if (array_size != 0) { // Lida com vetores declarados (>0) e parâmetros de vetor (-1)
                sym->dataType = TYPE_ARRAY; // O tipo principal é VETOR
                sym->baseType = dataType;   // O tipo base é INT
            } else {
                sym->dataType = dataType;   // O tipo principal é INT
                sym->baseType = 0;          // Não se aplica
            }
        }

        sym->declLines = NULL;
        sym->useLines  = NULL;
        sym->paramCount = 0;  /* no params yet */
        sym->paramTypes = NULL; /* no param types yet */
        appendLine(&sym->declLines, declLine);
        /* insert into table head */
        sym->next      = table->head;
        table->head    = sym;
    }
}

void registerSymbolUse(Symbol *symbol, int useLine) {
    if (!symbol) {
        return;
    }

    appendLine(&symbol->useLines, useLine);
}

void setFunctionParams(
    SymbolTable *table,
    const char *name,
    const char *scope,
    int paramCount,
    int *paramTypes
) {
    Symbol *sym = getSymbol(table, name, scope);
    if (!sym || sym->kind != SYMBOL_FUNC) {
        return;
    }

    free(sym->paramTypes);
    sym->paramTypes = NULL;
    sym->paramCount = paramCount;
    sym->array_size = 0;
    if (paramCount <= 0) {
        sym->paramTypes = NULL;
    } else {
        sym->paramTypes = malloc(paramCount * sizeof(int));
        if (!sym->paramTypes) {
            perror("malloc");
            exit(EXIT_FAILURE);
        }
        memcpy(sym->paramTypes, paramTypes, paramCount * sizeof(int));
    }
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
        typeStr = (s->dataType == TYPE_INT ? "INT" : "VOID");

        /* Print basic info */
        printf("%-15s %-10s %-6s ", s->name, s->scope, kindStr);

        /* Print all declaration lines as comma-separated */
        for (LineNode *ln = s->declLines; ln; ln = ln->next) {
            printf("%d", ln->line);
            if (ln->next) printf(",");
        }

        printf("\t");

        /* Print all use lines as comma-separated */
        for (LineNode *ln = s->useLines; ln; ln = ln->next) {
            printf("%d", ln->line);
            if (ln->next) printf(",");
        }
        
        printf("\t");

        if (s->dataType == TYPE_ARRAY) {
            const char* baseTypeStr = (s->baseType == TYPE_INT) ? "INT" : "?";
            // Imprime no formato "ARRAY(10, INT)"
            printf("ARRAY(%d, %s)\n", s->array_size, baseTypeStr);
        } else {
            // Comportamento antigo para INT e VOID
            const char *typeStr = (s->dataType == TYPE_INT ? "INT" : "VOID");
            printf("%s\n", typeStr);
        }
    }

    puts("======= END OF TABLE =======");
}
