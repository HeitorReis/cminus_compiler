#ifndef SYNTAX_TREE_H
#define SYNTAX_TREE_H

#include "node.h"

#define YYPARSER
#define YYSTYPE treeNode*

extern char *expName;
extern char *variableName;
extern char *functionName;
extern char *currentToken;

extern int currentLine;
extern int functionCurrentLine;
extern int argsCount;
extern int paramsCount;

extern char *argName;

int yylex();
int yyerror(char *errorMsg);

// Funções para manipulação de nós
treeNode *createDeclNode(declType node);
treeNode *createExpNode(expType node);
treeNode *createStmtNode(stmtType node);
treeNode *traversal(treeNode *node1, treeNode *node2);
treeNode *createDeclVarNode(declType declVar, treeNode *expType);
treeNode *createArrayDeclVarNode(expType expNum, declType declVar, treeNode *expType);
treeNode *createDeclFuncNode(declType declFunc, treeNode *expType, treeNode *params, treeNode *blocDecl);
treeNode *createEmptyParams(expType expId);
treeNode *createArrayArg(declType declVar, treeNode *expType);
treeNode *createIfStmt(stmtType stmtIf, treeNode *exp, treeNode *stmt1, treeNode *stmt2);
treeNode *createWhileStmt(stmtType stmtWhile, treeNode *exp, treeNode *stmt);
treeNode *createAssignStmt(stmtType stmtAttrib, treeNode *var, treeNode *exp);
treeNode *createExpVar(expType expId);
treeNode *createArrayExpVar(expType expId, treeNode *exp);
treeNode *createExpOp(expType expOp, treeNode *exp1, treeNode *exp2);
treeNode *createExpNum(expType expNum);
treeNode *createActivationFunc(stmtType stmtFunc, treeNode *arguments);

#endif