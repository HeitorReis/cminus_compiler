#include <stdarg.h>
#include <stdio.h>

#include "ir.h"
#include "semantic.h"
#include "utils.h"

extern char *currentScope;

typedef struct {
    SymbolTable *symtab;
    ExpType cur_ret_type;
    int error_count;
} SemanticContext;

static const char *const IR_OUTPUT_PATH = "docs/output/generated_IR.txt";

static void analyzeProgram(AstNode *prog, SemanticContext *ctx);
static void analyzeDeclaration(AstNode *decl, SemanticContext *ctx);
static void analyzeFunctionDeclaration(AstNode *decl, SemanticContext *ctx);
static void analyzeVariableDeclaration(AstNode *decl, SemanticContext *ctx);
static void analyzeBlock(AstNode *block, SemanticContext *ctx);
static void analyzeStatement(AstNode *stmt, SemanticContext *ctx);
static ExpType analyzeExpression(AstNode *expr, SemanticContext *ctx);
static ExpType analyzeAssignmentTarget(AstNode *expr, SemanticContext *ctx);
static ExpType analyzeArrayAccess(AstNode *expr, SemanticContext *ctx);
static int blockGuaranteesReturn(const AstNode *block);
static int statementGuaranteesReturn(const AstNode *stmt);
static int hasEarlierDeclaration(const Symbol *symbol, int line);
static int hasMainFunction(SymbolTable *symtab);
static const char *typeName(ExpType type);
static void semanticError(int line, SemanticContext *ctx, const char *fmt, ...);

static void semanticError(int line, SemanticContext *ctx, const char *fmt, ...) {
    va_list args;

    fprintf(stderr, "[Semantic:%d] ", line);
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fprintf(stderr, "\n");

    ctx->error_count++;
}

static const char *typeName(ExpType type) {
    switch (type) {
        case TYPE_INT:
            return "int";
        case TYPE_VOID:
            return "void";
        case TYPE_ARRAY:
            return "array";
        default:
            return "error";
    }
}

static int hasEarlierDeclaration(const Symbol *symbol, int line) {
    int seen_prior = 0;

    if (!symbol) {
        return 0;
    }

    for (const LineNode *node = symbol->declLines; node; node = node->next) {
        if (node->line == line) {
            return seen_prior;
        }
        seen_prior = 1;
    }

    return 0;
}

static int hasMainFunction(SymbolTable *symtab) {
    Symbol *symbol = getSymbol(symtab, "main", "global");
    return symbol && symbol->kind == SYMBOL_FUNC;
}

SemanticReport semanticAnalyze(AstNode *root, SymbolTable *symtab) {
    SemanticContext ctx = {
        .symtab = symtab,
        .cur_ret_type = TYPE_VOID,
        .error_count = 0,
    };
    SemanticReport report = {0, 0};

    remove(IR_OUTPUT_PATH);

    if (!root || root->kind != AST_PROGRAM) {
        fprintf(stderr, "Internal error: semanticAnalyze expects AST_PROGRAM\n");
        report.error_count = 1;
        return report;
    }

    initScopeStack();
    analyzeProgram(root, &ctx);

    report.error_count = ctx.error_count;
    report.missing_main = hasMainFunction(symtab) ? 0 : 1;

    if (report.error_count == 0 && report.missing_main == 0) {
        IRList *ir;

        printf("Semantic analysis completed successfully with no errors.\n");
        printf("\n=== IR ===\n");

        ir = generate_ir(root, symtab);
        print_ir(ir, (char *)IR_OUTPUT_PATH);
        free_ir(ir);
    }

    return report;
}

static void analyzeProgram(AstNode *prog, SemanticContext *ctx) {
    for (AstNode *decl = prog->firstChild; decl; decl = decl->nextSibling) {
        analyzeDeclaration(decl, ctx);
    }
}

static void analyzeDeclaration(AstNode *decl, SemanticContext *ctx) {
    if (!decl) {
        return;
    }

    switch (decl->kind) {
        case AST_VAR_DECL:
            analyzeVariableDeclaration(decl, ctx);
            break;
        case AST_FUN_DECL:
            analyzeFunctionDeclaration(decl, ctx);
            break;
        default:
            break;
    }
}

static void analyzeVariableDeclaration(AstNode *decl, SemanticContext *ctx) {
    Symbol *symbol;

    symbol = getSymbol(ctx->symtab, decl->name, currentScope);
    if (!symbol) {
        semanticError(decl->lineno, ctx,
                      "internal error: symbol '%s' not found in scope '%s'",
                      decl->name, currentScope);
        return;
    }

    if (symbol->kind != SYMBOL_VAR || hasEarlierDeclaration(symbol, decl->lineno)) {
        semanticError(decl->lineno, ctx, "redeclared identifier '%s'", decl->name);
    }

    if (decl->array_size > 0) {
        symbol->dataType = TYPE_ARRAY;
        symbol->baseType = decl->data_type;
        symbol->array_size = decl->array_size;

        if (decl->data_type == TYPE_VOID) {
            semanticError(decl->lineno, ctx, "array '%s' declared void", decl->name);
        }
    } else {
        symbol->dataType = decl->data_type;
        symbol->baseType = 0;
        symbol->array_size = 0;

        if (decl->data_type == TYPE_VOID) {
            semanticError(decl->lineno, ctx, "variable '%s' declared void", decl->name);
        }
    }
}

static void analyzeFunctionDeclaration(AstNode *decl, SemanticContext *ctx) {
    Symbol *function_symbol;
    AstNode *child;
    AstNode *param_list = NULL;
    AstNode *body = NULL;
    ExpType previous_ret_type;

    function_symbol = getSymbol(ctx->symtab, decl->name, "global");
    if (!function_symbol) {
        semanticError(decl->lineno, ctx,
                      "internal error: function '%s' not found in symbol table",
                      decl->name);
        return;
    }

    if (function_symbol->kind != SYMBOL_FUNC ||
        hasEarlierDeclaration(function_symbol, decl->lineno)) {
        semanticError(decl->lineno, ctx, "redeclared identifier '%s'", decl->name);
    }

    child = decl->firstChild;
    if (child && child->kind == AST_PARAM_LIST) {
        param_list = child;
        body = child->nextSibling;
    } else {
        body = child;
    }

    if (param_list) {
        for (AstNode *param = param_list->firstChild; param; param = param->nextSibling) {
            Symbol *param_symbol = getSymbol(ctx->symtab, param->name, decl->name);

            if (!param_symbol) {
                semanticError(param->lineno, ctx,
                              "internal error: parameter '%s' not found in scope '%s'",
                              param->name, decl->name);
                continue;
            }

            if (param_symbol->kind != SYMBOL_VAR ||
                hasEarlierDeclaration(param_symbol, param->lineno)) {
                semanticError(param->lineno, ctx,
                              "redeclared identifier '%s'", param->name);
            }

            if (param->kind == AST_PARAM_ARRAY) {
                param_symbol->dataType = TYPE_ARRAY;
                param_symbol->baseType = param->data_type;
                param_symbol->array_size = -1;
            } else {
                param_symbol->dataType = param->data_type;
                param_symbol->baseType = 0;
                param_symbol->array_size = 0;
            }

            if (param->data_type == TYPE_VOID) {
                semanticError(param->lineno, ctx,
                              param->kind == AST_PARAM_ARRAY
                                  ? "array parameter '%s' declared void"
                                  : "parameter '%s' declared void",
                              param->name);
            }
        }
    }

    previous_ret_type = ctx->cur_ret_type;
    ctx->cur_ret_type = (decl->data_type == TYPE_INT) ? TYPE_INT : TYPE_VOID;

    pushScope(decl->name);
    if (body && body->kind == AST_BLOCK) {
        analyzeBlock(body, ctx);
        if (ctx->cur_ret_type == TYPE_INT && !blockGuaranteesReturn(body)) {
            semanticError(decl->lineno, ctx,
                          "non-void function '%s' does not return a value on all paths",
                          decl->name);
        }
    } else {
        semanticError(decl->lineno, ctx, "expected block in function '%s'", decl->name);
    }
    popScope();

    ctx->cur_ret_type = previous_ret_type;
}

static void analyzeBlock(AstNode *block, SemanticContext *ctx) {
    int pushed_scope = 0;

    if (!block) {
        return;
    }

    if (block->name) {
        pushScope(block->name);
        pushed_scope = 1;
    }

    for (AstNode *child = block->firstChild; child; child = child->nextSibling) {
        if (child->kind == AST_VAR_DECL) {
            analyzeVariableDeclaration(child, ctx);
        } else {
            analyzeStatement(child, ctx);
        }
    }

    if (pushed_scope) {
        popScope();
    }
}

static void analyzeStatement(AstNode *stmt, SemanticContext *ctx) {
    AstNode *condition;
    AstNode *then_stmt;
    AstNode *else_stmt;
    AstNode *body;
    ExpType condition_type;
    ExpType returned_type;

    if (!stmt) {
        return;
    }

    switch (stmt->kind) {
        case AST_IF:
            condition = stmt->firstChild;
            if (!condition) {
                semanticError(stmt->lineno, ctx, "if with no condition");
                return;
            }

            condition_type = analyzeExpression(condition, ctx);
            if (condition_type != TYPE_INT) {
                semanticError(stmt->lineno, ctx, "non-int condition in if");
            }

            then_stmt = condition->nextSibling;
            else_stmt = then_stmt ? then_stmt->nextSibling : NULL;
            if (!then_stmt) {
                semanticError(stmt->lineno, ctx, "if with no then-branch");
                return;
            }

            analyzeStatement(then_stmt, ctx);
            if (else_stmt) {
                analyzeStatement(else_stmt, ctx);
            }
            return;

        case AST_WHILE:
            condition = stmt->firstChild;
            if (!condition) {
                semanticError(stmt->lineno, ctx, "while with no condition");
                return;
            }

            condition_type = analyzeExpression(condition, ctx);
            if (condition_type != TYPE_INT) {
                semanticError(stmt->lineno, ctx, "non-int condition in while");
            }

            body = condition->nextSibling;
            if (!body) {
                semanticError(stmt->lineno, ctx, "while with no body");
                return;
            }

            analyzeStatement(body, ctx);
            return;

        case AST_RETURN:
            if (!stmt->firstChild) {
                if (ctx->cur_ret_type != TYPE_VOID) {
                    semanticError(stmt->lineno, ctx,
                                  "return with no value in non-void function");
                }
                return;
            }

            returned_type = analyzeExpression(stmt->firstChild, ctx);
            if (returned_type != ctx->cur_ret_type) {
                semanticError(stmt->lineno, ctx,
                              "return type mismatch: expected %s, got %s",
                              typeName(ctx->cur_ret_type), typeName(returned_type));
            }
            return;

        case AST_BLOCK:
            analyzeBlock(stmt, ctx);
            return;

        default:
            (void)analyzeExpression(stmt, ctx);
            return;
    }
}

static ExpType analyzeAssignmentTarget(AstNode *expr, SemanticContext *ctx) {
    Symbol *symbol;

    if (!expr) {
        return TYPE_ERROR;
    }

    if (expr->kind == AST_ARRAY_ACCESS) {
        return analyzeArrayAccess(expr, ctx);
    }

    if (expr->kind != AST_ID) {
        semanticError(expr->lineno, ctx,
                      "lhs of assignment must be a variable or array element");
        return TYPE_ERROR;
    }

    symbol = resolveSymbol(ctx->symtab, expr->name, currentScope);
    if (!symbol) {
        semanticError(expr->lineno, ctx,
                      "use of undeclared identifier '%s'", expr->name);
        return TYPE_ERROR;
    }

    registerSymbolUse(symbol, expr->lineno);

    if (symbol->kind != SYMBOL_VAR) {
        semanticError(expr->lineno, ctx,
                      "cannot assign to function '%s'", expr->name);
        return TYPE_ERROR;
    }

    if (symbol->dataType == TYPE_ARRAY) {
        semanticError(expr->lineno, ctx,
                      "cannot assign to array '%s' without index", expr->name);
        return TYPE_ERROR;
    }

    return TYPE_INT;
}

static ExpType analyzeArrayAccess(AstNode *expr, SemanticContext *ctx) {
    Symbol *symbol;
    AstNode *index_node;
    ExpType index_type;

    symbol = resolveSymbol(ctx->symtab, expr->name, currentScope);
    if (!symbol) {
        semanticError(expr->lineno, ctx,
                      "use of undeclared identifier '%s'", expr->name);
        return TYPE_ERROR;
    }

    registerSymbolUse(symbol, expr->lineno);

    if (symbol->kind != SYMBOL_VAR) {
        semanticError(expr->lineno, ctx, "'%s' is not a variable", expr->name);
        return TYPE_ERROR;
    }

    if (symbol->dataType != TYPE_ARRAY) {
        semanticError(expr->lineno, ctx, "'%s' is not an array", expr->name);
        return TYPE_ERROR;
    }

    index_node = expr->firstChild;
    if (!index_node) {
        semanticError(expr->lineno, ctx,
                      "array access '%s' is missing an index", expr->name);
        return TYPE_ERROR;
    }

    index_type = analyzeExpression(index_node, ctx);
    if (index_type != TYPE_INT) {
        semanticError(expr->lineno, ctx,
                      "array index for '%s' must be int", expr->name);
        return TYPE_ERROR;
    }

    return TYPE_INT;
}

static ExpType analyzeExpression(AstNode *expr, SemanticContext *ctx) {
    AstNode *left;
    AstNode *op;
    AstNode *right;
    AstNode *args;
    Symbol *symbol;
    int got;
    int want_count;

    if (!expr) {
        return TYPE_ERROR;
    }

    switch (expr->kind) {
        case AST_NUM:
            return TYPE_INT;

        case AST_ID:
            symbol = resolveSymbol(ctx->symtab, expr->name, currentScope);
            if (!symbol) {
                semanticError(expr->lineno, ctx,
                              "use of undeclared identifier '%s'", expr->name);
                return TYPE_ERROR;
            }

            registerSymbolUse(symbol, expr->lineno);

            if (symbol->kind != SYMBOL_VAR) {
                semanticError(expr->lineno, ctx,
                              "function '%s' used without call", expr->name);
                return TYPE_ERROR;
            }

            if (symbol->dataType == TYPE_ARRAY) {
                return TYPE_ARRAY;
            }
            if (symbol->dataType == TYPE_INT) {
                return TYPE_INT;
            }
            return TYPE_VOID;

        case AST_BINOP:
            left = expr->firstChild;
            op = left ? left->nextSibling : NULL;
            right = op ? op->nextSibling : NULL;
            if (!left || !op || op->kind != AST_OP || !right) {
                semanticError(expr->lineno, ctx, "malformed binary operator");
                return TYPE_ERROR;
            }

            if (analyzeExpression(left, ctx) != TYPE_INT ||
                analyzeExpression(right, ctx) != TYPE_INT) {
                semanticError(expr->lineno, ctx,
                              "non-int operand in binary op '%s'",
                              op->name ? op->name : "<op>");
            }
            return TYPE_INT;

        case AST_ASSIGN:
            left = expr->firstChild;
            right = left ? left->nextSibling : NULL;
            if (!left) {
                semanticError(expr->lineno, ctx, "assignment with no left-hand side");
                return TYPE_ERROR;
            }
            if (!right) {
                semanticError(expr->lineno, ctx, "assignment with no right-hand side");
                return TYPE_ERROR;
            }

            (void)analyzeAssignmentTarget(left, ctx);
            if (analyzeExpression(right, ctx) != TYPE_INT) {
                semanticError(expr->lineno, ctx, "rhs of assignment not int");
            }
            return TYPE_INT;

        case AST_CALL:
            symbol = getSymbol(ctx->symtab, expr->name, "global");
            if (!symbol) {
                semanticError(expr->lineno, ctx,
                              "call to undeclared function '%s'", expr->name);
                return TYPE_ERROR;
            }

            registerSymbolUse(symbol, expr->lineno);

            if (symbol->kind != SYMBOL_FUNC) {
                semanticError(expr->lineno, ctx,
                              "'%s' is not a function", expr->name);
                return TYPE_ERROR;
            }

            args = expr->firstChild;
            got = 0;
            for (AstNode *arg = args ? args->firstChild : NULL; arg;
                 arg = arg->nextSibling, ++got) {
                ExpType actual_type = analyzeExpression(arg, ctx);
                int expected_type = getParamType(ctx->symtab, expr->name, "global", got);

                if (expected_type != -1 && actual_type != expected_type) {
                    semanticError(expr->lineno, ctx,
                                  "arg %d to '%s' expects %s but got %s",
                                  got + 1, expr->name,
                                  typeName((ExpType)expected_type),
                                  typeName(actual_type));
                }
            }

            want_count = getParamCount(ctx->symtab, expr->name, "global");
            if (got != want_count) {
                semanticError(expr->lineno, ctx,
                              "function '%s' called with %d args; expected %d",
                              expr->name, got, want_count);
            }

            return (symbol->dataType == TYPE_INT) ? TYPE_INT : TYPE_VOID;

        case AST_ARRAY_ACCESS:
            return analyzeArrayAccess(expr, ctx);

        default:
            semanticError(expr->lineno, ctx,
                          "unhandled expression node kind %d", expr->kind);
            return TYPE_ERROR;
    }
}

static int statementGuaranteesReturn(const AstNode *stmt) {
    const AstNode *condition;
    const AstNode *then_stmt;
    const AstNode *else_stmt;

    if (!stmt) {
        return 0;
    }

    switch (stmt->kind) {
        case AST_RETURN:
            return 1;

        case AST_BLOCK:
            return blockGuaranteesReturn(stmt);

        case AST_IF:
            condition = stmt->firstChild;
            then_stmt = condition ? condition->nextSibling : NULL;
            else_stmt = then_stmt ? then_stmt->nextSibling : NULL;
            return then_stmt && else_stmt &&
                   statementGuaranteesReturn(then_stmt) &&
                   statementGuaranteesReturn(else_stmt);

        default:
            return 0;
    }
}

static int blockGuaranteesReturn(const AstNode *block) {
    if (!block) {
        return 0;
    }

    for (const AstNode *child = block->firstChild; child; child = child->nextSibling) {
        if (child->kind == AST_VAR_DECL) {
            continue;
        }

        if (statementGuaranteesReturn(child)) {
            return 1;
        }
    }

    return 0;
}
