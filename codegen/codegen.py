import collections
import re

# Mapeamento de nomes simbólicos para registradores físicos
SPECIAL_REGS = {'sp': 'r13', 'lr': 'r14', 'fp': 'r11', 'retval': 'r0', 'arg': 'r0'}
ARG_REGS = ['r1', 'r2', 'r3', 'r4'] # Registrador r0 é reservado para operação de output

class RegisterAllocator:
    """
    Gerencia o uso de registradores de forma inteligente. Diferencia variáveis
    reais de temporárias, minimiza acessos à memória e usa uma política
    LRU (Least Recently Used) para liberar (spill) registradores.
    """
    def __init__(self, func_context):
        self.func_context = func_context
        # Define o conjunto de registradores de uso geral disponíveis (r4 a r10)
        self.reg_pool = [f"r{i}" for i in range(4, 11)] 
        
        # Estruturas para rastrear o estado dos registradores
        self.free_regs = collections.deque(self.reg_pool.copy())
        self.var_to_reg = {}  # Mapeia um nome de variável/temporária para um registrador (ex: 't0' -> 'r4')
        self.reg_to_var = {}  # Mapeia um registrador para a variável que ele contém (ex: 'r4' -> 't0')
        
        # Rastreia a ordem de uso para a política LRU. O registrador menos usado recentemente fica na frente.
        self.lru_order = collections.deque()
        
        # Rastreia registradores com valores novos que ainda não foram salvos na memória ("dirty")
        self.dirty_regs = set()

    def ensure_var_in_reg(self, var_name):
        """
        Garante que uma variável do código-fonte (como 'x') ou uma constante
        esteja carregada em um registrador.
        """
        # Se a variável já está em um registrador, apenas o retorna.
        if var_name in self.var_to_reg:
            reg = self.var_to_reg[var_name]
            self._mark_as_used(reg)
            return reg
        
        # Se for uma constante numérica, move o valor para um novo registrador.
        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
            reg = self._get_free_reg()
            self.func_context.add_instruction(f"\tmovi: {reg} = {var_name}")
            return reg

        if var_name.startswith('t'):
            # Se for uma variável temporária (ex: 't0'), aloca um registrador e marca como "dirty".
            pass
        else:
            # Se não, aloca um registrador e carrega a variável da memória.
            reg = self._get_free_reg()
            addr_reg = self._get_free_reg()
            self.func_context.add_instruction(f"\tmovi: {addr_reg} = var_{var_name}")
            self.func_context.add_instruction(f"\tload: {reg} = [{addr_reg}]")
            self._assign_reg_to_var(reg, var_name)
            return reg

    def get_reg_for_temp(self, temp_name):
        """
        Aloca um registrador para uma nova variável temporária (ex: 't2').
        Este registrador é marcado como "dirty" (sujo).
        """
        reg = self._get_free_reg()
        self._assign_reg_to_var(reg, temp_name)
        self.dirty_regs.add(reg)
        return reg

    def free_reg_if_temp(self, reg):
        """
        Libera um registrador se ele contiver uma temporária. Variáveis
        reais (não 't*') não são liberadas.
        """
        var_name = self.reg_to_var.get(reg)
        if var_name and var_name.startswith('t'):
            self._unassign_reg(reg)

    def update_var_from_reg(self, dest_var, src_reg):
        """
        Atualiza o mapeamento para refletir uma atribuição (mov).
        Ex: 't1 := t0', onde t0 está em src_reg. Agora t1 também aponta para src_reg.
        """
        self._assign_reg_to_var(src_reg, dest_var)

    def spill_all_dirty(self):
        """
        Força o salvamento de todas as variáveis "reais" (não temporárias) que
        estão em registradores sujos. Útil antes de chamadas de função.
        """
        for reg in list(self.dirty_regs):
            var_name = self.reg_to_var.get(reg)
            if var_name and not var_name.startswith('t'):
                # CORREÇÃO: Dividir em duas instruções separadas
                addr_reg = self._get_free_reg()
                self.func_context.add_instruction(f"\tmovi: {addr_reg} = var_{var_name}")
                self.func_context.add_instruction(f"\tstore: [{addr_reg}] = {reg}")
                self.dirty_regs.discard(reg)

    def _get_free_reg(self):
        """
        Obtém um registrador livre. Se não houver, derrama (spills) o menos
        usado recentemente (LRU).
        """
        if self.free_regs:
            reg = self.free_regs.popleft()
            self._mark_as_used(reg)
            return reg
        
        # Se não há registradores livres, escolhe o menos usado para derramar.
        if not self.lru_order:
            raise Exception("Erro de alocação: Sem registradores disponíveis para derramar.")
        
        reg_to_spill = self.lru_order.popleft() # Pega o menos usado recentemente
        self._spill_reg(reg_to_spill)
        self._mark_as_used(reg_to_spill)
        return reg_to_spill

    def _spill_reg(self, reg):
        """ Salva um registrador na memória se ele estiver 'sujo' e contiver uma variável real. """
        if reg in self.dirty_regs:
            var_name = self.reg_to_var.get(reg)
            # A CONDIÇÃO MAIS IMPORTANTE:
            # Só salva na memória se for uma variável real (não começa com 't').
            # Ignora completamente as temporárias.
            if var_name and not var_name.startswith('t'):
                # CORREÇÃO: Dividir em duas instruções separadas
                addr_reg = self._get_free_reg()
                self.func_context.add_instruction(f"\tmovi: {addr_reg} = var_{var_name}")
                self.func_context.add_instruction(f"\tstore: [{addr_reg}] = {reg}")
            
            # Independentemente de ter salvo ou não, o registrador não está mais "sujo".
            self.dirty_regs.discard(reg)
        
        # Remove o mapeamento antigo do registrador para que ele possa ser reutilizado
        self._unassign_reg(reg)

    def _assign_reg_to_var(self, reg, var_name):
        """ Cria um novo mapeamento entre um registrador e uma variável. """
        if var_name in self.var_to_reg and self.var_to_reg[var_name] != reg:
            old_reg = self.var_to_reg[var_name]
            self._unassign_reg(old_reg)

        if reg in self.reg_to_var and self.reg_to_var[reg] != var_name:
            self._unassign_reg(reg)

        self.var_to_reg[var_name] = reg
        self.reg_to_var[reg] = var_name  # <-- CORREÇÃO: Deve ser var_name, não reg
        self._mark_as_used(reg)

    def _unassign_reg(self, reg):
        """ Remove todos os mapeamentos de um registrador e o devolve à lista de livres. """
        if reg in self.reg_to_var:
            var_name = self.reg_to_var.pop(reg)
            if var_name in self.var_to_reg:
                del self.var_to_reg[var_name]

        if reg not in self.free_regs:
            self.free_regs.append(reg) # Devolve para a lista de livres
        if reg in self.lru_order:
            self.lru_order.remove(reg)

    def _mark_as_used(self, reg):
        """ Marca um registrador como o mais recentemente usado. """
        if reg in self.lru_order:
            self.lru_order.remove(reg)
        self.lru_order.append(reg)

class FunctionContext:
    def __init__(self, name):
        self.name = name
        self.instructions = []
        self.allocator = RegisterAllocator(self)
        self.arg_count = 0

    def add_instruction(self, instruction):
        self.instructions.append(instruction)

IR_BRANCH_COND = {'>': 'bigt', '<': 'bilt', '==': 'bieq', '!=': 'bineq', '>=': 'bigteq', '<=': 'bilteq'}

def translate_instruction(instr_parts, func_ctx):
    """
    Trabalha com o novo RegisterAllocator para traduzir uma única linha de IR
    para um assembly mais eficiente e conceitualmente correto.
    """
    alloc = func_ctx.allocator
    opcode = instr_parts[0]
    
    if opcode.endswith(':'):
        alloc.spill_all_dirty()
        func_ctx.add_instruction(opcode)
        return
    if opcode == 'goto':
        alloc.spill_all_dirty()
        func_ctx.add_instruction(f"\tbi: {instr_parts[1]}")
        return

    if ':=' in instr_parts:
        dest, _, *expr_parts = instr_parts
        
        # --- LÓGICA DE ATRIBUIÇÃO E OPERAÇÕES ---
        
        # CASO 1: Operação aritmética (ex: t2 := t0 + t1)
        if len(expr_parts) > 1 and expr_parts[1] in ['+', '-', '*', '/', '<', '<=', '>', '>=', '==', '!=']:
            op_map = {
                '+': 'add', '-': 'sub', '*': 'mul', '/': 'div',
                '<': 'slt', '<=': 'sle', '>': 'sgt', '>=': 'sge',
                '==': 'seq', '!=': 'sne'
                }
            arg1, op_str, arg2 = expr_parts
            
            # Garante que os operandos estejam em registradores
            reg1 = alloc.ensure_var_in_reg(arg1)
            assembly_op = op_map[op_str]
            
            # Verifica se o segundo operando é um imediato ou um registrador
            if arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit()):
                assembly_op += 'i'  # Usa a versão imediata da instrução
                op2_val = arg2
            else:
                op2_val = alloc.ensure_var_in_reg(arg2)
            
            # Obtém um registrador para o resultado e marca-o como "sujo"
            dest_reg = alloc.get_reg_for_temp(dest)
            func_ctx.add_instruction(f"\t{assembly_op}: {dest_reg} = {reg1}, {op2_val}")
        
        elif expr_parts[0].startswith('&'):
            var_name = expr_parts[0][1:]
            dest_reg = alloc.get_reg_for_temp(dest)
            # Gera a instrução para obter o endereço da variável
            func_ctx.add_instruction(f"\tmovi: {dest_reg} = var_{var_name}")
        # CASO 2:  t1 := *t2 (Carregar Valor Usando um Endereço que está em um Registador)
        # O '*' diz-nos para tratar o operando (t2) não como um valor, mas como um ponteiro.
        elif expr_parts[0].startswith('*'):
            var_name_to_load_from = expr_parts[0][1:]
            addr_reg = alloc.ensure_var_in_reg(var_name_to_load_from) 
            dest_reg = alloc.get_reg_for_temp(dest)
            
            # PASSO 1: Obter o ENDEREÇO da variável para um registador.
            addr_reg = alloc.get_reg_for_temp(f"addr_{var_name_to_load_from}")
            func_ctx.add_instruction(f"\tload: {dest_reg} = [{addr_reg}]")
        
        # CASO 3: *x := t1 (Armazenar valor na memória)
        # Aqui, o '*' está no destino. Queremos guardar um valor no endereço apontado por t1.
        elif dest.startswith('*'):
            var_name_to_store_in = dest[1:]
            
            # PASSO 1: Obter o ENDEREÇO da variável de destino.
            addr_reg = alloc.get_reg_for_temp(f"addr_{var_name_to_store_in}")
            func_ctx.add_instruction(f"\tmovi: {addr_reg} = var_{var_name_to_store_in}")
            
            # PASSO 2: Garantir que o VALOR a ser guardado está num registador.
            src_reg = alloc.ensure_var_in_reg(expr_parts[0])
            
            # PASSO 3: Executar o store.
            func_ctx.add_instruction(f"\tstore: [{addr_reg}] = {src_reg}")

        # CASO 4: Chamada de função (ex: t0 := call input) - Sem alterações, já estava correta.
        elif 'call' in expr_parts:
            func_name = expr_parts[1].replace(',', '')
            alloc.spill_all_dirty()
            if func_name == 'input':
                dest_reg = alloc.get_reg_for_temp(dest)
                func_ctx.add_instruction(f"\tin: {dest_reg}")
            else:
                func_ctx.add_instruction(f"\tbl: {func_name}")
                dest_reg = alloc.get_reg_for_temp(dest)
                func_ctx.add_instruction(f"\tmov: {dest_reg} = {SPECIAL_REGS['retval']}")
            func_ctx.arg_count = 0
            
        # CASO 5: Operação aritmética (ex: t2 := t0 + t1) - Sem alterações, já estava correta.
        elif len(expr_parts) > 1 and expr_parts[1] in ['+', '-', '*', '/']:
            op_map = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
            arg1, op_str, arg2 = expr_parts
            reg1 = alloc.ensure_var_in_reg(arg1)
            assembly_op = op_map[op_str]
            if arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit()):
                assembly_op += 'i'
                op2_val = arg2
            else:
                op2_val = alloc.ensure_var_in_reg(arg2)
            dest_reg = alloc.get_reg_for_temp(dest)
            func_ctx.add_instruction(f"\t{assembly_op}: {dest_reg} = {reg1}, {op2_val}")
            
        # CASO 6: Movimento simples (ex: t1 := x ou t1 := t0)
        else:
            # Carrega o valor da variável/temporário da direita para um registrador
            reg_src = alloc.ensure_var_in_reg(expr_parts[0])

    # --- LÓGICA DE CONTROLO E CHAMADAS DE PROCEDIMENTO ---

    elif opcode == 'call':
        func_name = instr_parts[1].replace(',', '')
        alloc.spill_all_dirty()
        if func_name == 'output':
            # Para output, o valor a ser impresso deve estar em r0
            src_reg = alloc.ensure_var_in_reg(instr_parts[2])
            func_ctx.add_instruction(f"\tmov: r0 = {src_reg}")
            func_ctx.add_instruction(f"\tbl: {func_name}")
        else:
            func_ctx.add_instruction(f"\tbl: {func_name}")
        func_ctx.arg_count = 0
    
    elif opcode == 'arg':
        if func_ctx.arg_count < len(ARG_REGS):
            # 1. Pega no valor do argumento.
            src_reg = alloc.ensure_var_in_reg(instr_parts[1])
            # 2. Usa o contador (arg_count) para escolher o registrador de destino (r0, r1, ...).
            dest_reg = ARG_REGS[func_ctx.arg_count]
            # 3. Move o argumento para o seu lugar correto.
            func_ctx.add_instruction(f"\tmov: {dest_reg} = {src_reg}")
            # 4. Atualiza o contador para o próximo argumento.
            func_ctx.arg_count += 1
        return  
    
    elif opcode == 'return':
        if len(instr_parts) > 1 and instr_parts[1] != '_':
            reg = alloc.ensure_var_in_reg(instr_parts[1])
            func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['retval']} = {reg}")
        alloc.spill_all_dirty()

    elif opcode == 'if_false': # (Lógica de branch - pode ser melhorada no futuro)
        func_ctx.add_instruction(f"\tbilteq: {instr_parts[3]}")


def generate_assembly(ir_list):
    functions = collections.OrderedDict()
    all_vars = set()
    
    # Coleta todos os nomes de variáveis do código IR.
    for line in ir_list:
        parts = line.strip().split()
        if not parts: continue
        
        # Regex para encontrar todas as palavras que podem ser variáveis,
        # ignorando temporários (t0, t1...), labels (L0, L1...) e palavras-chave.
        variable_pattern = re.compile(r'\b(?!t\d|L\d\b)\b([a-zA-Z_]\w*)\b')
        keywords = {'call', 'goto', 'arg', 'return', 'if_false', 'input', 'output'}
        
        matches = variable_pattern.findall(line)
        for var_name in matches:
            if var_name not in keywords and not (var_name.startswith('t') and var_name[1:].isdigit()):
                all_vars.add(var_name)

        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if not func_name.startswith('L'):
                if func_name not in functions:
                    functions[func_name] = FunctionContext(func_name)

    if not functions and any(ir_list):
        functions['main'] = FunctionContext('main')

    # Processa cada função para gerar seu código assembly
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
        
        # Limpa instruções antigas e traduz a IR para a função atual
        func_ctx.instructions.clear()
        for line in func_ir:
            translate_instruction(line.split(), func_ctx)
        
        # Garante que qualquer variável modificada seja salva no final da função
        func_ctx.allocator.spill_all_dirty()

    # --- Monta o código final ---
    final_code = [".text", ".global main", ""]
    
    for func_name, func_ctx in functions.items():
        final_code.append(f"{func_name}:")
        final_code.extend(func_ctx.instructions)
        final_code.append(f"\tbi: {func_name}_epilogue")
        final_code.append(f"{func_name}_epilogue:")
        final_code.append("\tret:")
        final_code.append("")

    # Secção de dados: declara apenas as variáveis reais do programa
    final_code.append(".data")
    func_names = set(functions.keys())
    # Filtra para declarar apenas variáveis que não são temporárias ('t*') ou nomes de funções.
    # Adicionamos 't' à verificação para garantir que a variável local 't' seja incluída.
    var_names = sorted([var for var in all_vars if var not in func_names and not (var.startswith('t') and var[1:].isdigit())])

    for var in var_names:
        final_code.append(f"var_{var}: .word 0")

    return "\n".join(final_code)