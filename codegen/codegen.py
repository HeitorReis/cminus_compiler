import collections

# Mapeamento de nomes simbólicos para registradores físicos
SPECIAL_REGS = {'sp': 'r13', 'lr': 'r14', 'fp': 'r11', 'retval': 'r0', 'arg': 'r0'}

class RegisterAllocator:
    """
    Gerencia o uso de registradores, otimizando loads/stores e mantendo o estado.
    Usa uma fila (deque) para uma política de substituição LRU (Least Recently Used) aproximada.
    """
    def __init__(self, func_context):
        self.func_context = func_context
        self.reg_pool = [f"r{i}" for i in range(4, 11)]  # r4-r10 para uso geral
        self.free_regs = collections.deque(self.reg_pool)
        self.var_to_reg = {}
        self.reg_to_var = {}
        self.dirty_regs = set()

    def _get_stack_offset(self, var_name):
        """ Retorna o offset da variável na pilha a partir do frame pointer (fp). """
        if var_name not in self.func_context.var_map:
            self.func_context.stack_size += 4
            offset = -self.func_context.stack_size
            self.func_context.var_map[var_name] = offset
        return self.func_context.var_map[var_name]

    def ensure_var_in_reg(self, var_name):
        """ Garante que uma variável ou imediato esteja em um registrador. """
        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
            reg = self._get_free_reg()
            self.func_context.add_instruction(f"\tmovi: {reg} = #{var_name}")
            return reg
        
        if var_name in self.var_to_reg:
            reg = self.var_to_reg[var_name]
            # Move o registrador para o final da fila para indicar que foi usado recentemente
            if reg in self.free_regs: self.free_regs.remove(reg)
            self.free_regs.append(reg)
            return reg

        reg = self._get_free_reg()
        offset = self._get_stack_offset(var_name)
        self.func_context.add_instruction(f"\tloadi: {reg} = [{SPECIAL_REGS['fp']}, #{offset}]")
        self._assign_reg_to_var(reg, var_name)
        self.dirty_regs.discard(reg)
        return reg

    def get_reg_for_temp(self, temp_name):
        """ Aloca um registrador para um resultado temporário. """
        reg = self._get_free_reg()
        self._assign_reg_to_var(temp_name, reg)
        self.dirty_regs.add(reg)
        return reg

    def update_var_from_reg(self, var_name, reg):
        self._assign_reg_to_var(var_name, reg)
        self.dirty_regs.add(reg)

    def spill_reg(self, reg):
        """ Salva um registrador na pilha se necessário e o libera. """
        if reg in self.dirty_regs:
            var_name = self.reg_to_var.get(reg)
            if var_name:
                offset = self._get_stack_offset(var_name)
                self.func_context.add_instruction(f"\tstorei: [{SPECIAL_REGS['fp']}, #{offset}] = {reg}")
            self.dirty_regs.discard(reg)
        
        if reg in self.reg_to_var:
            var_name = self.reg_to_var.pop(reg)
            self.var_to_reg.pop(var_name, None)
        
        if reg not in self.free_regs:
            self.free_regs.appendleft(reg)

    def spill_all(self):
        """ Força o spill de todos os registradores alocados. """
        for reg in self.reg_pool:
            if reg in self.reg_to_var:
                self.spill_reg(reg)

    def _get_free_reg(self):
        if not self.free_regs:
            # Lógica de spill: libera o registrador usado menos recentemente (início da fila)
            reg_to_spill = self.free_regs.popleft()
            self.spill_reg(reg_to_spill)
            self.free_regs.append(reg_to_spill)
            return reg_to_spill
        
        reg = self.free_regs.popleft()
        self.free_regs.append(reg) # Move para o final (mais recentemente usado)
        return reg

    def _assign_reg_to_var(self, reg, var_name):
        if reg in self.reg_to_var: self.spill_reg(reg)
        self.var_to_reg[var_name] = reg
        self.reg_to_var[reg] = var_name
        if reg in self.free_regs:
             self.free_regs.remove(reg)

class FunctionContext:
    def __init__(self, name):
        self.name = name
        self.var_map = {}
        self.stack_size = 0
        self.instructions = []
        self.allocator = RegisterAllocator(self)

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

    def generate_prologue(self):
        prologue = [
            f"{self.name}:",
            f"\tstorei: [{SPECIAL_REGS['sp']}, #-4]! = {SPECIAL_REGS['lr']}",
            f"\tstorei: [{SPECIAL_REGS['sp']}, #-4]! = {SPECIAL_REGS['fp']}",
            f"\tmov: {SPECIAL_REGS['fp']} = {SPECIAL_REGS['sp']}"
        ]
        if self.stack_size > 0:
            prologue.append(f"\tsubi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, #{self.stack_size}")
        return prologue

    def generate_epilogue(self):
        epilogue = [
            f"{self.name}_epilogue:",
            f"\tmov: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['fp']}",
            f"\tloadi: {SPECIAL_REGS['fp']} = [{SPECIAL_REGS['sp']}]!",
            f"\tloadi: {SPECIAL_REGS['lr']} = [{SPECIAL_REGS['sp']}]!",
            "\tret"
        ]
        return epilogue

IR_TO_COND = {'>': ('gt', 'lteq'), '<': ('lt', 'gteq'), '==': ('eq', 'neq'),
              '!=': ('neq', 'eq'), '>=': ('gteq', 'lt'), '<=': ('lteq', 'gt')}

def translate_instruction(instr_parts, func_ctx):
    alloc = func_ctx.allocator
    opcode = instr_parts[0]
    
    if opcode.endswith(':'): alloc.spill_all(); func_ctx.add_instruction(opcode); return
    if opcode == 'goto': alloc.spill_all(); func_ctx.add_instruction(f"b: {instr_parts[1]}"); return

    if ':=' in instr_parts:
        dest, _, *expr_parts = instr_parts
        expr = " ".join(expr_parts)

        if expr.startswith('*'):
            reg = alloc.ensure_var_in_reg(expr_parts[0][1:])
            alloc.update_var_from_reg(dest, reg)
        elif dest.startswith('*'):
            offset = alloc._get_stack_offset(dest[1:])
            reg_val = alloc.ensure_var_in_reg(expr_parts[0])
            func_ctx.add_instruction(f"\tstorei: [{SPECIAL_REGS['fp']}, #{offset}] = {reg_val}")
        elif 'call' in expr:
            alloc.spill_all()
            func_ctx.add_instruction(f"\tbl: {expr_parts[1].replace(',', '')}")
            dest_reg = alloc.get_reg_for_temp(dest)
            func_ctx.add_instruction(f"\tmov: {dest_reg} = {SPECIAL_REGS['retval']}")
        elif len(expr_parts) > 1 and expr_parts[1] in IR_TO_COND:
            op, arg2 = expr_parts[1], expr_parts[2]
            arg1_reg = alloc.ensure_var_in_reg(expr_parts[0])
            if arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit()):
                compare_instr = f"\tsubis: r0, {arg1_reg}, #{arg2}"
            else:
                arg2_reg = alloc.ensure_var_in_reg(arg2)
                compare_instr = f"\tsubis: r0, {arg1_reg}, {arg2_reg}"
            dest_reg = alloc.get_reg_for_temp(dest)
            cond_true, cond_false = IR_TO_COND[op]
            func_ctx.add_instruction(compare_instr)
            func_ctx.add_instruction(f"\tmov{cond_true}i: {dest_reg} = #1")
            func_ctx.add_instruction(f"\tmov{cond_false}i: {dest_reg} = #0")
        else:
            reg_src = alloc.ensure_var_in_reg(expr_parts[0])
            alloc.update_var_from_reg(dest, reg_src)
    elif opcode == 'if_false':
        reg = alloc.ensure_var_in_reg(instr_parts[1])
        func_ctx.add_instruction(f"\tsubis: r0, {reg}, #0")
        func_ctx.add_instruction(f"beq: {instr_parts[3]}")
    elif opcode == 'arg':
        reg = alloc.ensure_var_in_reg(instr_parts[1])
        func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['arg']} = {reg}")
    elif opcode == 'return':
        if len(instr_parts) > 1 and instr_parts[1] != '_':
            reg = alloc.ensure_var_in_reg(instr_parts[1])
            func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['retval']} = {reg}")
        alloc.spill_all()
        func_ctx.add_instruction(f"b: {func_ctx.name}_epilogue")

def generate_assembly(ir_list):
    functions = collections.OrderedDict()
    
    # Pass 1: Discover all functions first to initialize their contexts.
    for line in ir_list:
        parts = line.strip().split()
        if not parts: continue
        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if not func_name.startswith('L'):
                if func_name not in functions:
                    functions[func_name] = FunctionContext(func_name)

    # Pass 2: Process IR line by line, assigning instructions to the current function context.
    active_func_ctx = None
    for line in ir_list:
        parts = line.strip().split()
        if not parts: continue
        
        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if func_name in functions:
                active_func_ctx = functions[func_name]

        if active_func_ctx:
            translate_instruction(parts, active_func_ctx)

    # Pass 3: Resolve branches and build the final code string.
    final_code = [".text", ".global main", ""]
    for func_name, func_ctx in functions.items():
        # Pre-pass to determine stack size based on all variables encountered.
        alloc = func_ctx.allocator
        # Re-scan a clean version of the function's IR to map all variables
        func_ir_lines = [l.strip() for l in ir_list if l.strip()]
        start_idx = func_ir_lines.index(f"{func_name}:")
        end_idx = len(func_ir_lines)
        for i in range(start_idx + 1, len(func_ir_lines)):
            if func_ir_lines[i].endswith(':') and not func_ir_lines[i].startswith('L'):
                end_idx = i
                break
        
        for line in func_ir_lines[start_idx:end_idx]:
             parts = line.replace(',', ' ').replace('[', ' ').replace(']', ' ').replace(':', '').split()
             for part in parts:
                if part.startswith(('t', 'v', 'x', 'y', 'z')):
                    alloc._get_stack_offset(part)

        final_code.extend(func_ctx.generate_prologue())
        
        label_map = {}
        temp_code = []
        for instr in func_ctx.instructions:
            if instr.endswith(':'):
                label_map[instr[:-1]] = len(temp_code)
            else:
                temp_code.append(instr)
        
        label_map[f"{func_name}_epilogue"] = len(temp_code)

        final_body = []
        for i, instr in enumerate(temp_code):
            parts = instr.strip().split()
            opcode = parts[0][:-1] 
            if opcode in ['b', 'beq']:
                target_label = parts[1]
                offset = label_map[target_label] - i - 1
                final_body.append(f"\t{opcode}i: #{offset}")
            else:
                final_body.append(instr)
        
        final_code.extend(final_body)
        final_code.extend(func_ctx.generate_epilogue())
        final_code.append("")

    return "\n".join(final_code)
