#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "syntax_tree.h"
#include "node.h"
#include "utils.h"
#include "symbol_table.h"
#include "semantic.h"

extern SymbolTable tabela;
extern treeNode *syntaxTree;

void inicializaFuncoesBuiltIn() {
    insertSymbol(&tabela, "input", "global", FUNC, 0, Integer);
    
    insertSymbol(&tabela, "output", "global", FUNC, 0, Void);
}

void checkUndeclaredVariable(char *name, char *scope, int line) {
    if (!findSymbol(&tabela, name, scope)) {
        printf("Erro semântico: Variável '%s' não declarada na linha %d\n", name, line);
    }
}

void checkInvalidAssignment(char *name, char *scope, primitiveType expectedType, int line) {
    Symbol *symbol = findSymbol(&tabela, name, scope);
    if (symbol && symbol->dataType != expectedType) {
        printf("Erro semântico: Atribuição inválida para a variável '%s' na linha %d\n", name, line);
    }
}

void checkFunctionReturnType(char *name, primitiveType expectedType, int line) {
    Symbol *symbol = findSymbol(&tabela, name, "global");
    if (symbol && symbol->dataType != expectedType) {
        printf("Erro semântico: Função '%s' não retorna o tipo esperado na linha %d\n", name, line);
    }
}

void checkFunctionDeclared(char *name, int line) {
    if (!findSymbol(&tabela, name, "global")) {
        printf("Erro semântico: Função '%s' não declarada na linha %d\n", name, line);
    }
}

void checkMainFunctionDeclared() {
    if (!findSymbol(&tabela, "main", "global")) {
        printf("Erro semântico: Função 'main' não declarada\n");
    }
}

void checkDuplicateDeclaration(char *name, char *scope, int line) {
    if (findSymbol(&tabela, name, scope)) {
        printf("Erro semântico: '%s' já foi declarado previamente no escopo '%s' na linha %d\n", name, scope, line);
    }
}

void checkVoidVariableDeclaration(primitiveType type, int line) {
    if (type == Void) {
        printf("Erro semântico: Declaração inválida de variável na linha %d. 'void' só pode ser usado para declaração de função.\n", line);
    }
}

void traverseTree(treeNode *node, char *scope) {
    if (node == NULL) return;

    switch (node->node) {
        case decl:
            switch (node->nodeSubType.decl) {
                case declVar:
                    checkDuplicateDeclaration(node->key.name, scope, node->line);
                    checkVoidVariableDeclaration(node->type, node->line);
                    insertSymbolInTable(node->key.name, scope, VAR, node->line, node->type);
                    break;
                case declFunc:
                    checkDuplicateDeclaration(node->key.name, "global", node->line);
                    insertSymbolInTable(node->key.name, "global", FUNC, node->line, node->type);
                    traverseTree(node->child[0], node->key.name); // Params
                    traverseTree(node->child[1], node->key.name); // Body
                    break;
                default:
                    break;
            }
            break;
        case stmt:
            switch (node->nodeSubType.stmt) {
                case stmtAttrib:
                    checkUndeclaredVariable(node->child[0]->key.name, scope, node->line);
                    checkInvalidAssignment(node->child[0]->key.name, scope, node->child[1]->type, node->line);
                    break;
                case stmtReturn:
                    checkFunctionReturnType(scope, node->child[0]->type, node->line);
                    break;
                case stmtFunc:
                    checkFunctionDeclared(node->key.name, node->line);
                    break;
                default:
                    break;
            }
            break;
        case exp:
            switch (node->nodeSubType.exp) {
                case expId:
                    checkUndeclaredVariable(node->key.name, scope, node->line);
                    break;
                default:
                    break;
            }
            break;
        default:
            break;
    }

    for (int i = 0; i < CHILD_MAX_NODES; i++) {
        traverseTree(node->child[i], scope);
    }
    traverseTree(node->sibling, scope);
}

void semanticAnalysis() {
    inicializaFuncoesBuiltIn();
    
    checkMainFunctionDeclared();
    
    traverseTree(syntaxTree, "global");
}
