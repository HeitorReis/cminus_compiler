/* symbol_table.h */
#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

/* distinguish variables vs. functions */
typedef enum {
    SYMBOL_VAR,
    SYMBOL_FUNC
} SymbolKind;

/* linked list of source‐line numbers */
typedef struct LineNode {
    int line;
    struct LineNode *next;
} LineNode;

/* one symbol entry, now tracking all lines */
typedef struct Symbol {
    char        *name;      /* identifier */
    char        *scope;     /* e.g. "global" or function name */
    SymbolKind   kind;      /* var or func */
    int          dataType;  /* TYPE_INT or TYPE_VOID */
    LineNode    *declLines; /* lines where it was declared */
    LineNode    *useLines;  /* lines where it was used */
    int          paramCount; /* number of parameters (for functions) */
    int         *paramTypes; /* array of parameter types (for functions) */
    int         array_size;
    int         baseType;
    struct Symbol *next;    /* next symbol in table */
} Symbol;

/* the table is just a head pointer for now */
typedef struct {
    Symbol *head;
} SymbolTable;

void setFunctionParams(
    SymbolTable *table,
    const char *name,
    const char *scope,
    int paramCount,
    int *paramTypes
);

int getParamCount(
    SymbolTable *table,
    const char *name,
    const char *scope
);

int getParamType(
    SymbolTable *table,
    const char *name,
    const char *scope,
    int index
);

/* debug: print all entries in a human‐readable table */
void printSymbolTable(const SymbolTable *table);

/* initialize before parse */
void initSymbolTable(SymbolTable *table);

/* called from your grammar actions */
void declareSymbol(
    SymbolTable *table,
    const char  *name,
    const char  *scope,
    SymbolKind   kind,
    int          declLine,
    int          dataType,
    int          array_size
);

void useSymbol(
    SymbolTable *table,
    const char  *name,
    const char  *scope,
    int          useLine
);

Symbol *getSymbol(
    SymbolTable *table,
    const char *name,
    const char *scope
);

#endif /* SYMBOL_TABLE_H */
