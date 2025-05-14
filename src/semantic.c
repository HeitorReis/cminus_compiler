#include "semantic.h"
#include "symbol_table.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

/* — reportError — */
void reportError(SemanticContext *ctx, const char *fmt, ...) {
    char buf[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    ErrorNode *e = malloc(sizeof(*e));
    e->message = strdup(buf);
    e->next    = ctx->errors;
    ctx->errors = e;
}

/* — initSemanticContext — */
void initSemanticContext(SemanticContext *ctx) {
    initSymbolTable(&ctx->symbols);
    ctx->errors = NULL;
}

/* — prepareBuiltInsAndMain — */
void prepareBuiltInsAndMain(SemanticContext *ctx) {
    Symbol *s;
    /* input():int */
    insertSymbol(&ctx->symbols, "input",  "global", FUNC, 0, Integer);
    s = findSymbol(&ctx->symbols, "input", "global");
    s->paramCount = 0;
    s->paramTypes = NULL;
    /* output(int):void */
    insertSymbol(&ctx->symbols, "output", "global", FUNC, 0, Void);
    s = findSymbol(&ctx->symbols, "output", "global");
    s->paramCount = 1;
    s->paramTypes = malloc(sizeof(primitiveType));
    s->paramTypes[0] = Integer;
}

/* — analyzeNode — */
void analyzeNode(treeNode *n, SemanticContext *ctx, const char *scope) {
    if (!n) return;

    if (n->node == decl) {
        if (n->nodeSubType.decl == declVar) {
            if (n->type == Void) {
                reportError(ctx,
                    "Linha %d: variável '%s' não pode ser void",
                    n->line, n->key.name);
            }
            if (findSymbol(&ctx->symbols, n->key.name, scope)) {
                reportError(ctx,
                    "Linha %d: '%s' já declarado em '%s'",
                    n->line, n->key.name, scope);
            } else {
                insertSymbol(&ctx->symbols,
                             n->key.name, scope,
                             VAR, n->line, n->type);
            }
        }
        else if (n->nodeSubType.decl == declFunc) {
            if (findSymbol(&ctx->symbols, n->key.name, "global")) {
                reportError(ctx,
                    "Linha %d: função '%s' redeclarada",
                    n->line, n->key.name);
            } else {
                insertSymbol(&ctx->symbols,
                             n->key.name, "global",
                             FUNC, n->line, n->type);
            }
        }
    }

    /* --- Recurse filhos/siblings --- */
    const char *nextScope = (n->node == decl &&
                             n->nodeSubType.decl == declFunc)
                            ? n->key.name
                            : scope;
    for (int i = 0; i < CHILD_MAX_NODES; i++)
        if (n->child[i])
            analyzeNode(n->child[i], ctx, nextScope);
    if (n->sibling)
        analyzeNode(n->sibling, ctx, scope);

    /* --- Pós-ordem: checagem de expressões e statements --- */

    if (n->node == exp) {
        switch (n->nodeSubType.exp) {
          case expId:
            if (!findSymbol(&ctx->symbols, n->key.name, scope)) {
                reportError(ctx,
                    "Linha %d: '%s' não declarado em '%s'",
                    n->line, n->key.name, scope);
            }
            break;

          case expCall: {
            /* Chamada em expressão */
            Symbol *sym = findSymbol(&ctx->symbols,
                                     n->key.name, "global");
            if (!sym || sym->type != FUNC) {
                reportError(ctx,
                    "Linha %d: '%s' não é função",
                    n->line, n->key.name);
                n->type = Void;
            } else {
                n->type = sym->dataType;
                int given = 0;
                for (int i = 0; i < CHILD_MAX_NODES; i++)
                    if (n->child[i]) given++;
                /* child[0] aridade variável, mas anticipate children */
                /* Ajuste: se só child[0] guarda args-list,
                   use childCount se migrado para dynamic */
                if (given != (int)sym->paramCount) {
                    reportError(ctx,
                        "Linha %d: '%s' espera %zu args, recebeu %d",
                        n->line, n->key.name,
                        sym->paramCount, given);
                }
                for (int i = 0; i < (int)sym->paramCount && i < given; i++) {
                    primitiveType got = n->child[i]->type;
                    if (got != sym->paramTypes[i]) {
                        reportError(ctx,
                            "Linha %d: arg %d de '%s' é %s, esperava %s",
                            n->line, i+1, n->key.name,
                            primitiveTypeToString(got),
                            primitiveTypeToString(sym->paramTypes[i]));
                    }
                }
            }
            break;
          }

          default:
            break;
        }
    }
    else if (n->node == stmt) {
        switch (n->nodeSubType.stmt) {
          case stmtAttrib: {
            char *v = n->child[0]->key.name;
            Symbol *sym = findSymbol(&ctx->symbols, v, scope);
            primitiveType rhs = n->child[1]->type;
            if (!sym) {
                reportError(ctx,
                    "Linha %d: '%s' não declarado",
                    n->line, v);
            } else if (sym->dataType != rhs) {
                reportError(ctx,
                    "Linha %d: atribuição a '%s' espera %s, obtido %s",
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
                    "Linha %d: return em '%s' retorna %s, declarou %s",
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

/* — semanticAnalysis — */
void semanticAnalysis(treeNode *root) {
    SemanticContext ctx;
    initSemanticContext(&ctx);
    prepareBuiltInsAndMain(&ctx);
    analyzeNode(root, &ctx, "global");
    if (!findSymbol(&ctx.symbols, "main", "global")) {
        reportError(&ctx,
            "Função 'main' não declarada");
    }
    printSemanticResults(&ctx);
}

/* — printSemanticResults — */
void printSemanticResults(SemanticContext *ctx) {
    if (!ctx->errors) {
        printf("Análise semântica concluída com sucesso.\n");
    } else {
        for (ErrorNode *e = ctx->errors; e; e = e->next) {
            printf("Erro semântico: %s\n", e->message);
        }
        exit(EXIT_FAILURE);
    }
}
