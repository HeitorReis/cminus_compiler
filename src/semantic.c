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
    insertSymbol(&ctx->symbols, "input",  "global", FUNC, 0, Integer);
    insertSymbol(&ctx->symbols, "output", "global", FUNC, 0, Void);
}

void analyzeNode(treeNode *n, SemanticContext *ctx, const char *scope) {
    if (!n) return;

    switch (n->node) {
        case decl:
            if (n->nodeSubType.decl == declVar) {
                if (n->type == Void) {
                    reportError(ctx,
                        "Declaração inválida na linha %d: variável '%s' não pode ser void",
                        n->line, n->key.name);
                }
                if (findSymbol(&ctx->symbols, n->key.name, scope)) {
                    reportError(ctx,
                        "Redeclaração na linha %d: '%s' já declarado em escopo '%s'",
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
                        "Função '%s' redeclarada na linha %d",
                        n->key.name, n->line);
                } else {
                    insertSymbol(&ctx->symbols,
                                n->key.name, "global",
                                FUNC, n->line, n->type);
                }
                analyzeNode(n->child[0], ctx, n->key.name);
                analyzeNode(n->child[1], ctx, n->key.name);
            }
            break;

    case exp:
        if (n->nodeSubType.exp == expId) {
            if (!findSymbol(&ctx->symbols, n->key.name, scope)) {
                reportError(ctx,
                    "Símbolo '%s' não declarado no escopo '%s' (linha %d)",
                    n->key.name, scope, n->line);
            }
        }
        break;

    case stmt:
        switch (n->nodeSubType.stmt) {
            case stmtAttrib: {
                char *varName = n->child[0]->key.name;
                Symbol *sym = findSymbol(&ctx->symbols, varName, scope);
                if (!sym) {
                    reportError(ctx,
                        "Atribuição a '%s' não declarada (linha %d)",
                        varName, n->line);
                } else {
                    primitiveType rhsType = n->child[1]->type;
                    if (sym->dataType != rhsType) {
                        reportError(ctx,
                            "Tipo inválido em atribuição a '%s' (esperado %s, obtido %s) na linha %d",
                            varName,
                            primitiveTypeToString(sym->dataType),
                            primitiveTypeToString(rhsType),
                            n->line);
                    }
                }
                break;
            }
            case stmtReturn: {
                Symbol *fn = findSymbol(&ctx->symbols, scope, "global");
                primitiveType retT = n->child[0] ? n->child[0]->type : Void;
                if (fn && fn->dataType != retT) {
                    reportError(ctx,
                        "Return em '%s' retorna %s mas declarado como %s (linha %d)",
                        scope,
                        primitiveTypeToString(retT),
                        primitiveTypeToString(fn->dataType),
                        n->line);
                }
                break;
            }
            case stmtFunc: {
                if (!findSymbol(&ctx->symbols, n->key.name, "global")) {
                    reportError(ctx,
                        "Chamada de função '%s' não declarada (linha %d)",
                        n->key.name, n->line);
                }
                break;
            }
            default:
                break;
        }
        break;
    
    default:
        break;
    }
    
    for (int i = 0; i < CHILD_MAX_NODES; i++) {
        if (n->child[i]) {
            analyzeNode(n->child[i], ctx, scope);
        }
    }
    if (n->sibling) {
        analyzeNode(n->sibling, ctx, scope);
    }
}

void semanticAnalysis(treeNode *root) {
    SemanticContext ctx;
    initSemanticContext(&ctx);
    prepareBuiltInsAndMain(&ctx);
    analyzeNode(root, &ctx, "global");
    if (!findSymbol(&ctx.symbols, "main", "global")) {
        reportError(&ctx, "Função 'main' não declarada");
    }
    printSemanticResults(&ctx);
}

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
