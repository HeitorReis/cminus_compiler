// semantic.c

#include <stdio.h>
#include <stdarg.h>
#include "semantic.h"

// forward declarations
static void analyzeProgram(AstNode *prog, SemanticContext *ctx);
static void analyzeDeclaration(AstNode *decl, SemanticContext *ctx);
static void analyzeBlock(AstNode *block, SemanticContext *ctx);
static void analyzeStatement(AstNode *stmt, SemanticContext *ctx);
static ExpType analyzeExpression(AstNode *expr, SemanticContext *ctx);

// error‐reporting helper
static void semanticError(int line, SemanticContext *ctx, const char *fmt, ...) {
    va_list ap;
    fprintf(stderr, "[Semantic:%d] ", line);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fprintf(stderr, "\n");
    ctx->errorCount++;
}

// entry point
void semanticAnalyze(AstNode *root, SymbolTable *symtab) {
    SemanticContext ctx = {
        .symtab     = symtab,
        .curRetType = TYPE_VOID,
        .errorCount = 0
    };

    if (!root || root->kind != AST_PROGRAM) {
        fprintf(stderr, "Internal error: semanticAnalyze expects AST_PROGRAM\n");
        return;
    }

    analyzeProgram(root, &ctx);

    printf("Semantic analysis found %d error(s).\n", ctx.errorCount);
}

// stub implementations to be filled in:
static void analyzeProgram(AstNode *prog, SemanticContext *ctx) {
    printf("[Semantic DBG] analyzeProgram: entering program node\n");
    /* prog is your AST_PROGRAM node; its firstChild points at the first declaration */
    for (AstNode *decl = prog->firstChild; decl; decl = decl->nextSibling) {
        printf("[Semantic DBG] declaration: kind=%d", decl->kind);
        if (decl->name)
            printf(" name=\"%s\"", decl->name);
        printf(" at line %d\n", decl->lineno);
        analyzeDeclaration(decl, ctx);
    }
}

static void analyzeDeclaration(AstNode *decl, SemanticContext *ctx) {
    // Debug print to verify this is running
    printf("[Semantic DBG] analyzeDeclaration: kind=%d", decl->kind);
    if (decl->name)
        printf(" name=\"%s\"", decl->name);
    printf(" line=%d\n", decl->lineno);

    switch (decl->kind) {
    case AST_VAR_DECL:
        AstNode *typeNode = decl->firstChild;
        const char *typeName = typeNode ? typeNode->name : "unknown";
        printf(
            "[Semantic DBG]   VarDecl: type=%s name=%s\n",
            typeName, 
            decl->name
        );

        if (strcmp(typeName, "void") == 0) {
            semanticError(
                decl->lineno, 
                ctx,
                "variable '%s' declared void", 
                decl->name
            );
        }
        break;

    case AST_FUN_DECL:
        // TODO: later, set ctx->curRetType, push scope, analyze body
        break;

    default:
        // other top‐level nodes?
        break;
    }
}


static void analyzeBlock(AstNode *block, SemanticContext *ctx) {
    /* TODO: for each child, either analyzeDeclaration() or analyzeStatement() */
}

static void analyzeStatement(AstNode *stmt, SemanticContext *ctx) {
    /* TODO: handle AST_IF, AST_WHILE, AST_RETURN, AST_ASSIGN, AST_CALL, AST_BLOCK, etc. */
}

static ExpType analyzeExpression(AstNode *expr, SemanticContext *ctx) {
    /* TODO: handle AST_NUM, AST_ID, AST_BINOP, AST_ASSIGN, AST_CALL */
    return TYPE_ERROR;
}
