#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

#include "node.h"

#define SIZE 211
#define SHIFT 4

typedef enum { VAR, ARRAY, FUNC } SymbolType;

typedef struct LineList {
    int line;
    struct LineList *next;
} LineList;

typedef struct Symbol {
    char          *name;
    char          *scope;
    SymbolType     type;
    LineList      *lines;
    primitiveType  dataType;
    /* ======= NOVOS CAMPOS ======= */
    size_t         paramCount;
    primitiveType *paramTypes;
    /* ============================ */
    struct Symbol *next;
} Symbol;

typedef struct {
    Symbol *table[SIZE];
    int     count;
} SymbolTable;

void initSymbolTable(SymbolTable *table);
int  insertSymbol(SymbolTable *table,
                  const char *name,
                  const char *scope,
                  SymbolType type,
                  int line,
                  primitiveType dataType);
Symbol *findSymbol(SymbolTable *table,
                   const char *name,
                   const char *scope);
void addLine(Symbol *symbol, int line);
void printSymbolTable(SymbolTable *table);
void freeSymbolTable(SymbolTable *table);
int  hash(const char *key);

const char* primitiveTypeToString(primitiveType type);
const char* symbolTypeToString(SymbolType type);

#endif // SYMBOL_TABLE_H
