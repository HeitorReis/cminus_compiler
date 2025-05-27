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
    struct Symbol *next;    /* next symbol in table */
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
void declareSymbol(table, name, scope, kind, declLine, dataType); // insert a new symbol
void useSymbol   (table, name, scope, useLine); // record a use of an existing symbol


#endif /* SYMBOL_TABLE_H */
