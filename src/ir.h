/* src/ir.h */
#ifndef IR_H
#define IR_H

#include "syntax_tree.h"   /* for AstNode definition */

/* forward declaration of your AST node */
typedef struct AstNode AstNode;

/* your three-address IR opcodes */
typedef enum {
    IR_ADD, IR_SUB, IR_MUL, IR_DIV,
    IR_HT, IR_LT, IR_HTE, IR_LTE,
    IR_MOD, IR_EQ, IR_NEQ,
    IR_AND, IR_OR, IR_XOR, IR_NOT,
    IR_LOAD, IR_STORE,
    IR_CALL, IR_RET,
    IR_LABEL, IR_BR, IR_BRZ,
    IR_MOV
} IrOp;

/* one IR instruction in a linked list */
typedef struct IR {
    IrOp        op;
    char       *res;   /* destination/temp or label */
    char       *arg1;  /* source1 or label */
    char       *arg2;  /* source2 or immediate */
    struct IR  *next;
} IR;

/* head/tail pointers for easy append */
typedef struct IRList {
    IR *head;
    IR *tail;
} IRList;

/* IR list management */
IRList *ir_list_create(void);
IR  *ir_new       (IrOp op, char *res, char *arg1, char *arg2);
void  ir_append   (IRList *list, IR *node);
void  dumpIR      (IRList *list, FILE *out);
void  freeIR      (IRList *list);

/* name generators */
char *new_temp(void);
char *new_label(void);

/* top-level IR entry point */
IRList *generateIR(AstNode *root);

#endif /* IR_H */
