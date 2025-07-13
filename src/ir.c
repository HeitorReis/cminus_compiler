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

static const char* kind_to_string(AstNodeKind kind) {
    switch(kind) {
        case AST_PROGRAM: return "AST_PROGRAM";
        case AST_VAR_DECL: return "AST_VAR_DECL";
        case AST_FUN_DECL: return "AST_FUN_DECL";
        case AST_PARAM: return "AST_PARAM";
        case AST_PARAM_LIST: return "AST_PARAM_LIST";
        case AST_PARAM_ARRAY: return "AST_PARAM_ARRAY";
        case AST_BLOCK: return "AST_BLOCK";
        case AST_IF: return "AST_IF";
        case AST_WHILE: return "AST_WHILE";
        case AST_RETURN: return "AST_RETURN";
        case AST_ASSIGN: return "AST_ASSIGN";
        case AST_BINOP: return "AST_BINOP";
        case AST_CALL: return "AST_CALL";
        case AST_ID: return "AST_ID";
        case AST_NUM: return "AST_NUM";
        case AST_ARG_LIST: return "AST_ARG_LIST";
        default: return "UNKNOWN";
    }
}

static Operand new_temp() {
    printf("[IR_DBG] Creating new temporary: t%d\n", temp_counter);
    return (Operand){.kind = OPERAND_TEMP, .data.temp_id = temp_counter++};
}

static Operand new_label() {
    char label_name[20];
    sprintf(label_name, "L%d", label_counter);
    printf("[IR_DBG] Creating new label: %s\n", label_name);
    label_counter++;
    return (Operand){.kind = OPERAND_LABEL, .data.name = strdup(label_name)};
}

static Operand new_const(int value) {
    printf("[IR_DBG] Creating new constant: %d\n", value);
    return (Operand){.kind = OPERAND_CONST, .data.value = value};
}

static Operand new_name(const char* name) {
    if (!name) {
        fprintf(stderr, "[IR_DBG] Warning: new_name called with NULL.\n");
        return (Operand){.kind = OPERAND_EMPTY};
    }
    printf("[IR_DBG] Creating new name operand: %s\n", name);
    return (Operand){.kind = OPERAND_NAME, .data.name = strdup(name)};
}

static void emit(IRList* list, IrOpcode opcode, Operand result, Operand arg1, Operand arg2) {
    printf("[IR_DBG] Emitting instruction with opcode %d\n", opcode);
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
    if (!node) {
        printf("[IR_DBG] generate_ir_for_node: Encountered NULL node, returning.\n");
        return;
    }
    printf("[IR_DBG] > generate_ir_for_node: Processing node kind %s at line %d\n", kind_to_string(node->kind), node->lineno);

    switch (node->kind) {
        case AST_PROGRAM:
            printf("[IR_DBG]   Case AST_PROGRAM\n");
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;

        case AST_FUN_DECL: {
            printf("[IR_DBG]   Case AST_FUN_DECL for '%s'\n", node->name);
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
            printf("[IR_DBG]   Case AST_BLOCK\n");
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;

        case AST_IF: {
            printf("[IR_DBG]   Case AST_IF\n");
            Operand else_label = new_label();
            Operand end_label = new_label();

            AstNode* condition = node->firstChild;
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
            printf("[IR_DBG]   Case AST_WHILE\n");
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
            printf("[IR_DBG]   Case AST_RETURN\n");
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
            printf("[IR_DBG]   Case %s (as statement)\n", kind_to_string(node->kind));
            generate_ir_for_expr(node, list, symtab);
            break;

        case AST_VAR_DECL:
        case AST_PARAM:
        case AST_PARAM_LIST:
        case AST_PARAM_ARRAY:
            printf("[IR_DBG]   Skipping declaration node %s\n", kind_to_string(node->kind));
            break;

        default:
            printf("[IR_DBG]   Default case, traversing children for node %s\n", kind_to_string(node->kind));
            for (AstNode* child = node->firstChild; child; child = child->nextSibling) {
                generate_ir_for_node(child, list, symtab);
            }
            break;
    }
    printf("[IR_DBG] < generate_ir_for_node: Finished processing node kind %s\n", kind_to_string(node->kind));
}

static Operand generate_ir_for_expr(AstNode* node, IRList* list, SymbolTable* symtab) {
    if (!node) {
        printf("[IR_DBG] generate_ir_for_expr: Encountered NULL node, returning EMPTY operand.\n");
        return (Operand){.kind=OPERAND_EMPTY};
    }
    printf("[IR_DBG] >> generate_ir_for_expr: Processing expression kind %s at line %d\n", kind_to_string(node->kind), node->lineno);

    Operand result_op = {.kind = OPERAND_EMPTY};

    switch (node->kind) {
        case AST_NUM:
            printf("[IR_DBG]    Case AST_NUM\n");
            result_op = new_const(node->value);
            break;

        case AST_ID:
            printf("[IR_DBG]    Case AST_ID\n");
            result_op = new_name(node->name);
            break;

        case AST_ASSIGN: {
            printf("[IR_DBG]    Case AST_ASSIGN\n");
            AstNode* lhs = node->firstChild;
            if (!lhs) break;
            AstNode* rhs = lhs->nextSibling;
            if (!rhs) break;

            Operand rhs_op = generate_ir_for_expr(rhs, list, symtab);
            Operand lhs_op = new_name(lhs->name);
            emit(list, IR_ASSIGN, lhs_op, rhs_op, (Operand){.kind=OPERAND_EMPTY});
            result_op = lhs_op;
            break;
        }

        case AST_BINOP: {
            // Corrected: Added a NULL check for node->name before using strcmp
            if (node->name == NULL) {
                fprintf(stderr, "[IR_DBG] Error: AST_BINOP node at line %d has a NULL operator name.\n", node->lineno);
                // Attempt to process children anyway if they exist, assuming it's a wrapper node
                if(node->firstChild) {
                    result_op = generate_ir_for_expr(node->firstChild, list, symtab);
                }
                break;
            }
            printf("[IR_DBG]    Case AST_BINOP ('%s')\n", node->name);
            AstNode* left = node->firstChild;
            if (!left) break;
            AstNode* right = left->nextSibling;
            if (!right) break;

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
                break;
            }
            
            emit(list, op, result, left_op, right_op);
            result_op = result;
            break;
        }

        case AST_CALL: {
            printf("[IR_DBG]    Case AST_CALL for function '%s'\n", node->name);
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
                result_op = result;
            } else {
                emit(list, IR_PCALL, new_name(node->name), new_const(arg_count), (Operand){.kind=OPERAND_EMPTY});
                result_op = (Operand){.kind=OPERAND_EMPTY};
            }
            break;
        }

        default:
            fprintf(stderr, "[IR_DBG] Unhandled expression node kind: %s\n", kind_to_string(node->kind));
            result_op = (Operand){.kind=OPERAND_EMPTY};
            break;
    }
    printf("[IR_DBG] << generate_ir_for_expr: Finished processing expression kind %s\n", kind_to_string(node->kind));
    return result_op;
}

// --- Public Functions ---

IRList* generate_ir(AstNode* root, SymbolTable* symtab) {
    printf("\n[IR_DBG] === Starting IR Generation ===\n");
    IRList* list = (IRList*)malloc(sizeof(IRList));
    if (!list) {
        perror("Failed to allocate IR list");
        exit(EXIT_FAILURE);
    }
    list->head = list->tail = NULL;
    temp_counter = 0;
    label_counter = 0;
    
    generate_ir_for_node(root, list, symtab);
    
    printf("[IR_DBG] === Finished IR Generation ===\n");
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
