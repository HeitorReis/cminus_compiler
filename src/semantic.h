// semantic.h
#ifndef SEMANTIC_ANALYSIS_H
#define SEMANTIC_ANALYSIS_H

#include "symbol_table.h"
#include "node.h"

/* Um nó na lista encadeada de mensagens de erro */
typedef struct ErrorNode {
    char *message;
    struct ErrorNode *next;
} ErrorNode;

/* Contexto da análise semântica:
 * - symbols: tabela de símbolos
 * - errors: lista de erros coletados
 */
typedef struct {
    SymbolTable symbols;
    ErrorNode  *errors;
} SemanticContext;

/* Inicializa o contexto semântico (tabela e lista de erros) */
void initSemanticContext(SemanticContext *ctx);

/* Insere na tabela as funções built-in (input e output)
 * e prepara qualquer declaração especial (como main)
 */
void prepareBuiltInsAndMain(SemanticContext *ctx);

/* Ponto de entrada da análise semântica:
 *   percorre a AST inteira, coleta erros e imprime o resultado
 */
void semanticAnalysis(treeNode *root);

/* Caminha recursivamente pela árvore sintática,
 * usando `scope` como o escopo atual (nome da função ou "global")
 */
void analyzeNode(treeNode *n, SemanticContext *ctx, const char *scope);

/* Coleta um erro (estilo printf) sem interromper a análise */
void reportError(SemanticContext *ctx, const char *fmt, ...);

/* Ao final, imprime todos os erros encontrados
 * ou mensagem de sucesso, e encerra se houver falha
 */
void printSemanticResults(SemanticContext *ctx);

#endif // SEMANTIC_ANALYSIS_H
