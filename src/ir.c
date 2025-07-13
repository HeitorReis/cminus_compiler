#include "ir.h"
#include "syntax_tree.h"
#include "semantic.h" // Include for TYPE_INT definition
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// --- Forward Declarations for Helper Functions ---

static void generate_ir_for_node(AstNode* node, IRList* list, SymbolTable* symtab);
static Operand generate_ir_for_expr(AstNode* node, IRList* list, SymbolTable* symtab);

// --- State for generating unique temps and labels ---
static int temp_counter = 0;
static int label_counter = 0;

// --- Helper functions to create new operands and emit instructions ---

static Operand new_temp() {
    return (Operand){.kind = OPERAND_TEMP, .data.temp_id = temp_counter++};
}

static Operand new_label() {
    char label_name[20];
    sprintf(label_name, "L%d", label_counter++);
    return (Operand){.kind = OPERAND_LABEL, .data.name = strdup(label_name)};
}

static Operand new_const(int value) {
    return (Operand){.kind = OPERAND_CONST, .data.value = value};
}

// Corrected: Added a NULL check to prevent strdup(NULL)
static Operand new_name(const char* name) {
    if (!name) {
        fprintf(stderr, "Warning: new_name called with NULL.\n");
        return (Operand){.kind = OPERAND_EMPTY};
    }
    return (Operand){.kind = OPERAND_NAME, .data.name = strdup(name)};
}

static void emit(IRList* list, IrOpcode opcode, Operand result, Operand arg1, Operand arg2) {
    IRInstruction* instr = (IRInstruction*)malloc(sizeof(IRInstruction));
    if (!instr) {
        perror("Failed to allocate IR instruction");
        exit(EXIT_FAILURE);
    }
    instr->opcode = opcode;
    instr->result = result;
    instr->arg1 = arg1;
    instr->arg2 = arg2;
    instr->next = NULL;

    if (list->head == NULL) {
        list->head = list->tail = instr;
    } else {
        list->tail->next = instr;
        list->tail = instr;
    }
}

// --- Main IR Generation Logic ---

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
            emit(list, IR_RETURN, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            break;
        }

        case AST_BLOCK:
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;

        case AST_IF: {
            Operand else_label = new_label();
            Operand end_label = new_label();

            AstNode* condition = node->firstChild;
            // Corrected: Check that condition and then_stmt exist before proceeding
            if (!condition) break;
            AstNode* then_stmt = condition->nextSibling;
            if (!then_stmt) break;
            AstNode* else_stmt = then_stmt->nextSibling;

            Operand cond_result = generate_ir_for_expr(condition, list, symtab);
            emit(list, IR_IF_GOTO, else_label, cond_result, (Operand){.kind=OPERAND_EMPTY});
            
            generate_ir_for_node(then_stmt, list, symtab);
            emit(list, IR_GOTO, end_label, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            
            emit(list, IR_LABEL, else_label, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            if (else_stmt) {
                generate_ir_for_node(else_stmt, list, symtab);
            }
            emit(list, IR_LABEL, end_label, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            break;
        }

        case AST_WHILE: {
            Operand start_label = new_label();
            Operand end_label = new_label();
            
            AstNode* condition = node->firstChild;
            if (!condition) break;
            AstNode* body = condition->nextSibling;
            if (!body) break;

            emit(list, IR_LABEL, start_label, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            Operand cond_result = generate_ir_for_expr(condition, list, symtab);
            emit(list, IR_IF_GOTO, end_label, cond_result, (Operand){.kind=OPERAND_EMPTY});
            generate_ir_for_node(body, list, symtab);
            emit(list, IR_GOTO, start_label, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            emit(list, IR_LABEL, end_label, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            break;
        }

        case AST_RETURN: {
            if (node->firstChild) {
                Operand ret_val = generate_ir_for_expr(node->firstChild, list, symtab);
                emit(list, IR_RETURN, ret_val, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            } else {
                emit(list, IR_RETURN, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
            }
            break;
        }
        
        case AST_ASSIGN:
        case AST_CALL:
            generate_ir_for_expr(node, list, symtab);
            break;

        case AST_VAR_DECL:
        case AST_PARAM:
        case AST_PARAM_LIST:
        case AST_PARAM_ARRAY:
            // These nodes do not generate executable code at the statement level.
            break;

        default:
            // For other nodes, traverse children if they exist.
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;
    }
}

static Operand generate_ir_for_expr(AstNode* node, IRList* list, SymbolTable* symtab) {
    if (!node) return (Operand){.kind=OPERAND_EMPTY};

    switch (node->kind) {
        case AST_NUM:
            return new_const(node->value);

        case AST_ID:
            return new_name(node->name);

        case AST_ASSIGN: {
            // Corrected: Add NULL checks for lhs and rhs
            AstNode* lhs = node->firstChild;
            if (!lhs) return (Operand){.kind=OPERAND_EMPTY};
            AstNode* rhs = lhs->nextSibling;
            if (!rhs) return (Operand){.kind=OPERAND_EMPTY};

            Operand rhs_op = generate_ir_for_expr(rhs, list, symtab);
            Operand lhs_op = new_name(lhs->name);
            emit(list, IR_ASSIGN, lhs_op, rhs_op, (Operand){.kind=OPERAND_EMPTY});
            return lhs_op;
        }

        case AST_BINOP: {
            // Corrected: Add NULL checks for left and right children
            AstNode* left = node->firstChild;
            if (!left) return (Operand){.kind=OPERAND_EMPTY};
            AstNode* right = left->nextSibling;
            if (!right) return (Operand){.kind=OPERAND_EMPTY};

            Operand left_op = generate_ir_for_expr(left, list, symtab);
            Operand right_op = generate_ir_for_expr(right, list, symtab);
            Operand result = new_temp();
            
            IrOpcode op;
            if (strcmp(node->name, "+") == 0) op = IR_ADD;
            else if (strcmp(node->name, "-") == 0) op = IR_SUB;
            else if (strcmp(node->name, "*") == 0) op = IR_MUL;
            else if (strcmp(node->name, "/") == 0) op = IR_DIV;
            else if (strcmp(node->name, "==") == 0) op = IR_EQ;
            else if (strcmp(node->name, "!=") == 0) op = IR_NEQ;
            else if (strcmp(node->name, "<") == 0) op = IR_LT;
            else if (strcmp(node->name, "<=") == 0) op = IR_LTE;
            else if (strcmp(node->name, ">") == 0) op = IR_GT;
            else if (strcmp(node->name, ">=") == 0) op = IR_GTE;
            else {
                fprintf(stderr, "Unknown binary operator: %s\n", node->name);
                return (Operand){.kind=OPERAND_EMPTY};
            }
            
            emit(list, op, result, left_op, right_op);
            return result;
        }

        case AST_CALL: {
            Symbol* func_symbol = getSymbol(symtab, node->name, "global");
            int arg_count = 0;
            AstNode* arg_list_node = node->firstChild;
            if (arg_list_node) {
                for (AstNode* arg = arg_list_node->firstChild; arg; arg = arg->nextSibling) {
                    Operand arg_op = generate_ir_for_expr(arg, list, symtab);
                    emit(list, IR_ARG, arg_op, (Operand){.kind=OPERAND_EMPTY}, (Operand){.kind=OPERAND_EMPTY});
                    arg_count++;
                }
            }
            
            if (func_symbol && func_symbol->dataType == TYPE_INT) {
                Operand result = new_temp();
                emit(list, IR_CALL, result, new_name(node->name), new_const(arg_count));
                return result;
            } else {
                emit(list, IR_PCALL, new_name(node->name), new_const(arg_count), (Operand){.kind=OPERAND_EMPTY});
                return (Operand){.kind=OPERAND_EMPTY};
            }
        }

        default:
            fprintf(stderr, "Unhandled expression node kind: %d\n", node->kind);
            return (Operand){.kind=OPERAND_EMPTY};
    }
}

// --- Public Functions ---

IRList* generate_ir(AstNode* root, SymbolTable* symtab) {
    IRList* list = (IRList*)malloc(sizeof(IRList));
    if (!list) {
        perror("Failed to allocate IR list");
        exit(EXIT_FAILURE);
    }
    list->head = list->tail = NULL;
    temp_counter = 0;
    label_counter = 0;
    
    generate_ir_for_node(root, list, symtab);
    
    return list;
}

static void print_operand(FILE* out, Operand op) {
    if (!out) return;
    switch (op.kind) {
        case OPERAND_TEMP:  fprintf(out, "t%d", op.data.temp_id); break;
        case OPERAND_CONST: fprintf(out, "%d", op.data.value); break;
        case OPERAND_NAME:  fprintf(out, "%s", op.data.name ? op.data.name : "NULL_NAME"); break;
        case OPERAND_LABEL: fprintf(out, "%s", op.data.name ? op.data.name : "NULL_LABEL"); break;
        case OPERAND_EMPTY: fprintf(out, "_"); break;
        default:            fprintf(out, "UNKNOWN_OP"); break;
    }
}

static void print_instruction_to_stream(FILE* out, IRInstruction* instr) {
    if (!out || !instr) return;
    switch (instr->opcode) {
        case IR_LABEL:   print_operand(out, instr->result); fprintf(out, ":"); break;
        case IR_GOTO:    fprintf(out, "  goto "); print_operand(out, instr->result); break;
        case IR_IF_GOTO: fprintf(out, "  if_false "); print_operand(out, instr->arg1); fprintf(out, " goto "); print_operand(out, instr->result); break;
        case IR_RETURN:  fprintf(out, "  return "); print_operand(out, instr->result); break;
        case IR_ASSIGN:  fprintf(out, "  "); print_operand(out, instr->result); fprintf(out, " := "); print_operand(out, instr->arg1); break;
        case IR_ARG:     fprintf(out, "  arg "); print_operand(out, instr->result); break;
        case IR_CALL:    fprintf(out, "  "); print_operand(out, instr->result); fprintf(out, " := call "); print_operand(out, instr->arg1); fprintf(out, ", "); print_operand(out, instr->arg2); break;
        case IR_PCALL:   fprintf(out, "  call "); print_operand(out, instr->result); fprintf(out, ", "); print_operand(out, instr->arg1); break;
        case IR_LOAD:    fprintf(out, "  "); print_operand(out, instr->result); fprintf(out, " := *"); print_operand(out, instr->arg1); break;
        case IR_STORE:   fprintf(out, "  *"); print_operand(out, instr->result); fprintf(out, " := "); print_operand(out, instr->arg1); break;
        default: {
            const char* op_str = "?";
            switch(instr->opcode) {
                case IR_ADD: op_str = "+"; break; case IR_SUB: op_str = "-"; break; case IR_MUL: op_str = "*"; break; case IR_DIV: op_str = "/"; break;
                case IR_EQ:  op_str = "=="; break; case IR_NEQ: op_str = "!="; break; case IR_LT:  op_str = "<"; break; case IR_LTE: op_str = "<="; break;
                case IR_GT:  op_str = ">"; break; case IR_GTE: op_str = ">="; break;
                default: break;
            }
            fprintf(out, "  "); print_operand(out, instr->result); fprintf(out, " := "); print_operand(out, instr->arg1); fprintf(out, " %s ", op_str); print_operand(out, instr->arg2); break;
        }
    }
    fprintf(out, "\n");
}

void print_ir(IRList* list, FILE* stream) {
    const char* file_path = "docs/output/ir_dump.txt";
    FILE* outfile = fopen(file_path, "w");
    if (!outfile) {
        fprintf(stderr, "\n[Compiler Warning] Could not open '%s' for writing. Ensure 'docs/output' directory exists.\n", file_path);
    }

    printf("\n--- BEGIN IR DUMP (Terminal) ---\n");
    for (IRInstruction* instr = list->head; instr; instr = instr->next) {
        print_instruction_to_stream(stdout, instr);
    }
    printf("--- END IR DUMP ---\n");

    if (outfile) {
        for (IRInstruction* instr = list->head; instr; instr = instr->next) {
            print_instruction_to_stream(outfile, instr);
        }
        fclose(outfile);
        printf("IR dump has been saved to: %s\n", file_path);
    }
}

void free_ir(IRList* list) {
    if (!list) return;
    IRInstruction* current = list->head;
    while (current) {
        IRInstruction* next = current->next;
        if (current->result.kind == OPERAND_NAME || current->result.kind == OPERAND_LABEL) free(current->result.data.name);
        if (current->arg1.kind == OPERAND_NAME || current->arg1.kind == OPERAND_LABEL) free(current->arg1.data.name);
        if (current->arg2.kind == OPERAND_NAME || current->arg2.kind == OPERAND_LABEL) free(current->arg2.data.name);
        free(current);
        current = next;
    }
    free(list);
}
