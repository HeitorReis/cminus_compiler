#include <stdio.h>
#include <string.h>
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
        switch (tree->expSubType) {
            case expNum:
                printf("NUM: %d\n", tree->value);
                break;
            case expId:
                if (tree->name != NULL && strcmp(tree->name, "void") == 0) {
                    printf("void\n");
                } else if (tree->name != NULL) {
                    printf("ID: %s\n", tree->name);
                } else {
                    printf("ID: NULL\n");
                }
                break;
            case expOp:
                switch (tree->op) {
                    case 14: printf("OPERATOR: +\n"); break;
                    case 15: printf("OPERATOR: -\n"); break;
                    case 16: printf("OPERATOR: *\n"); break;
                    case 17: printf("OPERATOR: /\n"); break;
                    case 10: printf("OPERATOR: <\n"); break;
                    case 11: printf("OPERATOR: <=\n"); break;
                    case 12: printf("OPERATOR: >\n"); break;
                    case 13: printf("OPERATOR: >=\n"); break;
                    case 8:  printf("OPERATOR: ==\n"); break;
                    case 9:  printf("OPERATOR: !=\n"); break;
                    default: printf("OPERATOR: UNKNOWN\n");
                }
                break;
            case expCall:
                if (tree->name)
                    printf("Function Call: %s\n", tree->name);
                else
                    printf("Function Call: NULL\n");
                break;
            default:
                printf("INVALID EXPRESSION\n");
        }
    }
    else if (tree->node == stmt) {
        switch (tree->stmtSubType) {
            case stmtIf:     printf("if\n"); break;
            case stmtWhile:  printf("while\n"); break;
            case stmtAttrib: printf("ASSIGN\n"); break;
            case stmtReturn: printf("return\n"); break;
            case stmtFunc:
                if (tree->name != NULL) {
                    printf("Function Call: %s\n", tree->name);
                }
                break;
            default:
                printf("INVALID STATEMENT\n");
        }
    }
    else if (tree->node == decl) {
        switch (tree->declSubType) {
            case declFunc:
                printf("Function Declaration: %s\n",
                       tree->name ? tree->name : "NULL");
                break;
            case declVar:
                printf("Variable Declaration: %s\n",
                       tree->name ? tree->name : "NULL");
                break;
            case declIdType:
                if (tree->type == Integer)      printf("Type int\n");
                else if (tree->type == Array)   printf("Type int[]\n");
                else                             printf("Type void\n");
                break;
            default:
                printf("INVALID DECLARATION\n");
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
