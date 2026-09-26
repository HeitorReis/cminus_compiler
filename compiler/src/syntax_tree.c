// syntax_tree.c
#include <stdlib.h>    /* for malloc, free */
#include <string.h>    /* for strdup */
#include "syntax_tree.h"
#include <stdio.h>

static const char *kindName(AstNodeKind k) {
    switch(k) {
        case AST_PROGRAM:               return "AST_PROGRAM";
        case AST_VAR_DECL:              return "AST_VAR_DECL";
        case AST_FUN_DECL:              return "AST_FUN_DECL";
        case AST_PARAM:                 return "AST_PARAM";
        case AST_PARAM_LIST:            return "AST_PARAM_LIST";
        case AST_PARAM_ARRAY:           return "AST_PARAM_ARRAY";
        case AST_ARG_LIST:              return "AST_ARG_LIST";
        case AST_BLOCK:                 return "AST_BLOCK";
        case AST_IF:                    return "AST_IF";
        case AST_WHILE:                 return "AST_WHILE";
        case AST_RETURN:                return "AST_RETURN";
        case AST_ASSIGN:                return "AST_ASSIGN";
        case AST_BINOP:                 return "AST_BINOP";
        case AST_OP:                    return "AST_OP";
        case AST_CALL:                  return "AST_CALL";
        case AST_ID:                    return "AST_ID";
        case AST_NUM:                   return "AST_NUM";
        case AST_ARRAY_ACCESS:          return "AST_ARRAY_ACCESS";
        default:                        return "UNKNOWN";
        }
    }

/* Create a blank node */
AstNode *newNode(AstNodeKind kind) {
    AstNode *n = malloc(sizeof(*n));
    n->kind        = kind;
    n->name        = NULL;
    n->value       = 0;
    n->array_size  = 0;
    n->data_type   = 0;
    n->lineno      = 0;  // default line number, can be set later
    n->firstChild  = NULL;
    n->nextSibling = NULL;
    printf("[AST DBG] newNode kind=%s -> %p\n", kindName(kind), (void*)n);
    return n;
}

/* Identifier node */
AstNode *newIdNode(const char *name, int lineno) {
    AstNode *n = newNode(AST_ID);
    n->name = strdup(name);
    n->lineno = lineno;
    printf("[AST DBG] newIdNode(\"%s\") -> %p\n", name, (void*)n);
    return n;
}

/* Numeric literal node */
AstNode *newNumNode(int value, int lineno) {
    AstNode *n = newNode(AST_NUM);
    n->value = value;
    n->lineno = lineno;
    printf("[AST DBG] newNumNode(%d) -> %p\n", value, (void*)n);
    return n;
}

AstNode *newOpNode(const char *op, int lineno) {
    AstNode *n = newNode(AST_OP);
    n->lineno = lineno;
    n->name = strdup(op);
    return n;
}

/* Attach child as last sibling */
void addChild(AstNode *parent, AstNode *child) {
    if (!parent || !child) return;
    if (!parent->firstChild) {
        parent->firstChild = child;
    } else {
        AstNode *s = parent->firstChild;
        while (s->nextSibling) s = s->nextSibling;
        s->nextSibling = child;
    }
    printf(
        "[AST DBG] addChild parent=%p(%s, lineno=%d) child=%p(%s, lineno=%d)\n",
        (void*)parent, kindName(parent->kind), parent->lineno,
        (void*)child, kindName(child->kind), child->lineno
    );
}

/* Indented printing for debugging */
void printAstToStream(FILE *out, const AstNode *node, int indent) {
    if (!node) return;
    if (!out) return;
    for (int i = 0; i < indent; i++) fputc(' ', out);
    switch (node->kind) {
        case AST_ARG_LIST:      fprintf(out, "ArgList (lineno=%d)\n", node->lineno); break;
        case AST_PROGRAM:       fprintf(out, "Program (lineno=%d)\n", node->lineno); break;
        case AST_VAR_DECL:      fprintf(out, "VarDecl(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_FUN_DECL:      fprintf(out, "FunDecl(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_PARAM:         fprintf(out, "Param(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_PARAM_LIST:    fprintf(out, "ParamList (lineno=%d)\n", node->lineno); break;
        case AST_PARAM_ARRAY:   fprintf(out, "ParamArray(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_BLOCK:         fprintf(out, "Block (lineno=%d)\n", node->lineno); break;
        case AST_IF:            fprintf(out, "If (lineno=%d)\n", node->lineno); break;
        case AST_WHILE:         fprintf(out, "While (lineno=%d)\n", node->lineno); break;
        case AST_RETURN:        fprintf(out, "Return (lineno=%d)\n", node->lineno); break;
        case AST_ASSIGN:        fprintf(out, "Assign (lineno=%d)\n", node->lineno); break;
        case AST_BINOP:
            if (node->name)
                fprintf(out, "BinOp(op='%s', lineno=%d)\n", node->name, node->lineno);
            else
                fprintf(out, "BinOp (lineno=%d)\n", node->lineno);
            break;
        case AST_OP:
            fprintf(out, "Op(op='%s', lineno=%d)\n", node->name ? node->name : "<null>", node->lineno);
            break;
        case AST_CALL:          fprintf(out, "Call(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_ID:            fprintf(out, "Id(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_NUM:           fprintf(out, "Num(value=%d, lineno=%d)\n", node->value, node->lineno); break;
        case AST_ARRAY_ACCESS:  fprintf(out, "ArrayAccess(name=%s, lineno=%d)\n", node->name, node->lineno); break;
    }
    /* children */
    for (AstNode *c = node->firstChild; c; c = c->nextSibling)
        printAstToStream(out, c, indent + 2);
}

void printAst(const AstNode *node, int indent) {
    printAstToStream(stdout, node, indent);
}

/* Recursively free the tree */
void freeAst(AstNode *node) {
    if (!node) return;
    /* free children */
    AstNode *c = node->firstChild;
    while (c) {
        AstNode *next = c->nextSibling;
        freeAst(c);
        c = next;
    }
    /* free own data */
    if (node->name) free(node->name);
    free(node);
}

