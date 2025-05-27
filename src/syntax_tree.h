// syntax_tree.h
#ifndef SYNTAX_TREE_H
#define SYNTAX_TREE_H

#include <stdlib.h>

/* AST node kinds */
typedef enum {
    AST_PROGRAM,
    AST_VAR_DECL,
    AST_FUN_DECL,
    AST_PARAM,
    AST_PARAM_ARRAY,
    AST_BLOCK,
    AST_IF,
    AST_WHILE,
    AST_RETURN,
    AST_ASSIGN,
    AST_BINOP,
    AST_CALL,
    AST_ID,
    AST_NUM
} AstNodeKind;

/* Generic AST node for an n-ary tree */
typedef struct AstNode {
    AstNodeKind kind;
    char       *name;         /* identifier name or NULL */
    int         value;        /* literal value for NUM or 0 */
    struct AstNode *firstChild;
    struct AstNode *nextSibling;
} AstNode;

/* Constructors */
AstNode *newNode(AstNodeKind kind);
AstNode *newIdNode(const char *name);
AstNode *newNumNode(int value);
AstNode *newOpNode(int op);

/* Build tree */
void addChild(AstNode *parent, AstNode *child);

/* Utilities */
void printAst(const AstNode *node, int indent);
void freeAst(AstNode *node);

#endif /* SYNTAX_TREE_H */