#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "symbol_table.h"

int hash(char *key) {
    return internalHash(key, SIZE);
}

int internalHash(char *key, int modulo) {
    int temp = 0;
    int i = 0;
    while (key[i] != '\0') {
        temp = ((temp << SHIFT) + key[i]) % modulo;
        ++i;
    }
    return temp;
}


void initSymbolTable(SymbolTable *table) {
    for (int i = 0; i < SIZE; i++) {
        table->table[i] = NULL;
        table->count = 0;
    }
}

void freeSymbolTable(SymbolTable *table) {
    for (int i = 0; i < SIZE; i++) {
        Symbol *symbol = table->table[i];
        while (symbol) {
            Symbol *temp = symbol;
            symbol = symbol->next;

            LineList *line = temp->lines;
            while (line) {
                LineList *tempLine = line;
                line = line->next;
                free(tempLine);
            }

            free(temp->name);
            free(temp->scope);
            free(temp);
        }
        table->table[i] = NULL;
    }
}


int insertSymbol(SymbolTable *table, char *name, char *scope, SymbolType type, int line, primitiveType dataType) {
    int index = hash(name);
    Symbol *newSymbol = (Symbol *)malloc(sizeof(Symbol));
    if (!newSymbol) {
        fprintf(stderr, "Memory allocation error\n");
        return -1;
    }
    Symbol *existing = findSymbol(table, name, scope);
    if (existing) {
        // Just record the new line number
        addLine(existing, line);
        return 0;  // no new symbol allocated
    }
    newSymbol->name = strdup(name);
    newSymbol->scope = strdup(scope);
    newSymbol->type = type;
    newSymbol->lines = (LineList *)malloc(sizeof(LineList));
    newSymbol->lines->line = line;
    newSymbol->lines->next = NULL;
    newSymbol->dataType = dataType;
    newSymbol->next = table->table[index];
    table->table[index] = newSymbol;
    table->count++;
    return 0;
}

Symbol *findSymbol(SymbolTable *table, char *name, char *scope) {
    int index = hash(name);
    Symbol *current = table->table[index];
    while (current) {
        if (strcmp(current->name, name) == 0 && strcmp(current->scope, scope) == 0) {
            return current;
        }
        current = current->next;
    }
    return NULL;
}

void addLine(Symbol *symbol, int line) {
    if (!symbol) return;
    LineList *newLine = (LineList *)malloc(sizeof(LineList));
    newLine->line = line;
    LineList *aux = symbol->lines;
    while(aux->next){
        if(aux->line == line) return;
        aux = aux->next;
    }
    newLine->next = symbol->lines;
    symbol->lines = newLine;
}

const char* symbolTypeToString(SymbolType type) {
    switch (type) {
        case VAR: return "var";
        case ARRAY: return "array";
        case FUNC: return "func";
        default: return "unknown";
    }
}

const char* primitiveTypeToString(primitiveType type) {
    switch (type) {
        case Integer: return "int";
        case Void: return "void";
        default: return "unknown";
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