// syntax_tree.h
#ifndef SYNTAX_TREE_H
#define SYNTAX_TREE_H

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/* AST node kinds */
typedef enum {
    AST_ARG_LIST,
    AST_PROGRAM,
    AST_VAR_DECL,
    AST_FUN_DECL,
    AST_PARAM,
    AST_PARAM_LIST,
    AST_PARAM_ARRAY,
    AST_BLOCK,
    AST_IF,
    AST_WHILE,
    AST_RETURN,
    AST_ASSIGN,
    AST_BINOP,
    AST_CALL,
    AST_ID,
    AST_NUM,
    AST_ARRAY_ACCESS
} AstNodeKind;

/* Generic AST node for an n-ary tree */
typedef struct AstNode {
    AstNodeKind kind;
    char       *name;         /* identifier name or NULL */
    int         value;        /* literal value for NUM or 0 */
    int         array_size;
    int         data_type;    /* TYPE_INT/TYPE_VOID when relevant */
    int         lineno;
    struct AstNode *firstChild;
    struct AstNode *nextSibling;
} AstNode;

/* Constructors */
AstNode *newNode(AstNodeKind kind);
AstNode *newIdNode(const char *name, int lineno);
AstNode *newNumNode(int value, int lineno);
AstNode *newOpNode(char *op, int lineno);

/* Build tree */
void addChild(AstNode *parent, AstNode *child);

/* Utilities */
void printAst(const AstNode *node, int indent);
void freeAst(AstNode *node);

#endif /* SYNTAX_TREE_H */
