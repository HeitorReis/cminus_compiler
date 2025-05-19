#include "semantic.h"
#include "symbol_table.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

void reportError(SemanticContext *ctx, const char *fmt, ...) {
    char buf[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    ErrorNode *e = malloc(sizeof(*e));
    e->message = strdup(buf);
    e->next = ctx->errors;
    ctx->errors = e;
}

void initSemanticContext(SemanticContext *ctx) {
    initSymbolTable(&ctx->symbols);
    ctx->errors = NULL;
}

void prepareBuiltInsAndMain(SemanticContext *ctx) {
    Symbol *s;

    insertSymbol(&ctx->symbols, "input", "global", FUNC, 0, Integer);
    s = findSymbol(&ctx->symbols, "input", "global");
    s->paramCount = 0;
    s->paramTypes = NULL;

    insertSymbol(&ctx->symbols, "output", "global", FUNC, 0, Void);
    s = findSymbol(&ctx->symbols, "output", "global");
    s->paramCount = 1;
    s->paramTypes = malloc(sizeof(primitiveType));
    s->paramTypes[0] = Integer;
}

void analyzeNode(treeNode *n, SemanticContext *ctx, const char *scope) {
    if (!n) return;

    if (n->node == decl) {
        if (n->declSubType == declVar) {
            if (n->type == Void) {
                reportError(ctx,
                    "Line %d: variable '%s' cannot be void",
                    n->line, n->name);
            }
            if (findSymbol(&ctx->symbols, n->name, scope)) {
                reportError(ctx,
                    "Line %d: '%s' already declared in '%s'",
                    n->line, n->name, scope);
            } else {
                insertSymbol(&ctx->symbols,
                             n->name, scope,
                             VAR, n->line, n->type);
            }
        }
        else if (n->declSubType == declFunc) {
            if (findSymbol(&ctx->symbols, n->name, "global")) {
                reportError(ctx,
                    "Line %d: function '%s' redeclared",
                    n->line, n->name);
            } else {
                insertSymbol(&ctx->symbols,
                             n->name, "global",
                             FUNC, n->line, n->type);
            }
        }
    }

    const char *nextScope = (n->node == decl && n->declSubType == declFunc)
                            ? n->name
                            : scope;

    for (int i = 0; i < CHILD_MAX_NODES; i++)
        if (n->child[i])
            analyzeNode(n->child[i], ctx, nextScope);

    if (n->sibling)
        analyzeNode(n->sibling, ctx, scope);

    if (n->node == exp) {
        switch (n->expSubType) {
            case expId:
                if (!findSymbol(&ctx->symbols, n->name, scope)) {
                    reportError(ctx,
                        "Line %d: '%s' undeclared in '%s'",
                        n->line, n->name, scope);
                }
                break;

            case expCall: {
                Symbol *sym = findSymbol(&ctx->symbols, n->name, "global");
                if (!sym || sym->type != FUNC) {
                    reportError(ctx,
                        "Line %d: '%s' is not a function",
                        n->line, n->name);
                    n->type = Void;
                } else {
                    n->type = sym->dataType;

                    int given = 0;
                    treeNode *arg = n->child[0];
                    while (arg) {
                        given++;
                        arg = arg->sibling;
                    }

                    if (given != (int)sym->paramCount) {
                        reportError(ctx,
                            "Line %d: '%s' expects %zu args, received %d",
                            n->line, n->name,
                            sym->paramCount, given);
                    }

                    treeNode *argNode = n->child[0];
                    for (int i = 0; i < (int)sym->paramCount && argNode; i++) {
                        primitiveType got = argNode->type;
                        if (got != sym->paramTypes[i]) {
                            reportError(ctx,
                                "Line %d: arg %d of '%s' is %s, expected %s",
                                n->line, i + 1, n->name,
                                primitiveTypeToString(got),
                                primitiveTypeToString(sym->paramTypes[i]));
                        }
                        argNode = argNode->sibling;
                    }
                }
                break;
            }

            default:
                break;
        }
    }
    else if (n->node == stmt) {
        switch (n->stmtSubType) {
            case stmtAttrib: {
                if (!n->child[0] || !n->child[1]) break;
                char *v = n->child[0]->name;
                Symbol *sym = findSymbol(&ctx->symbols, v, scope);
                primitiveType rhs = n->child[1]->type;
                if (!sym) {
                    reportError(ctx,
                        "Line %d: '%s' undeclared",
                        n->line, v);
                } else if (sym->dataType != rhs) {
                    reportError(ctx,
                        "Line %d: assignment to '%s' expects %s, got %s",
                        n->line, v,
                        primitiveTypeToString(sym->dataType),
                        primitiveTypeToString(rhs));
                }
                break;
            }
            case stmtReturn: {
                Symbol *fn = findSymbol(&ctx->symbols, scope, "global");
                primitiveType ret = n->child[0] ? n->child[0]->type : Void;
                if (fn && fn->dataType != ret) {
                    reportError(ctx,
                        "Line %d: return in '%s' returns %s, declared %s",
                        n->line, scope,
                        primitiveTypeToString(ret),
                        primitiveTypeToString(fn->dataType));
                }
                break;
            }
            default:
                break;
        }
    }
}

void semanticAnalysis(treeNode *root) {
    SemanticContext ctx;
    initSemanticContext(&ctx);
    prepareBuiltInsAndMain(&ctx);
    analyzeNode(root, &ctx, "global");

    if (!findSymbol(&ctx.symbols, "main", "global")) {
        reportError(&ctx, "Function 'main' not declared");
    }

    printSemanticResults(&ctx);
}

void printSemanticResults(SemanticContext *ctx) {
    if (!ctx->errors) {
        printf("Semantic analysis completed successfully.\n");
    } else {
        for (ErrorNode *e = ctx->errors; e; e = e->next) {
            printf("Semantic error: %s\n", e->message);
        }
        exit(EXIT_FAILURE);
    }
}
