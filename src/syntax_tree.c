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

AstNode *newOpNode(char *op, int lineno) {
    AstNode *n = newNode(AST_BINOP);  // or AST_BINOP_KIND if you had separate kinds
    n->lineno = lineno;
    n->name = strdup(op);                    // store the token code (e.g. PLUS, LTE, etc.)
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
void printAst(const AstNode *node, int indent) {
    if (!node) return;
    for (int i = 0; i < indent; i++) putchar(' ');
    switch (node->kind) {
        case AST_ARG_LIST:      printf("ArgList (lineno=%d)\n", node->lineno); break;
        case AST_PROGRAM:       printf("Program (lineno=%d)\n", node->lineno); break;
        case AST_VAR_DECL:      printf("VarDecl(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_FUN_DECL:      printf("FunDecl(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_PARAM:         printf("Param(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_PARAM_LIST:    printf("ParamList (lineno=%d)\n", node->lineno); break;
        case AST_PARAM_ARRAY:   printf("ParamArray(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_BLOCK:         printf("Block (lineno=%d)\n", node->lineno); break;
        case AST_IF:            printf("If (lineno=%d)\n", node->lineno); break;
        case AST_WHILE:         printf("While (lineno=%d)\n", node->lineno); break;
        case AST_RETURN:        printf("Return (lineno=%d)\n", node->lineno); break;
        case AST_ASSIGN:        printf("Assign (lineno=%d)\n", node->lineno); break;
        case AST_BINOP:         
            if (node->name)
                printf("BinOp(op='%s', lineno=%d)\n", node->name, node->lineno);
            else
                printf("BinOp (lineno=%d)\n", node->lineno);
            break;
        case AST_CALL:          printf("Call(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_ID:            printf("Id(name=%s, lineno=%d)\n", node->name, node->lineno); break;
        case AST_NUM:           printf("Num(value=%d, lineno=%d)\n", node->value, node->lineno); break;
        case AST_ARRAY_ACCESS:  printf("ArrayAccess(name=%s, lineno=%d)\n", node->name, node->lineno); break;
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
    if (node->name) free(node->name);
    free(node);
}

