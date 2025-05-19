#ifndef NODE_H
#define NODE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHILD_MAX_NODES 3

typedef enum { decl, exp, stmt } nodeType;
typedef enum { declFunc, declVar, declIdType } declType;
/* Adiciona expCall para representar chamada de função em expressões */
typedef enum { expId, expNum, expOp, expCall } expType;
typedef enum { stmtAttrib, stmtFunc, stmtIf, stmtReturn, stmtWhile } stmtType;
typedef enum { Array, Boolean, Integer, Void } primitiveType;
typedef struct treeNode {
    struct treeNode *child[CHILD_MAX_NODES];
    struct treeNode *sibling;

    char          *scope;
    int            line;
    int            params;
    int            args;
    nodeType       node;
    primitiveType  type;

    declType       declSubType;
    expType        expSubType;
    stmtType       stmtSubType;

    char          *name;
    int            value;
    int            op;
} treeNode;

extern treeNode *syntaxTree;

/* Protótipos existentes */
void printSyntaxTree(treeNode *tree);
void printTreeNode(treeNode *tree);
treeNode *parse();

/* Novo construtor para chamada de função em expressões */
treeNode *createExpCallNode(const char *funcName, treeNode *args);

#endif
