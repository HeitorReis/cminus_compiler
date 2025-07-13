/* file: src/ir.h */
#ifndef IR_H
#define IR_H

#include "syntax_tree.h"
#include "symbol_table.h"
#include "semantic.h"

// Represents the different kinds of data that an instruction can operate on.
typedef enum {
    OPERAND_EMPTY,      // No operand
    OPERAND_TEMP,       // Temporary register (e.g., t1, t2)
    OPERAND_CONST,      // Integer constant (e.g., 100)
    OPERAND_NAME,       // Variable or function name (e.g., x, input)
    OPERAND_LABEL       // A code label (e.g., L1, L2)
} OperandKind;

// Structure for a single operand
typedef struct {
    OperandKind kind;
    union {
        int temp_id;    // For OPERAND_TEMP
        int value;      // For OPERAND_CONST
        char* name;     // For OPERAND_NAME and OPERAND_LABEL
    } data;
} Operand;

// These are the operations that can be performed in the IR.
typedef enum {
    // Memory and Assignment
    IR_ASSIGN,      // result = arg1
    IR_LOAD,        // result = *arg1 (load from address)
    IR_STORE,       // *result = arg1 (store to address)

    // Arithmetic Operations
    IR_ADD,         // result = arg1 + arg2
    IR_SUB,         // result = arg1 - arg2
    IR_MUL,         // result = arg1 * arg2
    IR_DIV,         // result = arg1 / arg2

    // Comparison Operations
    IR_EQ,          // result = (arg1 == arg2)
    IR_NEQ,         // result = (arg1 != arg2)
    IR_LT,          // result = (arg1 < arg2)
    IR_LTE,         // result = (arg1 <= arg2)
    IR_GT,          // result = (arg1 > arg2)
    IR_GTE,         // result = (arg1 >= arg2)

    // Control Flow
    IR_LABEL,       // result: (defines a label)
    IR_GOTO,        // goto result
    IR_IF_GOTO,     // if (arg1) goto result
    IR_RETURN,      // return result

    // Function Calls
    IR_ARG,         // Push an argument for a function call
    IR_PCALL,       // Procedure call (no return value)
    IR_CALL,        // Function call (with return value)

} IrOpcode;

// A single three-address-code style instruction.
typedef struct IRInstruction {
    IrOpcode opcode;
    Operand result;
    Operand arg1;
    Operand arg2;
    struct IRInstruction* next; // Pointer to the next instruction in the list
} IRInstruction;

// A doubly-linked list to hold the sequence of IR instructions.
typedef struct {
    IRInstruction* head;
    IRInstruction* tail;
} IRList;

// These functions will be implemented in ir.c

IRList* generate_ir(AstNode* root, SymbolTable* symtab);
void print_ir(IRList* list, char *file_path);
void free_ir(IRList* list);

#endif /* IR_H */