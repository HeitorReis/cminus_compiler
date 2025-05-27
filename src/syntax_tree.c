// syntax_tree.c
#include "syntax_tree.h"
#include <stdio.h>
#include <string.h>

/* Create a blank node */
AstNode *newNode(AstNodeKind kind) {
    AstNode *n = malloc(sizeof(*n));
    n->kind        = kind;
    n->name        = NULL;
    n->value       = 0;
    n->firstChild  = NULL;
    n->nextSibling = NULL;
    return n;
}

/* Identifier node */
AstNode *newIdNode(const char *name) {
    AstNode *n = newNode(AST_ID);
    n->name = strdup(name);
    return n;
}

/* Numeric literal node */
AstNode *newNumNode(int value) {
    AstNode *n = newNode(AST_NUM);
    n->value = value;
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
}

/* Indented printing for debugging */
void printAst(const AstNode *node, int indent) {
    if (!node) return;
    for (int i = 0; i < indent; i++) putchar(' ');
    switch (node->kind) {
        case AST_PROGRAM:       printf("Program\n"); break;
        case AST_VAR_DECL:      printf("VarDecl(name=%s)\n", node->name); break;
        case AST_FUN_DECL:      printf("FunDecl(name=%s)\n", node->name); break;
        case AST_PARAM:         printf("Param(name=%s)\n", node->name); break;
        case AST_PARAM_ARRAY:   printf("ParamArray(name=%s)\n", node->name); break;
        case AST_BLOCK:         printf("Block\n"); break;
        case AST_IF:            printf("If\n"); break;
        case AST_WHILE:         printf("While\n"); break;
        case AST_RETURN:        printf("Return\n"); break;
        case AST_ASSIGN:        printf("Assign\n"); break;
        case AST_BINOP:         printf("BinOp\n"); break;
        case AST_CALL:          printf("Call(name=%s)\n", node->name); break;
        case AST_ID:            printf("Id(name=%s)\n", node->name); break;
        case AST_NUM:           printf("Num(value=%d)\n", node->value); break;
    }
    /* children */
    for (AstNode *c = node->firstChild; c; c = c->nextSibling)
        printAst(c, indent + 2);
}

/* Recursively free the tree */
void freeAst(AstNode *node) {
    if (!node) return;
    /* free children */
    AstNode *c = node->firstChild;
    while (c) {
        AstNode *next = c->nextSibling;
        if (node->name) free(node->name);
        freeAst(c);
        c = next;
    }
    /* free own data */
    if (node->kind == AST_ID && node->name) free(node->name);
    free(node);
}

AstNode *newOpNode(char *op) {
    AstNode *n = newNode(AST_BINOP);  // or AST_BINOP_KIND if you had separate kinds
    n->name = strdup(op);                    // store the token code (e.g. PLUS, LTE, etc.)
    return n;
}