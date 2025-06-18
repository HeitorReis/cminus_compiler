#ifndef CODEGEN_H
#define CODEGEN_H

#include "syntax_tree.h"
#include "ir.h"

void generateCode(IRList *ir, const char *filename);

#endif
