// semantic.c

#include <stdio.h>
#include <stdarg.h>
#include "semantic.h"
#include "ir.h"

extern char *currentScope;

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

    if (ctx.errorCount > 0)
        fprintf(stderr, "Semantic analysis found %d error(s).\n", ctx.errorCount);
    else{
        printf("Semantic analysis completed successfully with no errors.\n");
        printf("\n=== IR ===\n");
        
        // To this:
        IRList *ir = generate_ir(root, &symtab); // Assuming you pass the symbol table
        print_ir(ir, stdout);
        
        printf("\n=== Codegen ===\n");
        generate_code(ir, "out.asm"); 
        
        free_ir(ir);
    }

    printf("[Codegen DBG] codeGen: completed\n", ctx.errorCount);

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
        printf(
            "[Semantic DBG] FunDecl: name=\"%s\" line=%d\n",
            decl->name, 
            decl->lineno
        );

        Symbol *fsym = getSymbol(ctx->symtab, decl->name, "global");
        if (!fsym){
            semanticError(
                decl->lineno,
                ctx,
                "internal error: function '%s' not found in symbol table",
                decl->name
            );
            break;
        }

        ctx->curRetType = (fsym->dataType == TYPE_INT? TYPE_INT : TYPE_VOID);
        printf(
            "[Semantic DBG]   return-type = %s\n",
            ctx->curRetType==TYPE_INT ? "int" : "void"
        );

        char *outerScope = currentScope;
        currentScope = decl->name; // set current scope to function name
        printf("[Semantic DBG]  switched currentScope = %s\n", currentScope);

        AstNode *child = decl->firstChild;
        AstNode *paramList = NULL;
        AstNode *body = NULL;
        int pcount = 0;
        if (child && child->kind == AST_PARAM_LIST) {
            paramList = child; // first child is the parameter list
            body = child->nextSibling; // next sibling is the block
            printf("[Semantic DBG]   Found parameter list\n");
            for (AstNode *param = paramList->firstChild; param; param = param->nextSibling, ++pcount) {
                printf(
                    "[Semantic DBG]   Param: name=\"%s\" line=%d\n",
                    param->name, 
                    param->lineno
                );
            }
        } else {
            body = child; // no parameters, just a block
            printf("[Semantic DBG]   No parameters, just a block\n");
        }

        if (body && body->kind == AST_BLOCK) {
            analyzeBlock(body, ctx);
        } else {
            semanticError(
                decl->lineno, 
                ctx,
                "expected block in function '%s'",
                decl->name
            );
        }

        currentScope = outerScope; // restore outer scope
        printf("[Semantic DBG]   currentScope restored to %s\n", currentScope);

        break;

    default:
        // other top‐level nodes?
        break;
    }
}


static void analyzeBlock(AstNode *block, SemanticContext *ctx) {
    printf("[Semantic DBG] analyzeBlock: scope=\"%s\"\n", currentScope);
    for (AstNode *c = block->firstChild; c; c = c->nextSibling) {
        if (c->kind == AST_VAR_DECL) {
            analyzeDeclaration(c, ctx);
        } else {
            printf(
                "[Semantic DBG]   Statement: kind=%d line=%d\n",
                c->kind, 
                c->lineno
            );
            analyzeStatement(c, ctx);
        }
    }
}

static void analyzeStatement(AstNode *stmt, SemanticContext *ctx) {
    printf("[Semantic DBG] → analyzeStatement(stmt=%p, kind=%d, line=%d)\n",
        (void*)stmt,
        stmt ? stmt->kind : -1,
        stmt ? stmt->lineno : -1);
    if (!stmt) {
        fprintf(stderr, "[Semantic DBG] NULL statement, skipping\n");
        return;
    }

    switch (stmt->kind) {
    case AST_IF: {
        AstNode *cond = stmt->firstChild;
        if (!cond) {
            semanticError(stmt->lineno, ctx, "if with no condition");
            break;
        }
        ExpType ct = analyzeExpression(cond, ctx);
        if (ct != TYPE_INT) {
            semanticError(stmt->lineno, ctx, "non-int condition in if");
        }
        AstNode *thenSt = cond->nextSibling;
        if (!thenSt) {
            semanticError(stmt->lineno, ctx, "if with no then-branch");
        } else {
            analyzeStatement(thenSt, ctx);
        }
        AstNode *elseSt = thenSt ? thenSt->nextSibling : NULL;
        if (elseSt) analyzeStatement(elseSt, ctx);
        break;
    }

    case AST_WHILE: {
        AstNode *cond = stmt->firstChild;
        if (!cond) {
            semanticError(stmt->lineno, ctx, "while with no condition");
            break;
        }
        ExpType ct = analyzeExpression(cond, ctx);
        if (ct != TYPE_INT) {
            semanticError(stmt->lineno, ctx, "non-int condition in while");
        }
        AstNode *body = cond->nextSibling;
        if (!body) {
            semanticError(stmt->lineno, ctx, "while with no body");
        } else {
            analyzeStatement(body, ctx);
        }
        break;
    }

    case AST_RETURN: {
        AstNode *expr = stmt->firstChild;
        if (!expr) {
            if (ctx->curRetType != TYPE_VOID) {
                semanticError(stmt->lineno, ctx,
                    "return with no value in non-void function");
            }
        } else {
            ExpType rt = analyzeExpression(expr, ctx);
            if (rt != ctx->curRetType) {
                semanticError(stmt->lineno, ctx,
                    "return type mismatch: expected %s, got %s",
                    ctx->curRetType==TYPE_INT?"int":"void",
                    rt==TYPE_INT?"int":"void");
            }
        }
        break;
    }

    case AST_BLOCK:
        analyzeBlock(stmt, ctx);
        break;

    default:
        // assignment, call, or bare expression
        analyzeExpression(stmt, ctx);
    }

    printf("[Semantic DBG] ← analyzeStatement(stmt=%p)\n", (void*)stmt);
}

static ExpType analyzeExpression(AstNode *expr, SemanticContext *ctx) {
    printf("[Semantic DBG] → analyzeExpression(expr=%p, kind=%d, line=%d)\n",
        (void*)expr,
        expr ? expr->kind : -1,
        expr ? expr->lineno : -1);
    if (!expr) {
        fprintf(stderr, "[Semantic DBG] NULL expression, defaulting to ERROR\n");
        return TYPE_ERROR;
    }

    ExpType result = TYPE_ERROR;
    switch (expr->kind) {
    case AST_NUM:
        result = TYPE_INT;
        break;

    case AST_ID: {
        Symbol *s = getSymbol(ctx->symtab, expr->name, currentScope);
        if (!s) {
            semanticError(expr->lineno, ctx,
                        "use of undeclared identifier '%s'",
                        expr->name);
            result = TYPE_ERROR;
        } else {
            result = (
                s->dataType == TYPE_INT ? 
                TYPE_INT : TYPE_VOID);
        }
        break;
    }

    case AST_BINOP: {
        AstNode *left  = expr->firstChild;
        AstNode *op    = left ? left->nextSibling : NULL;
        AstNode *right = op   ? op->nextSibling  : NULL;
        if (!left || !op || !right) {
            semanticError(expr->lineno, ctx, "malformed binop node");
            result = TYPE_ERROR;
        } else {
            ExpType lt = analyzeExpression(left, ctx);
            ExpType rt = analyzeExpression(right, ctx);
            if (lt!=TYPE_INT || rt!=TYPE_INT) {
                semanticError(expr->lineno, ctx,
                            "non-int operand in binary op '%s'",
                            op->name ? op->name : "<op>");
            }
            result = TYPE_INT;
        }
        break;
    }

    case AST_ASSIGN: {
        AstNode *lval = expr->firstChild;
        AstNode *rval = lval ? lval->nextSibling : NULL;
        if (!lval || lval->kind!=AST_ID) {
            semanticError(expr->lineno, ctx,
                        "lhs of assignment not an identifier");
        }
        if (!rval) {
            semanticError(expr->lineno, ctx,
                        "assignment with no right-hand side");
            result = TYPE_ERROR;
        } else {
            ExpType rt = analyzeExpression(rval, ctx);
            if (rt != TYPE_INT) {
                semanticError(expr->lineno, ctx,
                            "rhs of assignment not int");
            }
            result = TYPE_INT;
        }
        break;
    }

    case AST_CALL: {
        Symbol *f = getSymbol(ctx->symtab, expr->name, "global");
        if (!f || f->kind!=SYMBOL_FUNC) {
            semanticError(expr->lineno, ctx,
                        "call to undeclared function '%s'",
                        expr->name);
            result = TYPE_ERROR;
            break;
        }
        AstNode *args = expr->firstChild;
        int got = 0;
        for (AstNode *a = args ? args->firstChild : NULL;
            a;
            a = a->nextSibling, ++got) {
            ExpType at = analyzeExpression(a, ctx);
            int want = getParamType(ctx->symtab, expr->name, "global", got);
            if (at!=want) {
                semanticError(expr->lineno, ctx,
                            "arg %d to '%s' expects %s but got %s",
                            got+1, expr->name,
                            want==TYPE_INT?"int":"void",
                            at  ==TYPE_INT?"int":"void");
            }
        }
        int wantCount = getParamCount(ctx->symtab, expr->name, "global");
        if (got!=wantCount) {
            semanticError(expr->lineno, ctx,
                        "function '%s' called with %d args; expected %d",
                        expr->name, got, wantCount);
        }
        result = (f->dataType==TYPE_INT ? TYPE_INT : TYPE_VOID);
        break;
    }

    default:
        fprintf(stderr, "[Semantic DBG] unhandled expr kind=%d\n",
                expr->kind);
        result = TYPE_ERROR;
    }

    printf("[Semantic DBG] ← analyzeExpression(expr=%p) returns %d\n",
        (void*)expr, result);
    return result;
}