#include "node.h"

extern char *yytext;

treeNode *syntaxTree;
int treeSize = 0;

void printTreeNode(treeNode *tree) {
    if (tree == NULL) return;

    treeSize += 2;
    for (int i = 0; i < treeSize; i++) {
        printf(" ");
    }

    if (tree->node == exp) {
        switch (tree->nodeSubType.exp) {
            case expNum:
                printf("NUM: %d\n", tree->key.value);
                break;
            case expId:
                if (tree->key.name != NULL && strcmp(tree->key.name, "void") == 0) {
                    printf("void \n");
                } else if (tree->key.name != NULL) {
                    printf("ID: %s\n", tree->key.name);
                    //printf(" -> SCOPE: %s\n", tree->scope);
                } else {
                    printf("ID: NULL\n");
                }
                break;
            case expOp:
                switch (tree->key.op) {
                case 14:
                    printf("OPERATOR: + \n");
                    break;
                case 15:
                    printf("OPERATOR: - \n");
                    break;
                case 16:
                    printf("OPERATOR: * \n");
                    break;
                case 17:
                    printf("OPERATOR: / \n");
                    break;
                case 10:
                    printf("OPERATOR: < \n");
                    break;
                case 11:
                    printf("OPERATOR: <= \n");
                    break;
                case 12:
                    printf("OPERATOR: > \n");
                    break;
                case 13:
                    printf("OPERATOR: >= \n");
                    break;
                case 8:
                    printf("OPERATOR: == \n");
                    break;
                case 9:
                    printf("OPERATOR: != \n");
                    break;
                default:
                    printf("OPERATOR: UNKNOWN\n");
                }
                break;
            default:
                printf("INVALID EXPRESION");
        }
    } else if (tree->node == stmt) {
        switch (tree->nodeSubType.stmt) {
            case stmtIf:
                printf("if \n");
                break;
            case stmtWhile:
                printf("while \n");
                break;
            case stmtAttrib:
                printf("ASSIGN \n");
                break;
            case stmtReturn:
                printf("return \n");
                break;
            case stmtFunc:
                if (tree->key.name != NULL) {
                    printf("Function Call: %s\n", tree->key.name);
                }
                break;
            default:
                printf("INVALID STATEMENT \n");
        }
    } else if (tree->node == decl) {
        switch (tree->nodeSubType.decl) {
            case declFunc:
                if (tree->key.name != NULL) {
                    printf("Function Declaration: %s\n", tree->key.name);
                } else {
                    printf("Function Declaration: NULL\n");
                }
                break;
            case declVar:
                if (tree->key.name != NULL) {
                    printf("Variable Declaration: %s\n", tree->key.name);
                } else {
                    printf("Variable Declaration: NULL\n");
                }
                break;
            case declIdType:
                if (tree->type == Integer) {
                    printf("Type int \n");
                } else if (tree->type == Array) {
                    printf("Type int[] \n");
                } else {
                    printf("Type void \n");
                }
                break;
            default:
                printf("INVALID DECLARATION \n");
        }
    }
}

void printSyntaxTree(treeNode *tree) {
    if (tree == NULL) return;

    printTreeNode(tree);

    for (int i = 0; i < CHILD_MAX_NODES; i++) {
        if (tree->child[i] != NULL) {
            printSyntaxTree(tree->child[i]);
        }
    }
    treeSize -= 2;

    if (tree->sibling != NULL) {
        printSyntaxTree(tree->sibling);
    }
}