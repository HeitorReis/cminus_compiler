#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "node.h"
#include "syntax_tree.h"

#define DEBUG_FUNCTION_STACK 1 // Set to 1 to enable debugging, 0 to disable

extern char *yytext;
extern int yylineno;
extern int tokenNUM;

char *expName;
char *variableName;
char *currentScope = "global";

functionStack *functionStackHead = NULL;
functionStack **functionStackRef = &functionStackHead;

FunctionDeclStack *functionDeclStackHead = NULL;
FunctionDeclStack **functionDeclStackRef = &functionDeclStackHead;

void popFunctionStack(functionStack **headRef) {
    if (*headRef == NULL) {
        fprintf(stderr, "Warning: Attempted to pop from an empty function stack.\n");
        return;
    }
    functionStack *temp = *headRef;
    *headRef = (*headRef)->next;
    free(temp->name);
    free(temp);
}


void pushFunctionStack(functionStack **headRef, char *name, int line) {
    functionStack *newNode = (functionStack *)malloc(sizeof(functionStack));
    if (!newNode) {
        fprintf(stderr, "Error: Memory allocation failed in pushFunctionStack.\n");
        exit(EXIT_FAILURE);
    }
    newNode->name = strdup(name);
    if (!newNode->name) {
        fprintf(stderr, "Error: Memory allocation failed for function name in pushFunctionStack.\n");
        free(newNode);
        exit(EXIT_FAILURE);
    }
    newNode->line = line;
    newNode->next = *headRef;
    *headRef = newNode;
}


void printFunctionStack(functionStack *functionStackHead) {
    functionStack *temp = functionStackHead;
    if (temp == NULL) {
        printf("Function stack is empty.\n");
        return;
    }
    while (temp != NULL) {
        printf("Function: %s\n", temp->name);
        printf("Line: %d\n", temp->line);
        temp = temp->next;
    }
}

char *getFunctionName(functionStack *functionStackHead) {
    if (functionStackHead != NULL) {
        return functionStackHead->name;
    }
    return NULL;
}

int getFunctionLine(functionStack *functionStackHead) {
    if (functionStackHead != NULL) {
        return functionStackHead->line;
    }
    return 0;
}

int argsCount = 0;
int paramsCount = 0;

treeNode *createNode() {
    treeNode *newNode = (treeNode*) malloc(sizeof(treeNode));
    for (int i = 0; i < CHILD_MAX_NODES; i++) {
        newNode->child[i] = NULL;
    }
    newNode->sibling = NULL;
    newNode->line = yylineno;
    newNode->scope = currentScope;
    return newNode;
}

treeNode *createDeclNode(declType node) {
    treeNode *newNode = createNode();
    newNode->node = decl;
    newNode->declSubType = node;
    return newNode;
}

treeNode *createStmtNode(stmtType node) {
    treeNode *newNode = createNode();
    newNode->node = stmt;
    newNode->stmtSubType = node;
    return newNode;
}

treeNode *createExpNode(expType node) {
    treeNode *newNode = createNode();
    newNode->node = exp;
    newNode->expSubType = node;
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
    declVarNode->name = expName;
    declVarNode->type = expType->type;
    expType->child[0] = declVarNode;
    return expType;
}

treeNode *createArrayDeclVarNode(expType expNum, declType declVar, treeNode *expType) {
    treeNode *expNumNode = createExpNode(expNum);
    expNumNode->value = tokenNUM;  
    expNumNode->type = Integer;

    treeNode *declVarNode = createDeclNode(declVar);
    declVarNode->name = expName; 
    declVarNode->child[0] = expNumNode;

    declVarNode->type = (expType->type == Integer) ? Array : Void;
    expType->child[0] = declVarNode;
    return expType;
}

treeNode *createDeclFuncNode(
    FunctionDeclStack **declStackRef,
    declType declFunc, 
    treeNode *expType, 
    treeNode *params, 
    treeNode *blocDecl
) {
    treeNode* declFuncNode = createDeclNode(declFunc);
    declFuncNode->child[0] = params;
    declFuncNode->child[1] = blocDecl;
    declFuncNode->name = getFunctionName(*declStackRef);
    declFuncNode->line = getCurrentFunctionLine(*declStackRef);
    declFuncNode->type = expType->type;
    declFuncNode->params = paramsCount;
    expType->child[0] = declFuncNode;
    return expType;
}

treeNode *createEmptyParams(expType expId) {
    treeNode *node = createExpNode(expId);
    node->name = "void";
    node->type = Void;
    return node;
}

treeNode *createArrayArg(declType declVar, treeNode *expType) {
    treeNode *declVarNode = createDeclNode(declVar);
    declVarNode->name = expName;
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
    expVarNode->name = expName;
    expVarNode->type = Void;
    return expVarNode;
}

treeNode *createArrayExpVar(expType expId, treeNode *exp) {
    treeNode *expVarNode = createExpNode(expId);
    expVarNode->name = variableName;
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
    expNumNode->value = atoi(yytext);   
    expNumNode->type = Integer;
    return expNumNode;
}

treeNode *createActivationFunc(functionStack *functionStackHead, stmtType stmtFunc, treeNode *arguments) {
    treeNode *activationFuncNode = createStmtNode(stmtFunc);
    activationFuncNode->child[1] = arguments; 
    const char *funcName = getFunctionName(functionStackHead);
    if (!funcName) {
        fprintf(stderr, "Error: Function name is NULL in createActivationFunc.\n");
        exit(EXIT_FAILURE);
    }
    activationFuncNode->name = funcName;
    activationFuncNode->line = getCurrentFunctionLine(*functionStackRef);
    activationFuncNode->args = argsCount;
    return activationFuncNode;
}

/* === Novo construtor para chamada em expressão === */
treeNode *createExpCallNode(const char *funcName, treeNode *args) {
    treeNode *node = createExpNode(expCall);
    node->name = strdup(funcName);
    node->child[0] = args;  /* lista de argumentos */
    node->type = Void;      /* será ajustado na semântica */
    return node;
}

void pushFunctionDecl(FunctionDeclStack **headRef, char *name, int line) {
    FunctionDeclStack *newNode = (FunctionDeclStack *)malloc(sizeof(FunctionDeclStack));
    if (!newNode) {
        fprintf(stderr, "Error: Memory allocation failed in pushFunctionDecl.\n");
        exit(EXIT_FAILURE);
    }
    newNode->name = strdup(name);
    if (!newNode->name) {
        fprintf(stderr, "Error: Memory allocation failed for function name in pushFunctionDecl.\n");
        free(newNode);
        exit(EXIT_FAILURE);
    }
    newNode->line = line;
    newNode->next = *headRef;
    *headRef = newNode;

#if DEBUG_FUNCTION_STACK
    printf("[DEBUG] PUSHED Function Declaration: %s at Line: %d\n", name, line);
#endif
}

void popFunctionDecl(FunctionDeclStack **headRef) {
    if (*headRef == NULL) {
        fprintf(stderr, "Warning: Attempted to pop from an empty function declaration stack.\n");
        return;
    }
    FunctionDeclStack *temp = *headRef;
    *headRef = (*headRef)->next;

#if DEBUG_FUNCTION_STACK
    printf("[DEBUG] POPPED Function Declaration: %s at Line: %d\n", temp->name, temp->line);
#endif

    free(temp->name);
    free(temp);
}

char *getCurrentFunctionName(FunctionDeclStack *head) {
    if (head != NULL) {
        return head->name;
    }
    return NULL;
}

int getCurrentFunctionLine(FunctionDeclStack *head) {
    if (head != NULL) {
        return head->line;
    }
    return 0;
}

#if DEBUG_FUNCTION_STACK
void printFunctionDeclStack(FunctionDeclStack *head) {
    FunctionDeclStack *tmp = head;
    if (!tmp) {
        printf("[DEBUG] FunctionDeclStack is empty.\n");
        return;
    }
    printf("[DEBUG] Current FunctionDeclStack:\n");
    while (tmp) {
        printf("  → %s (decl at line %d)\n", tmp->name, tmp->line);
        tmp = tmp->next;
    }
}
#endif
