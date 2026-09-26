#include "utils.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>   /* for perror, if you choose */

/* internal stack storage */
static char *scopeStack[MAX_SCOPE_DEPTH];
static int   scopeTop;       /* index of the top; –1 when empty */
static int   blockCounter;

/* the one global pointer everyone reads */
char *currentScope = "global";

void initScopeStack(void) {
    scopeTop = -1;
    blockCounter = 0;
    currentScope = "global";
}

int getScopeDepth(void) {
    return scopeTop + 1;
}

const char *getScopeNameAt(int index) {
    if (index < 0 || index > scopeTop) {
        return NULL;
    }
    return scopeStack[index];
}

int isScopeActive(const char *name) {
    if (!name) {
        return 0;
    }
    if (strcmp(name, "global") == 0) {
        return 1;
    }
    for (int index = scopeTop; index >= 0; --index) {
        if (strcmp(scopeStack[index], name) == 0) {
            return 1;
        }
    }
    return 0;
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

void pushBlockScope(void) {
    char generated_name[256];
    snprintf(generated_name, sizeof(generated_name), "%s#block%d", currentScope, blockCounter++);
    pushScope(generated_name);
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
