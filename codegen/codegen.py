import collections
import re

# Mapeamento de nomes simbólicos para registradores físicos
SPECIAL_REGS = {'sp': 'r13', 'lr': 'r14', 'fp': 'r11', 'retval': 'r0', 'arg': 'r0'}

class RegisterAllocator:
    """ Gerencia o uso de registradores com uma lógica de spill aprimorada (LRU). """
    def __init__(self, func_context):
        self.func_context = func_context
        self.reg_pool = [f"r{i}" for i in range(4, 11)] 
        self.free_regs = collections.deque(self.reg_pool.copy())
        self.used_regs_order = collections.deque()
        self.var_to_reg = {}
        self.reg_to_var = {}
        self.dirty_regs = set()

    def ensure_var_in_reg(self, var_name):
        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
            reg = self._get_free_reg()
            self.func_context.add_instruction(f"\tmovi: {reg} = {var_name}")
            self._mark_reg_used(reg)
            return reg
        
        if var_name in self.var_to_reg:
            reg = self.var_to_reg[var_name]
            self._mark_reg_used(reg)
            return reg

        reg = self._get_free_reg()
        self.func_context.add_instruction(f"\tloadi: {reg} = [var_{var_name}]")
        self._assign_reg_to_var(reg, var_name)
        self.dirty_regs.discard(reg)
        return reg

    def get_reg_for_temp(self, temp_name):
        reg = self._get_free_reg()
        self._assign_reg_to_var(reg, temp_name)
        self.dirty_regs.add(reg)
        return reg

    def update_var_from_reg(self, var_name, reg):
        self._assign_reg_to_var(var_name, reg)
        self.dirty_regs.add(reg)

    def spill_reg(self, reg):
        if reg in self.dirty_regs:
            var_name = self.reg_to_var.get(reg)
            if var_name:
                self.func_context.add_instruction(f"\tstorei: [var_{var_name}] = {reg}")
            self.dirty_regs.discard(reg)
        
        if reg in self.reg_to_var:
            var_name = self.reg_to_var.pop(reg)
            if var_name in self.var_to_reg:
                del self.var_to_reg[var_name]
        
        if reg in self.used_regs_order:
            self.used_regs_order.remove(reg)
        
        if reg not in self.free_regs:
            self.free_regs.append(reg)

    def spill_all(self):
        for reg in list(self.reg_to_var.keys()):
            self.spill_reg(reg)

    def _get_free_reg(self):
        if self.free_regs:
            return self.free_regs.popleft()
        
        if not self.used_regs_order:
            raise Exception("Register allocation error: No registers available to spill.")

        reg_to_spill = self.used_regs_order.popleft()
        self.spill_reg(reg_to_spill)
        return self.free_regs.popleft()

    def _assign_reg_to_var(self, reg, var_name):
        if reg in self.reg_to_var: self.spill_reg(reg)
        if var_name in self.var_to_reg: self.spill_reg(self.var_to_reg[var_name])

        self.var_to_reg[var_name] = reg
        self.reg_to_var[reg] = var_name
        
        if reg in self.free_regs:
            self.free_regs.remove(reg)
        
        self._mark_reg_used(reg)

    def _mark_reg_used(self, reg):
        if reg in self.used_regs_order:
            self.used_regs_order.remove(reg)
        self.used_regs_order.append(reg)

class FunctionContext:
    def __init__(self, name):
        self.name = name
        self.instructions = []
        self.allocator = RegisterAllocator(self)

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

IR_BRANCH_COND = {'>': 'bigt', '<': 'bilt', '==': 'bieq', '!=': 'bineq', '>=': 'bigteq', '<=': 'bilteq'}

def translate_instruction(instr_parts, func_ctx):
    alloc = func_ctx.allocator
    opcode = instr_parts[0]
    
    if opcode.endswith(':'):
        alloc.spill_all()
        func_ctx.add_instruction(opcode)
        return
    if opcode == 'goto':
        alloc.spill_all()
        func_ctx.add_instruction(f"\tbi: {instr_parts[1]}")
        return

    if ':=' in instr_parts:
        dest, _, *expr_parts = instr_parts
        
        if 'call' in expr_parts:
            # (A lógica de chamada de função ainda tem problemas, mas vamos corrigi-la depois)
            func_name = expr_parts[1].replace(',', '')
            alloc.spill_all()

            if func_name == 'input':
                dest_reg = alloc.get_reg_for_temp(dest)
                func_ctx.add_instruction(f"\tin: {dest_reg}")
            else: 
                func_ctx.add_instruction(f"\tbl: {func_name}")
                if dest:
                    dest_reg = alloc.get_reg_for_temp(dest)
                    func_ctx.add_instruction(f"\tmov: {dest_reg} = {SPECIAL_REGS['retval']}")

        # Verifica se é uma operação aritmética como: t2 := t1 * 2
        elif len(expr_parts) == 3 and expr_parts[1] in ['+', '-', '*', '/']:
            op_map = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
            
            arg1, op_str, arg2 = expr_parts
            
            # Garante que os operandos estão em registradores
            reg1 = alloc.ensure_var_in_reg(arg1)
            
            # Determina a instrução assembly (imediata ou registrador)
            assembly_op = op_map[op_str]
            if arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit()):
                assembly_op += 'i' # Usa a versão imediata: addi, muli, etc.
                reg2 = arg2 # O operando é o próprio número
            else:
                reg2 = alloc.ensure_var_in_reg(arg2)

            # Obtém um registrador para o resultado
            dest_reg = alloc.get_reg_for_temp(dest)
            
            # Gera a instrução de assembly
            func_ctx.add_instruction(f"\t{assembly_op}: {dest_reg} = {reg1}, {reg2}")
            
            # Libera os registradores dos operandos se eles forem temporários
            if arg1.startswith('t'): alloc.spill_reg(reg1)
            if arg2.startswith('t') and not (arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit())): alloc.spill_reg(reg2)
            
        elif len(expr_parts) > 1 and expr_parts[1] in IR_BRANCH_COND:
            op, arg2 = expr_parts[1], expr_parts[2]
            arg1_reg = alloc.ensure_var_in_reg(expr_parts[0])
            arg2_reg = alloc.ensure_var_in_reg(arg2)
            func_ctx.add_instruction(f"\tsubis: r0 = {arg1_reg}, {arg2_reg}")
            alloc.spill_reg(arg1_reg)
            alloc.spill_reg(arg2_reg)

        elif expr_parts[0].startswith('*'):
            var_name = expr_parts[0][1:]
            reg = alloc.ensure_var_in_reg(var_name)
            alloc.update_var_from_reg(dest, reg)
        elif dest.startswith('*'):
            var_name = dest[1:]
            reg_val = alloc.ensure_var_in_reg(expr_parts[0])
            func_ctx.add_instruction(f"\tstorei: [var_{var_name}] = {reg_val}")
            alloc.spill_reg(reg_val)
        else:
            reg_src = alloc.ensure_var_in_reg(expr_parts[0])
            alloc.update_var_from_reg(dest, reg_src)
    
    elif opcode == 'if_false':
        func_ctx.add_instruction(f"\tbilteq: {instr_parts[3]}")
    
    elif opcode == 'arg':
        reg = alloc.ensure_var_in_reg(instr_parts[1])
        func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['arg']} = {reg}")
        alloc.spill_reg(reg)
    
    elif opcode == 'return':
        if len(instr_parts) > 1 and instr_parts[1] != '_':
            reg = alloc.ensure_var_in_reg(instr_parts[1])
            func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['retval']} = {reg}")
        alloc.spill_all()
    
def generate_assembly(ir_list):
    functions = collections.OrderedDict()
    all_vars = set()
    
    for line in ir_list:
        parts = line.strip().split()
        if not parts: continue
        
        for part in re.split(r'[\s,:=\*\[\]]+', line):
            if part and part.isalpha() and part not in ['call', 'goto', 'arg', 'return', 'if_false']:
                all_vars.add(part)

        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if not func_name.startswith('L'):
                if func_name not in functions:
                    functions[func_name] = FunctionContext(func_name)

    if not functions and any(ir_list):
        functions['main'] = FunctionContext('main')

    for func_name, func_ctx in functions.items():
        func_ir = []
        in_func = False
        for line in ir_list:
            stripped = line.strip()
            if not stripped: continue
            
            if stripped.startswith(func_name + ':'):
                in_func = True
                continue
            
            if stripped.endswith(':') and not stripped.startswith('L'):
                if stripped[:-1] in functions and stripped[:-1] != func_name:
                    in_func = False

            if in_func:
                func_ir.append(stripped)
        
        func_ctx.instructions.clear()
        for line in func_ir:
            translate_instruction(line.split(), func_ctx)

    final_code = [".text", ".global main", ""]
    
    for func_name, func_ctx in functions.items():
        final_code.append(f"{func_name}:")
        final_code.extend(func_ctx.instructions)
        final_code.append(f"\tbi: {func_name}_epilogue")
        final_code.append(f"{func_name}_epilogue:")
        final_code.append("\tret:")
        final_code.append("")

    final_code.append(".data")
    func_names = set(functions.keys())
    var_names = sorted([var for var in all_vars if var not in func_names])

    for var in var_names:
        final_code.append(f"var_{var}: .word 0")

    return "\n".join(final_code)