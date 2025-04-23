// semantic.c
#include "semantic.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>

// ------------------------------------------------------------
// Error-list helpers
// ------------------------------------------------------------
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

// ------------------------------------------------------------
// Initialization & Built-ins
// ------------------------------------------------------------
void initSemanticContext(SemanticContext *ctx) {
    initSymbolTable(&ctx->symbols);
    ctx->errors = NULL;
}

void prepareBuiltInsAndMain(SemanticContext *ctx) {
    // 1) Built-ins
    insertSymbol(&ctx->symbols, "input",  "global", FUNC, 0, Integer);
    insertSymbol(&ctx->symbols, "output", "global", FUNC, 0, Void);

    // 2) main() must be declared somewhere in the user code
    //    We’ll check *after* the AST walk, so here is a placeholder.
}

// ------------------------------------------------------------
// Recursive AST Walker
// ------------------------------------------------------------
void analyzeNode(treeNode *n, SemanticContext *ctx, const char *scope) {
    if (!n) return;

    switch (n->node) {
      case decl:
        if (n->nodeSubType.decl == declVar) {
            // (3) void-only-for-functions rule
            if (n->type == Void) {
                reportError(ctx,
                    "Declaração inválida na linha %d: variável '%s' não pode ser void",
                    n->line, n->key.name);
            }
            // (4 & 5) duplicate declarations: var vs. var, var vs. func, func vs. var
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
            // duplicate function names
            if (findSymbol(&ctx->symbols, n->key.name, "global")) {
                reportError(ctx,
                    "Função '%s' redeclarada na linha %d",
                    n->key.name, n->line);
            } else {
                insertSymbol(&ctx->symbols,
                             n->key.name, "global",
                             FUNC, n->line, n->type);
            }
            // parameters are in child[0], body in child[1]
            analyzeNode(n->child[0], ctx, n->key.name);
            analyzeNode(n->child[1], ctx, "global");
        }
        break;

      case exp:
        if (n->nodeSubType.exp == expId) {
            // (1) undeclared-variable or function
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
                // (2) invalid-assignment: type mismatch
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
            // (2) return-type mismatch
            // scope holds the *current* function name
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
            // (6) function-call undeclared
            if (!findSymbol(&ctx->symbols, n->key.name, "global")) {
                reportError(ctx,
                    "Chamada de função '%s' não declarada (linha %d)",
                    n->key.name, n->line);
            }
            // TODO: check argument count/types here
            break;
          }
          default:
            break;
        }
        break;

      default:
        break;
    }

    // Recurse into children (new scope only for declFunc’s body)
    for (int i = 0; i < CHILD_MAX_NODES; i++) {
        analyzeNode(n->child[i], ctx, scope);
    }
    // Then siblings stay in same scope
    analyzeNode(n->sibling, ctx, scope);
}

// ------------------------------------------------------------
// Top-Level Driver
// ------------------------------------------------------------
void semanticAnalysis(treeNode *root) {
    SemanticContext ctx;
    initSemanticContext(&ctx);
    prepareBuiltInsAndMain(&ctx);

    // Walk entire tree starting in global scope
    analyzeNode(root, &ctx, "global");

    // (7) missing-main check
    if (!findSymbol(&ctx.symbols, "main", "global")) {
        reportError(&ctx, "Função 'main' não declarada");
    }

    // Print results
    printSemanticResults(&ctx);
}

void printSemanticResults(SemanticContext *ctx) {
    if (!ctx->errors) {
        printf("Análise semântica concluída com sucesso.\n");
    } else {
        // Print and exit with failure
        for (ErrorNode *e = ctx->errors; e; e = e->next) {
            printf("Erro semântico: %s\n", e->message);
        }
        exit(EXIT_FAILURE);
    }
}
