#include "analysis_state.h"

AnalysisState gAnalysisState = {0, 0, 0};

void resetAnalysisState(void) {
    gAnalysisState.lexical_error_count = 0;
    gAnalysisState.syntax_error_count = 0;
    gAnalysisState.pending_lexical_error = 0;
}

void recordLexicalError(void) {
    gAnalysisState.lexical_error_count++;
    gAnalysisState.pending_lexical_error = 1;
}

void recordSyntaxError(void) {
    gAnalysisState.syntax_error_count++;
}

int consumePendingLexicalError(void) {
    int pending = gAnalysisState.pending_lexical_error;
    gAnalysisState.pending_lexical_error = 0;
    return pending;
}
