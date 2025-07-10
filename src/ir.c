#include "ir.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Global counters for temporary variables and labels
static int temp_counter = 0;
static int label_counter = 0;

// Function to create a new temporary operand
Operand new_temp() {
    Operand op;
    op.kind = OPERAND_TEMP;
    op.data.temp_id = temp_counter++;
    return op;
}

// Function to create a new label operand
Operand new_label() {
    Operand op;
    op.kind = OPERAND_LABEL;
    char label_name[16];
    sprintf(label_name, "L%d", label_counter++);
    op.data.name = strdup(label_name);
    return op;
}

// Function to create a new constant operand
Operand new_const(int value) {
    Operand op;
    op.kind = OPERAND_CONST;
    op.data.value = value;
    return op;
}

// Function to create a new name operand (for variables/functions)
Operand new_name(const char* name) {
    Operand op;
    op.kind = OPERAND_NAME;
    op.data.name = strdup(name);
    return op;
}

// Initializes a new, empty IR list
void init_ir_list(IRList* list) {
    list->head = NULL;
    list->tail = NULL;
}

// Appends a new instruction to the IR list
void append_ir(IRList* list, IRInstruction* instr) {
    if (!list->head) {
        list->head = list->tail = instr;
    } else {
        list->tail->next = instr;
        list->tail = instr;
    }
    instr->next = NULL;
}

// Creates and appends a new instruction
void emit(IRList* list, IrOpcode opcode, Operand result, Operand arg1, Operand arg2) {
    IRInstruction* instr = (IRInstruction*)malloc(sizeof(IRInstruction));
    instr->opcode = opcode;
    instr->result = result;
    instr->arg1 = arg1;
    instr->arg2 = arg2;
    instr->next = NULL;
    append_ir(list, instr);
}

// Forward declaration for the main traversal function
static void generate_ir_for_node(AstNode* node, IRList* list, SymbolTable* symtab);

// Main entry point for IR generation
IRList* generate_ir(AstNode* root, SymbolTable* symtab) {
    IRList* list = (IRList*)malloc(sizeof(IRList));
    init_ir_list(list);
    if (root) {
        generate_ir_for_node(root, list, symtab);
    }
    return list;
}

// The recursive workhorse for IR generation
static void generate_ir_for_node(AstNode* node, IRList* list, SymbolTable* symtab) {
    if (!node) return;

    switch (node->kind) {
        case AST_PROGRAM:
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;

        case AST_FUN_DECL: {
            emit(list, IR_LABEL, new_name(node->name), (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            AstNode* body = node->firstChild;
            if (body && body->kind == AST_PARAM_LIST) {
                body = body->nextSibling;
            }
            if (body && body->kind == AST_BLOCK) {
                generate_ir_for_node(body, list, symtab);
            }
            break;
        }

        case AST_BLOCK:
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;

        // ... (Implement cases for other AST nodes like IF, WHILE, ASSIGN, etc.) ...

        default:
            // For nodes that don't generate code directly, traverse their children
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;
    }
}

// Helper to print a single operand
void print_operand(Operand op) {
    switch (op.kind) {
        case OPERAND_TEMP:
            printf("t%d", op.data.temp_id);
            break;
        case OPERAND_CONST:
            printf("#%d", op.data.value);
            break;
        case OPERAND_NAME:
            printf("%s", op.data.name);
            break;
        case OPERAND_LABEL:
            printf("%s", op.data.name);
            break;
        case OPERAND_EMPTY:
            break;
    }
}

// Prints the entire IR list to a file
void print_ir(IRList* list, FILE* out) {
    for (IRInstruction* instr = list->head; instr; instr = instr->next) {
        switch (instr->opcode) {
            case IR_LABEL:
                print_operand(instr->result);
                fprintf(out, ":\n");
                break;
            case IR_ASSIGN:
                fprintf(out, "\t");
                print_operand(instr->result);
                fprintf(out, " := ");
                print_operand(instr->arg1);
                fprintf(out, "\n");
                break;
            // ... (Implement print cases for other opcodes) ...
            default:
                fprintf(out, "  Unhandled Opcode\n");
        }
    }
}

// Frees the memory used by the IR list
void free_ir(IRList* list) {
    IRInstruction* current = list->head;
    while (current) {
        IRInstruction* next = current->next;
        if (current->result.kind == OPERAND_NAME || current->result.kind == OPERAND_LABEL) {
            free(current->result.data.name);
        }
        if (current->arg1.kind == OPERAND_NAME || current->arg1.kind == OPERAND_LABEL) {
            free(current->arg1.data.name);
        }
        if (current->arg2.kind == OPERAND_NAME || current->arg2.kind == OPERAND_LABEL) {
            free(current->arg2.data.name);
        }
        free(current);
        current = next;
    }
    free(list);
}

