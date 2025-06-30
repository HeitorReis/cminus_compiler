/* file: src/ir_new.h */
#ifndef IR_NEW_H
#define IR_NEW_H

#include "syntax_tree.h"
#include "symbol_table.h"

// 1. Define Operand Types
typedef enum {
    OPERAND_EMPTY,      // No operand
    OPERAND_TEMP,       // Temporary (t1, t2)
    OPERAND_CONST,      // Integer constant (100)
    OPERAND_NAME,       // Variable/Function name (x, input)
    OPERAND_LABEL       // A label (L1, L2)
} OperandKind;

typedef struct {
    OperandKind kind;
    union {
        int temp_id;    // For OPERAND_TEMP
        int value;      // For OPERAND_CONST
        char* name;     // For OPERAND_NAME and OPERAND_LABEL
    } data;
} Operand;

// 2. Define the Full Instruction Set Opcodes
typedef enum {
    IR_ASSIGN,
    IR_ADD, IR_SUB, IR_MUL, IR_DIV,
    IR_EQ, IR_NEQ, IR_LT, IR_LTE, IR_GT, IR_GTE,
    IR_LABEL,
    IR_GOTO,
    IR_IF_GOTO,
    IR_ARG,
    IR_PCALL,       // Procedure call (void)
    IR_CALL,        // Function call (returns value)
    IR_RETURN,
    IR_LOAD,
    IR_STORE
} IrOpcode;

// 3. Define the Instruction Structure
typedef struct IRInstruction {
    IrOpcode opcode;
    Operand result;
    Operand arg1;
    Operand arg2;
    struct IRInstruction* next;
} IRInstruction;

// 4. Define the Instruction List
typedef struct {
    IRInstruction* head;
    IRInstruction* tail;
} IRList;

// 5. Declare the Public Functions for the new generator
IRList* generate_ir(AstNode* root, SymbolTable* symtab);
void print_ir(IRList* list, FILE* out);
void free_ir(IRList* list);

#endif