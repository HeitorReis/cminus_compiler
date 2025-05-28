// syntax_tree.c
#include <stdlib.h>    /* for malloc, free */
#include <string.h>    /* for strdup */
#include "syntax_tree.h"
#include <stdio.h>

static const char *kindName(AstNodeKind k) {
    switch(k) {
        case AST_PROGRAM:      return "AST_PROGRAM";
        case AST_VAR_DECL:     return "AST_VAR_DECL";
        case AST_FUN_DECL:     return "AST_FUN_DECL";
        case AST_PARAM:        return "AST_PARAM";
        case AST_PARAM_LIST:   return "AST_PARAM_LIST";
        case AST_PARAM_ARRAY:  return "AST_PARAM_ARRAY";
        case AST_ARG_LIST:     return "AST_ARG_LIST";
        case AST_BLOCK:        return "AST_BLOCK";
        case AST_IF:           return "AST_IF";
        case AST_WHILE:        return "AST_WHILE";
        case AST_RETURN:       return "AST_RETURN";
        case AST_ASSIGN:       return "AST_ASSIGN";
        case AST_BINOP:        return "AST_BINOP";
        case AST_CALL:         return "AST_CALL";
        case AST_ID:           return "AST_ID";
        case AST_NUM:          return "AST_NUM";
        default:               return "UNKNOWN";
        }
    }

/* Create a blank node */
AstNode *newNode(AstNodeKind kind) {
    AstNode *n = malloc(sizeof(*n));
    n->kind        = kind;
    n->name        = NULL;
    n->value       = 0;
    n->firstChild  = NULL;
    n->nextSibling = NULL;
    printf("[AST DBG] newNode kind=%s -> %p\n", kindName(kind), (void*)n);
    return n;
}

/* Identifier node */
AstNode *newIdNode(const char *name) {
    AstNode *n = newNode(AST_ID);
    n->name = strdup(name);
    printf("[AST DBG] newIdNode(\"%s\") -> %p\n", name, (void*)n);
    return n;
}

/* Numeric literal node */
AstNode *newNumNode(int value) {
    AstNode *n = newNode(AST_NUM);
    n->value = value;
    printf("[AST DBG] newNumNode(%d) -> %p\n", value, (void*)n);
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
        "[AST DBG] addChild parent=%p(%s) child=%p(%s)\n",
        (void*)parent, kindName(parent->kind),
        (void*)child, kindName(child->kind)
    );
}

/* Indented printing for debugging */
void printAst(const AstNode *node, int indent) {
    if (!node) return;
    for (int i = 0; i < indent; i++) putchar(' ');
    switch (node->kind) {
        case AST_ARG_LIST:      printf("ArgList\n"); break;
        case AST_PROGRAM:       printf("Program\n"); break;
        case AST_VAR_DECL:      printf("VarDecl(name=%s)\n", node->name); break;
        case AST_FUN_DECL:      printf("FunDecl(name=%s)\n", node->name); break;
        case AST_PARAM:         printf("Param(name=%s)\n", node->name); break;
        case AST_PARAM_LIST:    printf("ParamList\n"); break;
        case AST_PARAM_ARRAY:   printf("ParamArray(name=%s)\n", node->name); break;
        case AST_BLOCK:         printf("Block\n"); break;
        case AST_IF:            printf("If\n"); break;
        case AST_WHILE:         printf("While\n"); break;
        case AST_RETURN:        printf("Return\n"); break;
        case AST_ASSIGN:        printf("Assign\n"); break;
        case AST_BINOP:         
            if (node->name)
                printf("BinOp(op='%s')\n", node->name);
            else
                printf("BinOp\n");
            break;
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
