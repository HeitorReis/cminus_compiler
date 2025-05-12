#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "parser.tab.h"
#include "node.h"
#include "syntax_tree.h"

extern char *yytext;
extern int tokenNUM;

// Variáveis auxiliares...
char *expName;
char *variableName;
char *functionName;
char *currentToken;
char *currentScope = "global";
char *argName;

int currentLine = 1;
int functionCurrentLine = 1;
int argsCount = 0;
int paramsCount = 0;

treeNode *createNode() {
    treeNode *newNode = (treeNode*) malloc(sizeof(treeNode));
    for (int i = 0; i < CHILD_MAX_NODES; i++) {
        newNode->child[i] = NULL;
    }
    newNode->sibling = NULL;
    newNode->line = currentLine;
    newNode->scope = currentScope;
    return newNode;
}

treeNode *createDeclNode(declType node) {
    treeNode *newNode = createNode();
    newNode->node = decl;
    newNode->nodeSubType.decl = node;
    return newNode;
}

treeNode *createStmtNode(stmtType node) {
    treeNode *newNode = createNode();
    newNode->node = stmt;
    newNode->nodeSubType.stmt = node;
    return newNode;
}

treeNode *createExpNode(expType node) {
    treeNode *newNode = createNode();
    newNode->node = exp;
    newNode->nodeSubType.exp = node;
    return newNode;
}

treeNode *traversal(treeNode *node1, treeNode *node2) {
    treeNode *temp = node1;
    if (temp != NULL) {
        while (temp->sibling != NULL) {
            temp = temp->sibling;
        }
        temp->sibling = node2;
        return node1;
    } else {
        return node2;
    }
}

treeNode *createDeclVarNode(declType declVar, treeNode *expType) {
    treeNode *declVarNode = createDeclNode(declVar);
    declVarNode->key.name = expName;
    declVarNode->type = expType->type;
    expType->child[0] = declVarNode;
    return expType;
}

treeNode *createArrayDeclVarNode(expType expNum, declType declVar, treeNode *expType) {
    treeNode *expNumNode = createExpNode(expNum);
    expNumNode->key.value = tokenNUM;  
    expNumNode->type = Integer;

    treeNode *declVarNode = createDeclNode(declVar);
    declVarNode->key.name = expName; 
    declVarNode->child[0] = expNumNode;

    declVarNode->type = (expType->type == Integer) ? Array : Void;
    expType->child[0] = declVarNode;
    return expType;
}

treeNode *createDeclFuncNode(declType declFunc, treeNode *expType, treeNode *params, treeNode *blocDecl) {
    treeNode* declFuncNode = createDeclNode(declFunc);
    declFuncNode->child[0] = params;
    declFuncNode->child[1] = blocDecl;
    declFuncNode->key.name = functionName;
    declFuncNode->line = functionCurrentLine;
    declFuncNode->type = expType->type;
    declFuncNode->params = paramsCount;
    expType->child[0] = declFuncNode;
    return expType;
}

treeNode *createEmptyParams(expType expId) {
    treeNode *node = createExpNode(expId);
    node->key.name = "void";
    node->type = Void;
    return node;
}

treeNode *createArrayArg(declType declVar, treeNode *expType) {
    treeNode *declVarNode = createDeclNode(declVar);
    declVarNode->key.name = expName;
    declVarNode->type = (expType->type == Integer) ? Array : expType->type;
    expType->child[0] = declVarNode;
    return expType;
}

treeNode *createIfStmt(stmtType stmtIf, treeNode *exp, treeNode *stmt1, treeNode *stmt2) {
    treeNode *stmtIfNode = createStmtNode(stmtIf);
    stmtIfNode->child[0] = exp;
    stmtIfNode->child[1] = stmt1;
    if (stmt2 != NULL) stmtIfNode->child[2] = stmt2;
    return stmtIfNode;
}

treeNode *createWhileStmt(stmtType stmtWhile, treeNode *exp, treeNode *stmt) {
    treeNode *stmtWhileNode = createStmtNode(stmtWhile);
    stmtWhileNode->child[0] = exp;
    stmtWhileNode->child[1] = stmt;
    stmtWhileNode->type = Boolean;
    return stmtWhileNode;
}

treeNode *createAssignStmt(stmtType stmtAttrib, treeNode *var, treeNode *exp) {
    treeNode *stmtAttribNode = createStmtNode(stmtAttrib);
    stmtAttribNode->child[0] = var;
    stmtAttribNode->child[1] = exp;
    stmtAttribNode->type = Integer;
    return stmtAttribNode;
}

treeNode *createExpVar(expType expId) {
    treeNode *expVarNode = createExpNode(expId);
    expVarNode->key.name = expName;
    expVarNode->type = Void;
    return expVarNode;
}

treeNode *createArrayExpVar(expType expId, treeNode *exp) {
    treeNode *expVarNode = createExpNode(expId);
    expVarNode->key.name = variableName;
    expVarNode->child[0] = exp;
    expVarNode->type = Integer;
    return expVarNode;
}

treeNode *createExpOp(expType expOp, treeNode *exp1, treeNode *exp2) {
    treeNode *expOpNode = createExpNode(expOp);
    expOpNode->child[0] = exp1;
    expOpNode->child[1] = exp2;
    return expOpNode;
}

treeNode *createExpNum(expType expNum) {
    treeNode *expNumNode = createExpNode(expNum);
    expNumNode->key.value = atoi(yytext);   
    expNumNode->type = Integer;
    return expNumNode;
}

treeNode *createActivationFunc(stmtType stmtFunc, treeNode *arguments) {
    treeNode *activationFuncNode = createStmtNode(stmtFunc);
    activationFuncNode->child[1] = arguments; 
    activationFuncNode->key.name = functionName;
    activationFuncNode->line = functionCurrentLine;
    activationFuncNode->args = argsCount;
    return activationFuncNode;
}

/* === Novo construtor para chamada em expressão === */
treeNode *createExpCallNode(const char *funcName, treeNode *args) {
    treeNode *node = createExpNode(expCall);
    node->key.name = strdup(funcName);
    node->child[0] = args;  /* lista de argumentos */
    node->type = Void;      /* será ajustado na semântica */
    return node;
}
