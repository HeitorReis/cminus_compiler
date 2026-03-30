#ifndef ANALYSIS_STATE_H
#define ANALYSIS_STATE_H

typedef struct {
    int lexical_error_count;
    int syntax_error_count;
    int pending_lexical_error;
} AnalysisState;

extern AnalysisState gAnalysisState;

void resetAnalysisState(void);
void recordLexicalError(void);
void recordSyntaxError(void);
int consumePendingLexicalError(void);

#endif
