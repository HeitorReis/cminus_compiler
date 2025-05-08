#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "symbol_table.h"

// forward‐declare
static int internalHash(const char *key, int modulo);

int hash(const char *key) {
    return internalHash(key, SIZE);
}

static int internalHash(const char *key, int modulo) {
    int temp = 0, i = 0;
    while (key[i] != '\0') {
        temp = ((temp << SHIFT) + key[i]) % modulo;
        ++i;
    }
    return temp;
}

void initSymbolTable(SymbolTable *table) {
    table->count = 0;
    for (int i = 0; i < SIZE; i++) {
        table->table[i] = NULL;
    }
}

int insertSymbol(SymbolTable *table,
                const char *name,
                const char *scope,
                SymbolType type,
                int line,
                primitiveType dataType) {
    int index = hash(name);
    Symbol *existing = findSymbol(table, name, scope);
    if (existing) {
        addLine(existing, line);
        return 0;
    }

    Symbol *newSymbol = malloc(sizeof(Symbol));
    if (!newSymbol) {
        fprintf(stderr, "Memory allocation error\n");
        return -1;
    }
    newSymbol->name       = strdup(name);
    newSymbol->scope      = strdup(scope);
    newSymbol->type       = type;
    newSymbol->dataType   = dataType;

    /* inicializa os campos de parâmetros */
    newSymbol->paramCount = 0;
    newSymbol->paramTypes = NULL;

    newSymbol->lines = malloc(sizeof(LineList));
    newSymbol->lines->line = line;
    newSymbol->lines->next = NULL;

    newSymbol->next = table->table[index];
    table->table[index] = newSymbol;
    table->count++;
    return 0;
}

void freeSymbolTable(SymbolTable *table) {
    for (int i = 0; i < SIZE; i++) {
        Symbol *symbol = table->table[i];
        while (symbol) {
            Symbol *tmp = symbol;
            symbol = symbol->next;

            /* libera lista de linhas */
            LineList *line = tmp->lines;
            while (line) {
                LineList *nextLine = line->next;
                free(line);
                line = nextLine;
            }

            /* libera array de parâmetros, se houver */
            free(tmp->paramTypes);

            free(tmp->name);
            free(tmp->scope);
            free(tmp);
        }
    }
    table->count = 0;
}

Symbol *findSymbol(SymbolTable *table,
                   const char *name,
                   const char *scope) {
    int index = hash(name);
    Symbol *current = table->table[index];
    while (current) {
        if (strcmp(current->name, name) == 0 &&
            strcmp(current->scope, scope) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

void addLine(Symbol *symbol, int line) {
    if (!symbol) return;

    LineList *aux = symbol->lines;
    while (aux) {
        if (aux->line == line) return;  // já gravado
        aux = aux->next;
    }
    LineList *newLine = malloc(sizeof(LineList));
    newLine->line = line;
    newLine->next = symbol->lines;
    symbol->lines  = newLine;
}

const char* symbolTypeToString(SymbolType type) {
    switch (type) {
        case VAR:   return "var";
        case ARRAY: return "array";
        case FUNC:  return "func";
        default:    return "unknown";
    }
}

const char* primitiveTypeToString(primitiveType type) {
    switch (type) {
        case Integer: return "int";
        case Void:    return "void";
        default:      return "unknown";
    }
}

void printSymbolTable(SymbolTable *table) {
    printf("Name     | Scope        | Tipo ID      | Tipo dado | Linhas\n");
    printf("-------------------------------------------------------------\n");
    for (int i = 0; i < SIZE; i++) {
        Symbol *current = table->table[i];
        while (current) {
            printf("%-8s | %-12s | %-12s | %-8s | ",
                   current->name,
                   current->scope,
                   symbolTypeToString(current->type),
                   primitiveTypeToString(current->dataType));
            LineList *line = current->lines;
            while (line) {
                printf("%d ", line->line);
                line = line->next;
            }
            printf("\n");
            current = current->next;
        }
    }
}
