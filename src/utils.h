#ifndef UTILS_H
#define UTILS_H

/* maximum nesting depth of scopes (functions or blocks) */
#define MAX_SCOPE_DEPTH 128

/* the “current” scope name that parser and symbol_table will use */
extern char *currentScope;

/* initialize the scope stack (call before parsing) */
void initScopeStack(void);

/* push a new scope name; currentScope is updated */
void pushScope(const char *name);

/* pop back to the previous scope; currentScope is updated */
void popScope(void);

#endif /* UTILS_H */