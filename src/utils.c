#include "utils.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>   /* for perror, if you choose */

/* internal stack storage */
static char *scopeStack[MAX_SCOPE_DEPTH];
static int   scopeTop;       /* index of the top; –1 when empty */

/* the one global pointer everyone reads */
char *currentScope = "global";

void initScopeStack(void) {
    scopeTop = -1;
    currentScope = "global";
}

void pushScope(const char *name) {
    if (scopeTop + 1 >= MAX_SCOPE_DEPTH) {
        fprintf(stderr, "Scope stack overflow\n");
        exit(EXIT_FAILURE);
    }
    /* strdup so we own the memory */
    scopeStack[++scopeTop] = strdup(name);
    currentScope = scopeStack[scopeTop];
}

void popScope(void) {
    if (scopeTop < 0) {
        /* underflow—nothing to pop; reset to global */
        currentScope = "global";
        return;
    }
    free(scopeStack[scopeTop]);
    scopeStack[scopeTop--] = NULL;
    if (scopeTop >= 0) {
        currentScope = scopeStack[scopeTop];
    } else {
        currentScope = "global";
    }
}
