/* src/codegen.c */
#include "codegen.h"
#include <stdio.h>
#include <stdlib.h>

void generateCode(IRList *ir, const char *out_filename) {
    if (!ir) {
        fprintf(stderr, "[CG ERR] generateCode: IRList is NULL\n");
        exit(1);
    }
    FILE *out = fopen(out_filename, "w");
    if (!out) {
        perror("[CG ERR] fopen");
        exit(1);
    }
    for (IR *i = ir->head; i; i = i->next) {
        switch (i->op) {
            case IR_ADD:
                fprintf(out, "add %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_SUB:
                fprintf(out, "sub %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_MUL:
                fprintf(out, "mul %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_DIV:
                fprintf(out, "div %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_MOD:
                fprintf(out, "mod %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_HT:
                fprintf(out, "cmpgt %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_LT:
                fprintf(out, "cmplt %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_HTE:
                fprintf(out, "cmpge %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_LTE:
                fprintf(out, "cmple %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_EQ:
                fprintf(out, "cmpeq %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_NEQ:
                fprintf(out, "cmpne %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_AND:
                fprintf(out, "and %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_OR:
                fprintf(out, "or %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_XOR:
                fprintf(out, "xor %s, %s, %s\n", i->res, i->arg1, i->arg2);
                break;
            case IR_NOT:
                fprintf(out, "not %s, %s\n", i->res, i->arg1);
                break;
            case IR_LOAD:
                fprintf(out, "load %s, [%s]\n", i->res, i->arg1);
                break;
            case IR_STORE:
                fprintf(out, "store [%s], %s\n", i->res, i->arg1);
                break;
            case IR_MOV:
                fprintf(out, "mov %s, %s\n", i->res, i->arg1);
                break;
            case IR_LABEL:
                fprintf(out, "%s:\n", i->res);
                break;
            case IR_BR:
                fprintf(out, "b %s\n", i->res);
                break;
            case IR_BRZ:
                fprintf(out, "brz %s, %s\n", i->res, i->arg1);
                break;
            case IR_CALL:
                fprintf(out, "bl %s\n", i->res);
                break;
            case IR_RET:
                fprintf(out, "ret\n");
                break;
            default:
                fprintf(stderr, "[CG ERR] unknown IR op %d\n", i->op);
                fclose(out);
                exit(1);
        }
    }
    fclose(out);
}