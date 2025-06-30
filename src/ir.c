/* src/ir.c */
#include "ir.h"
#include "syntax_tree.h"   /* for AstNode definition */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/*── IR list management ───────────────────────────────────────────────────*/

/* Create an empty IR list */
IRList *ir_list_create(void) {
    IRList *list = malloc(sizeof(*list));
    if (!list) {
        fprintf(stderr, "[IR ERR] ir_list_create: malloc failed\n");
        exit(1);
    }
    list->head = list->tail = NULL;
    fprintf(stderr, "[IR DBG] ir_list_create → %p\n", (void*)list);
    return list;
}

/* Allocate a new IR instruction */
IR *ir_new(IrOp op, char *res, char *arg1, char *arg2) {
    IR *inst = malloc(sizeof(*inst));
    if (!inst) {
        fprintf(stderr, "[IR ERR] ir_new: malloc failed\n");
        exit(1);
    }
    inst->op   = op;
    inst->res  = res;
    inst->arg1 = arg1;
    inst->arg2 = arg2;
    inst->next = NULL;
    fprintf(stderr,
        "[IR DBG] ir_new: op=%d res=%s arg1=%s arg2=%s → %p\n",
        op,
        res  ? res  : "_",
        arg1 ? arg1 : "_",
        arg2 ? arg2 : "_",
        (void*)inst);
    return inst;
}

/* Append an instruction to the list */
void ir_append(IRList *list, IR *node) {
    if (!list) {
        fprintf(stderr, "[IR ERR] ir_append: list is NULL\n");
        return;
    }
    if (!node) {
        fprintf(stderr, "[IR ERR] ir_append: node is NULL\n");
        return;
    }
    fprintf(stderr,
        "[IR DBG] ir_append: list=%p head=%p tail=%p appending node=%p\n",
        (void*)list, (void*)list->head, (void*)list->tail, (void*)node);

    if (!list->head) {
        list->head = node;
    } else {
        list->tail->next = node;
    }
    list->tail = node;
}


static const char *op_name(IrOp op) {
    switch (op) {
        case IR_ADD:    return "add";
        case IR_SUB:    return "sub";
        case IR_MUL:    return "mul";
        case IR_DIV:    return "div";
        case IR_MOD:    return "mod";
        case IR_EQ:     return "eq";
        case IR_NEQ:    return "new";
        case IR_GT:     return "gt";
        case IR_LT:     return "lt";
        case IR_GTE:    return "gte";
        case IR_LTE:    return "lte";
        case IR_AND:    return "and";
        case IR_OR:     return "or";
        case IR_XOR:    return "xor";
        case IR_NOT:    return "not";
        case IR_MOV:    return "mov";
        case IR_LOAD:   return "load";
        case IR_STORE:  return "store";
        case IR_LABEL:  return "label";
        case IR_BR:     return "br";
        case IR_BRZ:    return "brz";
        case IR_CALL:   return "call";
        case IR_RET:    return "ret";
        default:        return "??";
    }
}

void dumpIR(IRList *list, FILE *out) {
    if (!list) return;
    fprintf(stderr, "[IR DBG] dumpIR: dumping %p\n", (void*)list);
    for (IR *i = list->head; i; i = i->next) {
        const char *mn = op_name(i->op);
        switch (i->op) {
            case IR_LABEL:
                fprintf(out, "%s:\n", i->res);
                break;
            case IR_RET:
                fprintf(out, "ret\n");
                break;
            case IR_BR:
                fprintf(out, "br %s\n", i->res);
                break;
            case IR_BRZ:
                fprintf(out, "brz %s, %s\n", i->res, i->arg1);
                break;
            case IR_LOAD:
                fprintf(out, "load %s, [%s]\n", i->res, i->arg1);
                break;
            case IR_STORE:
                fprintf(out, "store [%s], %s\n", i->res, i->arg1);
                break;
            case IR_CALL:
                fprintf(out, "call %s\n", i->res);
                break;
            default:
                // all other 3-operand ops: op res, arg1, arg2
                fprintf(out, "%s %s, %s, %s\n",
                        mn,
                        i->res  ? i->res  : "_",
                        i->arg1 ? i->arg1 : "_",
                        i->arg2 ? i->arg2 : "_");
        }
    }
}

/* Free the entire IR list */
void freeIR(IRList *list) {
    if (!list) return;
    fprintf(stderr, "[IR DBG] freeIR: freeing list %p\n", (void*)list);
    IR *cur = list->head;
    while (cur) {
        IR *n = cur->next;
        free(cur->res);
        free(cur->arg1);
        free(cur->arg2);
        free(cur);
        cur = n;
    }
    free(list);
}

/*── Temporary & label generators ─────────────────────────────────────────*/

static int temp_count  = 0;
static int label_count = 0;

/* Map function parameters to temps */
typedef struct ParamMap {
    char *name;
    char *temp;
    struct ParamMap *next;
} ParamMap;

static ParamMap *param_add(ParamMap *head, const char *name, char *temp) {
    ParamMap *n = malloc(sizeof(*n));
    n->name = strdup(name);
    n->temp = temp;
    n->next = head;
    return n;
}

static char *param_lookup(ParamMap *head, const char *name) {
    for (ParamMap *p = head; p; p = p->next)
        if (strcmp(p->name, name) == 0)
            return p->temp;
    return NULL;
}

static void param_free(ParamMap *head) {
    while (head) {
        ParamMap *n = head->next;
        free(head->name);
        free(head);
        head = n;
    }
}

/* Returns a fresh temp name "t0", "t1", ... */
char *new_temp(void) {
    char buf[16];
    snprintf(buf, sizeof(buf), "t%d", temp_count++);
    return strdup(buf);
}

/* Returns a fresh label "L0", "L1", ... */
char *new_label(void) {
    char buf[16];
    snprintf(buf, sizeof(buf), "L%d", label_count++);
    return strdup(buf);
}

/*── Forward declarations of lowering helpers ────────────────────────────*/
static void      gen_function(AstNode *funcDecl, IRList *ir);
static void      gen_stmt    (AstNode *stmt,     IRList *ir, ParamMap *params);
static char     *gen_expr    (AstNode *expr,     IRList *ir, ParamMap *params);

/*── Top‐level IR generation ───────────────────────────────────────────────*/

/* Walk the AST_PROGRAM and lower each function */
IRList *generateIR(AstNode *root) {
    if (!root) {
        fprintf(stderr, "[IR ERR] generateIR: root is NULL\n");
        return NULL;
    }
    fprintf(stderr,
        "[IR DBG] generateIR: root=%p firstChild=%p\n",
        (void*)root, (void*)root->firstChild);

    IRList *ir = ir_list_create();
    for (AstNode *decl = root->firstChild; decl; decl = decl->nextSibling) {
        fprintf(stderr,
            "[IR DBG] generateIR: decl kind=%d at %p\n",
            decl->kind, (void*)decl);
        if (decl->kind == AST_FUN_DECL) {
            fprintf(stderr,
                "[IR DBG]   lowering function '%s'\n",
                decl->name);
            gen_function(decl, ir);
        }
    }
    
    FILE *out = fopen("ir_dump.txt", "w");
    if (!out) {
        fprintf(stderr, "[IR ERR] generateIR: failed to open ir_dump.txt\n");
        return NULL;
    }
    dumpIR(ir, out);
    fclose(out);
    return ir;
}

/*── Function lowering ───────────────────────────────────────────────────*/

static ParamMap *create_param_map(AstNode *paramList, IRList *ir) {
    ParamMap *map = NULL;
    int idx = 0;
    for (AstNode *p = paramList->firstChild; p; p = p->nextSibling, ++idx) {
        char *t = new_temp();
        char reg[16];
        sprintf(reg, "arg%d", idx);
        ir_append(ir, ir_new(IR_MOV, strdup(t), strdup(reg), NULL));
        map = param_add(map, p->name, t);
    }
    return map;
}

static void gen_function(AstNode *funcDecl, IRList *ir) {
    /* Emit entry label */
    ir_append(ir,
        ir_new(IR_LABEL, strdup(funcDecl->name), NULL, NULL));
    
    ParamMap *params = NULL;

    /* Skip past parameter list if present */
    AstNode *child = funcDecl->firstChild;
    if (child && child->kind == AST_PARAM_LIST) {
        params = create_param_map(child, ir);
        child = child->nextSibling;
    }
    /* Lower the function body */
    gen_stmt(child, ir, params);

    /* Ensure a RET at end if none emitted */
    if (!ir->tail || ir->tail->op != IR_RET) {
        ir_append(ir,
            ir_new(IR_RET, NULL, NULL, NULL));
    }

    param_free(params);
}

/*── Statement lowering ──────────────────────────────────────────────────*/

static void gen_stmt(AstNode *stmt, IRList *ir, ParamMap *params) {
    if (!stmt) {
        fprintf(stderr, "[IR ERR] gen_stmt: stmt is NULL\n");
        return;
    }
    fprintf(stderr,
        "[IR DBG] gen_stmt: kind=%d at %p\n",
        stmt->kind, (void*)stmt);

    switch (stmt->kind) {
        case AST_VAR_DECL:
        case AST_PARAM:
        case AST_PARAM_LIST:
        case AST_PARAM_ARRAY:
        case AST_PROGRAM:
        case AST_FUN_DECL:
        case AST_ARG_LIST:
            return; /* nothing to emit for declarations */
        case AST_RETURN: {
            AstNode *expr = stmt->firstChild;
            if (expr && expr->kind == AST_NUM) {
                char buf[32];
                snprintf(buf, sizeof(buf), "%d", expr->value);
                ir_append(ir,
                    ir_new(IR_MOV, strdup("retval"), strdup(buf), NULL));
            } else if (expr && expr->kind == AST_ID) {
                char *tmp = param_lookup(params, expr->name);
                if (tmp) {
                    ir_append(ir,
                        ir_new(IR_MOV, strdup("retval"), strdup(tmp), NULL));
                } else {
                    ir_append(ir,
                        ir_new(IR_LOAD, strdup("retval"), strdup(expr->name), NULL));
                }
            } else if (expr) {
                char *val = gen_expr(expr, ir, params);
                ir_append(ir,
                    ir_new(IR_MOV, strdup("retval"), strdup(val), NULL));
            }
            ir_append(ir,
                ir_new(IR_RET, NULL, NULL, NULL));
            break;
        }

        case AST_IF: {
            AstNode *condNode = stmt->firstChild;
            AstNode *thenNode = condNode->nextSibling;
            AstNode *elseNode = thenNode->nextSibling;

            char *cond    = gen_expr(condNode, ir, params);
            char *elseLbl = new_label();
            char *endLbl  = new_label();

            fprintf(stderr,
                "[IR DBG]   IF cond=%s elseLbl=%s endLbl=%s\n",
                strdup(cond), strdup(elseLbl), strdup(endLbl));

            /* if zero → else */
            ir_append(ir,
                ir_new(IR_BRZ, strdup(elseLbl), strdup(cond), NULL));

            /* then‐branch */
            gen_stmt(thenNode, ir, params);

            bool thenRet = ir->tail && ir->tail->op == IR_RET;

            /* jump past else */
            if (!thenRet) {
                ir_append(ir,
                    ir_new(IR_BR, strdup(endLbl), NULL, NULL));
            }

            /* else label */
            ir_append(ir,
                ir_new(IR_LABEL, strdup(elseLbl), NULL, NULL));
            
            if (elseNode) {
                gen_stmt(elseNode, ir, params);
            }

            bool elseRet = elseNode && ir->tail && ir->tail->op == IR_RET;

            /* end label */
            if (!thenRet || (elseNode && !elseRet)) {
                ir_append(ir,
                    ir_new(IR_LABEL, strdup(endLbl), NULL, NULL));
            }
            
            break;
        }

        case AST_WHILE: {
            AstNode *condNode = stmt->firstChild;
            AstNode *bodyNode = condNode->nextSibling;

            char *startLbl = new_label();
            char *endLbl   = new_label();
            fprintf(stderr,
                "[IR DBG]   WHILE start=%s end=%s\n",
                strdup(startLbl), strdup(endLbl));

            /* start label */
            ir_append(ir,
                ir_new(IR_LABEL, strdup(startLbl), NULL, NULL));

            /* condition */
            char *cond = gen_expr(condNode, ir, params);
            ir_append(ir,
                ir_new(IR_BRZ, strdup(endLbl), strdup(cond), NULL));

            /* body */
            gen_stmt(bodyNode, ir, params);

            bool bodyRet = ir->tail && ir->tail->op == IR_RET;

            /* back to start */
            if (!bodyRet) {
                ir_append(ir,
                    ir_new(IR_BR, strdup(startLbl), NULL, NULL));
            }

            /* end label */
            ir_append(ir,
                ir_new(IR_LABEL, strdup(endLbl), NULL, NULL));
            break;
        }

        case AST_BLOCK: {
            for (AstNode *c = stmt->firstChild; c; c = c->nextSibling) {
                gen_stmt(c, ir, params);
            }
            break;
        }

        default: {
            /* expression‐statement */
            fprintf(stderr,
                "[IR DBG]   expr-stmt dispatch at %p\n",
                (void*)stmt);
            gen_expr(stmt, ir, params);
            break;
        }
    }
}

/*── Expression lowering ─────────────────────────────────────────────────*/

static char *gen_expr(AstNode *expr, IRList *ir, ParamMap *params) {
    if (!expr) {
        fprintf(stderr, "[IR ERR] gen_expr: expr is NULL\n");
        return NULL;
    }
    fprintf(stderr,
        "[IR DBG] gen_expr: kind=%d at %p\n",
        expr->kind, (void*)expr);

    char buf[32];

    switch (expr->kind) {

    case AST_NUM: {
        snprintf(buf, sizeof(buf), "%d", expr->value);
        char *imm = strdup(buf);
        char *t   = new_temp();
        ir_append(ir, ir_new(IR_MOV, t, imm, NULL));
        return t;
    }

    case AST_ID: {
        char *tmp = param_lookup(params, expr->name);
        if (tmp) {
            return strdup(tmp);
        }
        char *t = new_temp();
        ir_append(ir, ir_new(IR_LOAD, strdup(t), strdup(expr->name), NULL));
        return t;
    }

    case AST_ASSIGN: {
        AstNode *lhs = expr->firstChild;
        AstNode *rhs = lhs->nextSibling;
        char *r = gen_expr(rhs, ir, params);
        char *var = lhs->name ? lhs->name : NULL;
        char *dest = param_lookup(params, var);
        if (dest) {
            ir_append(ir, ir_new(IR_MOV, strdup(dest), strdup(r), NULL));
        } else {
            ir_append(ir, ir_new(IR_STORE, strdup(var), strdup(r), NULL));
        }
        return r;
    }

    case AST_BINOP: {
        AstNode *left  = expr->firstChild;
        AstNode *op    = left->nextSibling;
        AstNode *right = op->nextSibling;

        char *l = gen_expr(left,  ir, params);
        char *r = gen_expr(right, ir, params);
        char *t = new_temp();

        IrOp opc;
        if      (strcmp(op->name, "+")==0) opc = IR_ADD;
        else if (strcmp(op->name, "-")==0) opc = IR_SUB;
        else if (strcmp(op->name, "*")==0) opc = IR_MUL;
        else if (strcmp(op->name, "/")==0) opc = IR_DIV;
        if      (strcmp(op->name, "==")==0) opc = IR_EQ;
        else if (strcmp(op->name, "!=")==0) opc = IR_NEQ;
        else if (strcmp(op->name, ">")==0) opc = IR_GT;
        else if (strcmp(op->name, "<")==0) opc = IR_LT;
        else if (strcmp(op->name, ">=")==0) opc = IR_GTE;
        else if (strcmp(op->name, "<=")==0) opc = IR_LTE;
        else if (strcmp(op->name, '%')==0) opc = IR_MOD;
        else                                opc = IR_ADD;

        ir_append(ir, ir_new(opc, strdup(t), strdup(l), strdup(r)));
        return strdup(t);
    }

    case AST_CALL: {
        int idx = 0;
        AstNode *argList = expr->firstChild;
        for (
            AstNode *arg = argList ? argList->firstChild : NULL;
            arg;
            arg = arg->nextSibling, ++idx
        ) {            
            char *val = gen_expr(arg, ir, params);
            char reg[16];
            sprintf(reg, "arg%d", idx);
            ir_append(ir, ir_new(IR_MOV, strdup(reg), strdup(val), NULL));
        }
        ir_append(ir, ir_new(IR_CALL, strdup(expr->name), NULL, NULL));
        char *t = new_temp();
        ir_append(ir, ir_new(IR_MOV, t, strdup("retval"), NULL));
        return t;
    }

    case AST_ARG_LIST:
        /* Argument lists are handled in the CALL case */
        return NULL;

    default:
        fprintf(stderr,
            "[IR ERR] gen_expr: unhandled kind=%d\n",
            expr->kind);
        return NULL;
    }
}
