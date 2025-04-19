// Exemplo: em analisador_semantico.h
#ifndef SEMANTIC_ANALYSIS_H
#define SEMANTIC_ANALYSIS_H

// Outras declarações...

void insertSymbolInTable(char *name, char *scope, SymbolType type, int line, primitiveType dataType);

void semanticAnalysis();

#endif // SEMANTIC_ANALYSIS_H
