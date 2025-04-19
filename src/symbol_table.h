#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

#include "node.h"

#define SIZE 211 // Número primo para melhorar a distribuição
#define SHIFT 4

typedef enum { VAR, ARRAY, FUNC } SymbolType;

typedef struct LineList {
    int line;
    struct LineList *next;
} LineList;

typedef struct Symbol {
    char *name;
    char *scope;
    SymbolType type;
    LineList *lines;
    primitiveType dataType;
    struct Symbol *next; // Para resolver colisões na tabela hash
} Symbol;

typedef struct {
    Symbol *table[SIZE];
    int count; // número de símbolos inseridos
} SymbolTable;


void initSymbolTable(SymbolTable *table);
int insertSymbol(SymbolTable *table, char *name, char *scope, SymbolType type, int line, primitiveType dataType);
Symbol *findSymbol(SymbolTable *table, char *name, char *scope);
void addLine(Symbol *symbol, int line);
void printSymbolTable(SymbolTable *table);
void freeSymbolTable(SymbolTable *table);
int hash(char *key);

#endif // SYMBOL_TABLE_H