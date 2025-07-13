import collections
import re

# Mapeamento de nomes simbólicos para registradores físicos
SPECIAL_REGS = {'sp': 'r13', 'lr': 'r14', 'fp': 'r11', 'retval': 'r0', 'arg': 'r0'}

class RegisterAllocator:
    """ Gerencia o uso de registradores com alocação estática de memória. """
    def __init__(self, func_context):
        self.func_context = func_context
        self.reg_pool = [f"r{i}" for i in range(4, 11)]
        self.free_regs = collections.deque(self.reg_pool.copy())
        self.var_to_reg = {}
        self.reg_to_var = {}
        self.dirty_regs = set()

    def ensure_var_in_reg(self, var_name):
        """ Garante que uma variável ou imediato esteja em um registrador. """
        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
            reg = self._get_free_reg()
            self.func_context.add_instruction(f"\tmovi: {reg} = {var_name}")
            return reg
        
        if var_name in self.var_to_reg:
            self._mark_reg_used(self.var_to_reg[var_name])
            return self.var_to_reg[var_name]

        reg = self._get_free_reg()
        # A instrução é gerada com um placeholder que será substituído depois
        self.func_context.add_instruction(f"\tloadi: {reg} = [var_{var_name}]")
        self._assign_reg_to_var(reg, var_name)
        self.dirty_regs.discard(reg)
        return reg

    def get_reg_for_temp(self, temp_name):
        reg = self._get_free_reg()
        self._assign_reg_to_var(temp_name, reg)
        self.dirty_regs.add(reg)
        return reg

    def update_var_from_reg(self, var_name, reg):
        self._assign_reg_to_var(var_name, reg)
        self.dirty_regs.add(reg)

    def spill_reg(self, reg):
        if reg in self.dirty_regs:
            var_name = self.reg_to_var.get(reg)
            if var_name:
                # Gera instrução com placeholder
                self.func_context.add_instruction(f"\tstorei: [var_{var_name}] = {reg}")
            self.dirty_regs.discard(reg)
        
        if reg in self.reg_to_var:
            var_name = self.reg_to_var.pop(reg)
            self.var_to_reg.pop(var_name, None)
        
        if reg not in self.free_regs:
            self.free_regs.appendleft(reg)

    def spill_all(self):
        for reg in self.reg_pool:
            if reg in self.reg_to_var:
                self.spill_reg(reg)

    def _get_free_reg(self):
        if not self.free_regs:
            reg_to_spill = self.free_regs.pop() # LRU aproximado
            self.spill_reg(reg_to_spill)
            self.free_regs.appendleft(reg_to_spill)
            return reg_to_spill
        return self.free_regs.popleft()

    def _assign_reg_to_var(self, reg, var_name):
        if reg in self.reg_to_var: self.spill_reg(reg)
        self.var_to_reg[var_name] = reg
        self.reg_to_var[reg] = var_name
        if reg in self.free_regs: self.free_regs.remove(reg)

    def _mark_reg_used(self, reg):
        if reg in self.free_regs: self.free_regs.remove(reg)
        self.free_regs.append(reg)

class FunctionContext:
    def __init__(self, name):
        self.name = name
        self.instructions = []
        self.allocator = RegisterAllocator(self)

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

IR_TO_COND = {'>': ('gt', 'lteq'), '<': ('lt', 'gteq'), '==': ('eq', 'neq'),
              '!=': ('neq', 'eq'), '>=': ('gteq', 'lt'), '<=': ('lteq', 'gt')}

def translate_instruction(instr_parts, func_ctx):
    alloc = func_ctx.allocator
    opcode = instr_parts[0]
    
    if opcode.endswith(':'): alloc.spill_all(); func_ctx.add_instruction(opcode); return
    if opcode == 'goto': alloc.spill_all(); func_ctx.add_instruction(f"b: {instr_parts[1]}"); return

    if ':=' in instr_parts:
        dest, _, *expr_parts = instr_parts
        if expr_parts[0].startswith('*'):
            reg = alloc.ensure_var_in_reg(expr_parts[0][1:])
            alloc.update_var_from_reg(dest, reg)
        elif dest.startswith('*'):
            reg_val = alloc.ensure_var_in_reg(expr_parts[0])
            func_ctx.add_instruction(f"\tstorei: [var_{dest[1:]}] = {reg_val}")
        elif 'call' in expr_parts:
            alloc.spill_all()
            func_ctx.add_instruction(f"\tbl: {expr_parts[1].replace(',', '')}")
            dest_reg = alloc.get_reg_for_temp(dest)
            func_ctx.add_instruction(f"\tmov: {dest_reg} = {SPECIAL_REGS['retval']}")
        elif len(expr_parts) > 1 and expr_parts[1] in IR_TO_COND:
            op, arg2 = expr_parts[1], expr_parts[2]
            arg1_reg = alloc.ensure_var_in_reg(expr_parts[0])
            if arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit()):
                compare_instr = f"\tsubis: r0 = {arg1_reg}, {arg2}"
            else:
                arg2_reg = alloc.ensure_var_in_reg(arg2)
                compare_instr = f"\tsubis: r0 = {arg1_reg}, {arg2_reg}"
            dest_reg = alloc.get_reg_for_temp(dest)
            cond_true, cond_false = IR_TO_COND[op]
            func_ctx.add_instruction(compare_instr)
            # A ordem do sufixo é [opcode][suporte][condição]
            func_ctx.add_instruction(f"\tmovi{cond_true}: {dest_reg} = 1")
            func_ctx.add_instruction(f"\tmovi{cond_false}: {dest_reg} = 0")
        else:
            reg_src = alloc.ensure_var_in_reg(expr_parts[0])
            alloc.update_var_from_reg(dest, reg_src)
    elif opcode == 'if_false':
        reg = alloc.ensure_var_in_reg(instr_parts[1])
        func_ctx.add_instruction(f"\tsubis: r0 = {reg}, 0")
        func_ctx.add_instruction(f"beq: {instr_parts[3]}")
    elif opcode == 'arg':
        reg = alloc.ensure_var_in_reg(instr_parts[1])
        func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['arg']} = {reg}")
    elif opcode == 'return':
        if len(instr_parts) > 1 and instr_parts[1] != '_':
            reg = alloc.ensure_var_in_reg(instr_parts[1])
            func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['retval']} = {reg}")
        alloc.spill_all()
        func_ctx.add_instruction(f"\tb: {func_ctx.name}_epilogue")


def generate_assembly(ir_list):
    functions = collections.OrderedDict()
    all_vars = set()
    
    # Pass 1: Descobrir funções e todas as variáveis estáticas
    active_func_name = None
    for line in ir_list:
        parts = line.strip().split()
        if not parts: continue
        
        for part in re.split(r'[\s,:=\*\[\]]+', line):
             if part and part.startswith(('t', 'v', 'x', 'y', 'z')):
                all_vars.add(part)

        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if not func_name.startswith('L'):
                active_func_name = func_name
                if func_name not in functions:
                    functions[func_name] = FunctionContext(func_name)
    
    # Pass 2: Gerar código intermediário para cada função
    for func_name, func_ctx in functions.items():
        func_ir = []
        in_func = False
        for line in ir_list:
            stripped = line.strip()
            if not stripped: continue
            if stripped.startswith(func_name + ':'): in_func = True
            elif stripped.endswith(':') and not stripped.startswith('L'): in_func = False
            if in_func: func_ir.append(stripped)
        
        for line in func_ir:
            translate_instruction(line.split(), func_ctx)
        # Adicionar um epílogo implícito
        func_ctx.add_instruction(f"b: {func_name}_epilogue")


    # Pass 3: Calcular layout de memória e resolver branches
    final_code = [".text", ".global main", ""]
    code_section_size = 0
    # Calcular tamanho da seção de código
    for func_name, func_ctx in functions.items():
        # Prólogo simples (apenas label da função)
        code_section_size += 1 
        # Corpo da função
        for instr in func_ctx.instructions:
            if not instr.endswith(':'):
                code_section_size += 1
        # Epílogo (ret)
        code_section_size += 1 

    # Calcular endereços das variáveis estáticas
    data_base_address = code_section_size * 4 # Assumindo 4 bytes por instrução
    var_address_map = {}
    current_addr = data_base_address
    for var in sorted(list(all_vars)):
        var_address_map[f"var_{var}"] = current_addr
        current_addr += 4

    # Pass 4: Montar código final com endereços e offsets resolvidos
    instruction_counter = 0
    for func_name, func_ctx in functions.items():
        func_body_start_pos = instruction_counter + 1 # Posição após o label da função
        final_code.append(f"{func_name}:")
        instruction_counter += 1

        label_map = {}
        temp_code = []
        # Mapear labels para suas posições relativas no corpo da função
        for instr in func_ctx.instructions:
            if instr.endswith(':'):
                label_map[instr[:-1]] = len(temp_code)
            else:
                temp_code.append(instr)
        label_map[f"{func_name}_epilogue"] = len(temp_code)

        # Gerar o corpo da função com branches e endereços resolvidos
        for i, instr in enumerate(temp_code):
            # Substituir placeholders de endereço de memória
            instr = re.sub(r'\[(var_.*?)\]', lambda m: f"{var_address_map.get(m.group(1), 0)}", instr)

            parts = instr.strip().split(':')
            opcode = parts[0].strip()
            if opcode in ['b', 'beq']:
                target_label = parts[1].strip()
                offset = label_map.get(target_label, len(temp_code)) - i - 1
                # ALTERAÇÃO MÍNIMA AQUI:
                if opcode == 'beq':
                    final_code.append(f"\tbieq: {offset}")
                else: # opcode == 'b'
                    final_code.append(f"\tbi: {offset}")
            else:
                final_code.append(instr)
        
        instruction_counter += len(temp_code)
        # Adicionar epílogo simples
        final_code.append("\tret:")
        instruction_counter += 1
        final_code.append("")

    # Adicionar seção de dados
    final_code.append(".data")
    for var in sorted(list(all_vars)):
        final_code.append(f"var_{var}: .word 0")

    return "\n".join(final_code)
