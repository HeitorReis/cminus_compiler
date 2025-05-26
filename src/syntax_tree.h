#ifndef SYNTAX_TREE_H
#define SYNTAX_TREE_H

#include "node.h"

#define YYPARSER
#define YYSTYPE treeNode*

extern char *expName;
extern char *variableName;
extern char *currentScope;
extern char *yytext;

extern int tokenNUM;
extern int functionCurrentLine;
extern int argsCount;
extern int paramsCount;

int yylex();
int yyerror(char *errorMsg);

typedef struct functionStack {
    char *name;
    int line;
    struct functionStack *next;
} functionStack;

typedef struct FunctionDeclStack {
    char *name;                     // Function name
    int line;                       // Line number of the function declaration
    struct FunctionDeclStack *next; // Pointer to the next function in the stack
} FunctionDeclStack;


void pushFunctionDecl(FunctionDeclStack **headRef, char *name, int line);
void popFunctionDecl(FunctionDeclStack **headRef);
char *getCurrentFunctionName(FunctionDeclStack *head);

void popFunctionStack(functionStack **headRef);
 void pushFunctionStack(functionStack **headRef, char *name, int line);
void printFunctionStack(functionStack *functionStackHead);
  char *getFunctionName(functionStack *functionStackHead);
    int getFunctionLine(functionStack *functionStackHead);

treeNode *createDeclNode(declType node);
treeNode *createExpNode(expType node);
treeNode *createStmtNode(stmtType node);
treeNode *traversal(treeNode *node1, treeNode *node2);
treeNode *createDeclVarNode(declType declVar, treeNode *expType);
treeNode *createArrayDeclVarNode(expType expNum, declType declVar, treeNode *expType);
treeNode *createDeclFuncNode(FunctionDeclStack **declStackRef, declType declFunc, treeNode *expType, treeNode *params, treeNode *blocDecl);
treeNode *createEmptyParams(expType expId);
treeNode *createArrayArg(declType declVar, treeNode *expType);
treeNode *createIfStmt(stmtType stmtIf, treeNode *exp, treeNode *stmt1, treeNode *stmt2);
treeNode *createWhileStmt(stmtType stmtWhile, treeNode *exp, treeNode *stmt);
treeNode *createAssignStmt(stmtType stmtAttrib, treeNode *var, treeNode *exp);
treeNode *createExpVar(expType expId);
treeNode *createArrayExpVar(expType expId, treeNode *exp);
treeNode *createExpOp(expType expOp, treeNode *exp1, treeNode *exp2);
treeNode *createExpNum(expType expNum);
treeNode *createActivationFunc(functionStack *functionStackHead, stmtType stmtFunc, treeNode *arguments);

#endif