#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

/* distinguish variables vs. functions */
typedef enum {
    SYMBOL_VAR,
    SYMBOL_FUNC
} SymbolKind;

/* one symbol entry */
typedef struct Symbol {
    char        *name;      /* identifier */
    char        *scope;     /* e.g. "global" or function name */
    SymbolKind   kind;      /* var or func */
    int          line;      /* declaration line */
    int          dataType;  /* e.g. TYPE_INT (1) or TYPE_VOID (2) */
    struct Symbol *next;    /* linked‐list bucket */
} Symbol;

/* the table is just a head pointer for now */
typedef struct {
    Symbol *head;
} SymbolTable;

/* debug: print all entries in a human‐readable table */
void printSymbolTable(const SymbolTable *table);

/* initialize before parse */
void initSymbolTable(SymbolTable *table);

/* called from your grammar actions */
void insertSymbol(
    SymbolTable *table,
    const char  *name,
    const char  *scope,
    SymbolKind   kind,
    int          line,
    int          dataType
);

/* debug dump after parsing */
void dumpSymbolTable(const SymbolTable *table);

#endif /* SYMBOL_TABLE_H */
