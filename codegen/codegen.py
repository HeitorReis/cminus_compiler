import collections
import re

IR_TO_ASSEMBLY_BRANCH = {

    '<': 'bigteq',
    '<=': 'bigt',
    '>': 'bilteq',
    '>=': 'bilt',
    '==': 'bineq',
    '!=': 'bieq',
}

LINK_STACK_SIZE = 32
DATA_MEMORY_SIZE = 64

SPECIAL_REGS = {  'retval': 'r0', 'pseudo': 'r27', 'lr': 'r28', 'sp': 'r29','spill': 'r30', 'fp': 'r31'}

ARG_REGS = ['r1', 'r2', 'r3']


FUNCTION_PARAM_MAP = {}

class DataMemoryManager:
    """
    Gerencia alocação de endereços na seção .data para variáveis definidas no IR.

    Cada variável recebe um endereço único em memória de dados, com base
    em um ponteiro de base que avança conforme definimos novos símbolos.
    """
    def __init__(self, base_address=0):

        self.base_address = base_address

        self.next_offset = 0

        self.var_to_address = {}

    def register_variable(self, var_name, size=1):
        """
        Registra uma variável na seção de dados.

        :param var_name: Nome simbólico da variável (string).
        :param size: Número de palavras ocupadas por esta variável.
        :return: Endereço (int) onde a variável começa.
        """
        if var_name in self.var_to_address:
            return self.var_to_address[var_name]

        address = self.base_address + self.next_offset
        self.var_to_address[var_name] = address

        self.next_offset += size
        return address

    def get_address(self, var_name):
        """
        Retorna o endereço previamente registrado de uma variável.
        Levanta KeyError se a variável não tiver sido registrada.
        """
        return self.var_to_address[var_name]

    def generate_data_directives(self):
        """
        Gera listas de diretivas .word ou .space para inclusão na seção .data.
        Exemplo: ['var_x: .word 0', 'var_arr: .space 4']
        """
        directives = []
        for name, addr in sorted(self.var_to_address.items(), key=lambda kv: kv[1]):

            directives.append(f"var_{name}: .word {addr}")
        return directives

class RegisterAllocator:
    """
    Gerencia o uso de registradores de forma inteligente, distinguindo entre
    registradores "caller-saved" (voláteis) e "callee-saved" (preservados).
    """
    def __init__(self, func_context):
        self.func_context = func_context
        print(f"[ALLOC_INIT] Inicializando alocador para a função '{func_context.name}'")



        self.callee_saved_pool = [f"r{i}" for i in range(12, 27)]
        self.caller_saved_pool = [f"r{i}" for i in range(4, 12)]

        self.reg_pool = self.callee_saved_pool + self.caller_saved_pool
        self.SPILL_TEMP_REG = SPECIAL_REGS['spill']
        print(f"[ALLOC_INIT] Pool de registradores definido: {self.reg_pool}")
        print(f"[ALLOC_INIT] Registrador de spill reservado: {self.SPILL_TEMP_REG}")


        self.free_regs = collections.deque(self.reg_pool.copy())
        self.var_to_reg = {}
        self.reg_to_var = {}
        self.lru_order = collections.deque()
        self.dirty_regs = set()
        self.spilled_temps = {}
        print(f"[ALLOC_INIT] Estado inicial: {len(self.free_regs)} registradores livres.")

    def ensure_var_in_reg(self, var_name):
        """
        Garante que uma variável do código-fonte (como 'x') ou uma constante
        esteja carregada em um registrador.
        """
        print(f"[ENSURE] Tentando garantir '{var_name}' em um registrador.")


        if var_name in self.var_to_reg:
            reg = self.var_to_reg[var_name]
            self._mark_as_used(reg)
            print(f"[ENSURE] -> Sucesso! '{var_name}' já está em {reg}.")
            return reg


        if var_name in self.spilled_temps:
            reg = self._get_free_reg()
            offset = self.spilled_temps[var_name]
            self.func_context.add_instruction(f"\tloadi: {reg} = [fp, #{offset}]")
            print(f"[ENSURE] -> Recuperando '{var_name}' da pilha [fp, #{offset}] para {reg}.")
            del self.spilled_temps[var_name]
            self._assign_reg_to_var(reg, var_name)
            self.dirty_regs.add(reg)
            return reg


        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
            reg = self._get_free_reg()
            print(f"[ENSURE] -> Alocando {reg} para a constante '{var_name}'.")
            self.func_context.add_instruction(f"\tmovi: {reg} = {var_name}")
            return reg

        if var_name.startswith('t'):

            reg = self.get_reg_for_temp(var_name)
            print(f"[ENSURE] -> Variável temporária '{var_name}' alocada em {reg}.")
            return reg


        print(f"[ENSURE] -> Variável '{var_name}' não está em um registrador. Carregando da memória.")
        reg = self._get_free_reg()
        addr_reg = self._get_free_reg()


        addr = self.func_context.data_manager.get_address(var_name)

        self.func_context.add_instruction(f"\tmovi: {addr_reg} = {addr}")
        print(f"[ENSURE] -> Usando {reg} para o valor e {addr_reg} para o endereço {addr}.")

        self.func_context.add_instruction(f"\tload: {reg} = [{addr_reg}]")
        self._assign_reg_to_var(reg, var_name)
        self._unassign_reg(addr_reg)
        return reg

    def get_address_in_reg(self, var_name):
        """
        Garante que o ENDEREÇO de uma variável esteja em um registrador.
        """
        print(f"[GET_ADDR] Obtendo endereço para '{var_name}'.")
        addr_reg = self._get_free_reg()
        addr = self.func_context.data_manager.get_address(var_name)
        self.func_context.add_instruction(f"\tmovi: {addr_reg} = {addr}")
        print(f"[GET_ADDR] -> Endereço de '{var_name}' ({addr}) carregado em {addr_reg}.")
        return addr_reg

    def get_reg_for_temp(self, temp_name):
        """
        Aloca um registrador para uma nova variável temporária (ex: 't2').
        """
        print(f"[GET_TEMP] Solicitando registrador para o temporário '{temp_name}'.")
        reg = self._get_free_reg()
        self._assign_reg_to_var(reg, temp_name)
        self.dirty_regs.add(reg)
        print(f"[GET_TEMP] -> '{temp_name}' alocado no registrador {reg}.")
        return reg

    def free_reg_if_temp(self, reg):
        """
        Libera um registrador se ele contiver uma temporária.
        """
        var_name = self.reg_to_var.get(reg)
        if var_name and var_name.startswith('t'):
            print(f"[FREE_TEMP] Liberando registrador {reg} que continha o temporário '{var_name}'.")
            self._unassign_reg(reg)

    def update_var_from_reg(self, dest_var, src_reg):
        """
        Atualiza o mapeamento para refletir uma atribuição (mov).
        """
        print(f"[UPDATE_MAP] Mapeando '{dest_var}' para o registrador {src_reg} (que contém o valor de origem).")
        self._assign_reg_to_var(src_reg, dest_var)

    def spill_all_dirty(self):
        """
        Força o salvamento de todas as variáveis "reais" antes de chamadas de função.
        """
        print(f"[SPILL_ALL] Verificando registradores sujos para salvar antes da chamada de função. Sujos: {self.dirty_regs}")
        for reg in list(self.dirty_regs):
            var_name = self.reg_to_var.get(reg)
            if var_name and not var_name.startswith('t'):
                addr_reg = self.SPILL_TEMP_REG
                addr = self.func_context.data_manager.get_address(var_name)
                print(f"[SPILL_ALL] -> Salvando variável real '{var_name}' do registrador {reg} na memória.")
                self.func_context.add_instruction(f"\tmovi: {addr_reg} = {addr}")
                self.func_context.add_instruction(f"\tstore: [{addr_reg}] = {reg}")
                self.dirty_regs.discard(reg)

    def invalidate_vars(self, var_names):
        """Remove o mapeamento de registradores para as variáveis fornecidas."""
        for var in var_names:
            if var in self.var_to_reg:
                reg = self.var_to_reg[var]
                self._unassign_reg(reg)
                self.dirty_regs.discard(reg)

    def _get_free_reg(self):
        """
        Obtém um registrador livre ou derrama um, se necessário.
        """
        if self.free_regs:
            reg = self.free_regs.popleft()
            self._mark_as_used(reg)
            print(f"[GET_FREE] -> Encontrado registrador livre: {reg}. Restantes: {len(self.free_regs)}.")
            return reg

        print("[GET_FREE] -> Nenhum registrador livre. Iniciando processo de spill.")

        reg_to_spill = None

        for reg in self.lru_order:
            var_name = self.reg_to_var.get(reg)
            if var_name and not var_name.startswith('t'):
                reg_to_spill = reg
                break


        if reg_to_spill is None:
            if self.lru_order:
                reg_to_spill = self.lru_order[0]
                print(f"[GET_FREE] -> Nenhum candidato ideal para spill. Forçando o spill do menos usado: {reg_to_spill}.")
            else:
                raise Exception("Erro de alocação: LRU vazia e sem registradores livres. Impossível continuar.")

        self._spill_reg(reg_to_spill)
        self._mark_as_used(reg_to_spill)
        return reg_to_spill

    def _spill_reg(self, reg):
        """ Salva um registrador na memória (se for variável) ou na pilha (se for temporário). """
        var_name = self.reg_to_var.get(reg)
        if not var_name:
            print(f"[SPILL] Registrador {reg} não tinha variável mapeada. Apenas liberando.")
            self._unassign_reg(reg)
            return

        print(f"[SPILL] Derramando registrador {reg}, que contém '{var_name}'.")

        if reg in self.dirty_regs:
            if not var_name.startswith('t'):
                addr_reg = self.SPILL_TEMP_REG
                addr = self.func_context.data_manager.get_address(var_name)
                print(f"[SPILL] -> '{var_name}' é uma variável real. Salvando em .data.")
                self.func_context.add_instruction(f"\tmovi: {addr_reg} = {addr}")
                self.func_context.add_instruction(f"\tstore: [{addr_reg}] = {reg}")
            else:
                self.func_context.spill_offset -= 4
                offset = self.func_context.spill_offset
                self.spilled_temps[var_name] = offset
                print(f"[SPILL] -> '{var_name}' é um temporário. Salvando na pilha em [fp, #{offset}].")
                self.func_context.add_instruction(f"\tstorei: [fp, #{offset}] = {reg}")
            

            self.dirty_regs.discard(reg)
        else:
            print(f"[SPILL] -> Registrador {reg} não estava 'sujo'. Nenhum valor foi salvo.")

        self._unassign_reg(reg)

    def _assign_reg_to_var(self, reg, var_name):
        """ Cria um novo mapeamento entre um registrador e uma variável. """
        print(f"[ASSIGN_REG] Mapeando '{var_name}' para {reg}.")
        if var_name in self.var_to_reg and self.var_to_reg[var_name] != reg:
            old_reg = self.var_to_reg[var_name]
            print(f"[ASSIGN_REG] -> Variável '{var_name}' já estava em {old_reg}. Liberando o mapeamento antigo.")
            self._unassign_reg(old_reg)

        if reg in self.reg_to_var and self.reg_to_var[reg] != var_name:
            old_var = self.reg_to_var[reg]
            print(f"[ASSIGN_REG] -> Registrador {reg} já continha '{old_var}'. Liberando o mapeamento antigo.")
            self._unassign_reg(reg)

        self.var_to_reg[var_name] = reg
        self.reg_to_var[reg] = var_name
        self._mark_as_used(reg)

    def _unassign_reg(self, reg):
        """ Remove todos os mapeamentos de um registrador e o devolve à lista de livres. """
        if reg in self.reg_to_var:
            var_name = self.reg_to_var.pop(reg)
            if var_name in self.var_to_reg:
                del self.var_to_reg[var_name]
            print(f"[UNASSIGN_REG] Desmapeado {reg} de '{var_name}'.")
        else:
            print(f"[UNASSIGN_REG] {reg} já estava desmapeado.")

        if reg not in self.free_regs:
            self.free_regs.append(reg)
        if reg in self.lru_order:
            self.lru_order.remove(reg)
        print(f"[UNASSIGN_REG] -> Estado atual: {len(self.free_regs)} registradores livres. Mapeamentos: {self.var_to_reg}")

    def _mark_as_used(self, reg):
        """ Marca um registrador como o mais recentemente usado. """
        if reg in self.lru_order:
            self.lru_order.remove(reg)
        self.lru_order.append(reg)

class FunctionContext:
    def __init__(self, name, data_manager):
        self.name = name
        self.instructions = []
        self.data_manager = data_manager
        self.allocator = RegisterAllocator(self)
        self.arg_count = 0
        self.arg_vars = []
        self.spill_offset = 0
        self.last_comparison = None
        self.label_counter = 0
        print(f"[FUNC_CTX] Contexto para a função '{name}' criado.")

    def add_instruction(self, instruction):
        print(f"[ADD_INSTR] Adicionando instrução para '{self.name}': {instruction.strip()}")
        self.instructions.append(instruction)

    def new_label(self, prefix="Lret"):
        label = f"{self.name}_{prefix}{self.label_counter}"
        self.label_counter += 1
        return label

def _initialize_call_args(func_ctx, func_name, num_args):
    """Salva cada registrador de argumento no local de memória do parâmetro correspondente."""
    param_list = FUNCTION_PARAM_MAP.get(func_name, [])
    for idx in range(num_args):
        param_name = param_list[idx] if idx < len(param_list) else None
        if not param_name or param_name not in func_ctx.data_manager.var_to_address:
            continue
        addr_reg = func_ctx.allocator.get_address_in_reg(param_name)
        if idx < len(ARG_REGS):
            src_reg = ARG_REGS[idx]
            func_ctx.add_instruction(f"\tstore: [{addr_reg}] = {src_reg}")
        func_ctx.allocator._unassign_reg(addr_reg)

IR_BRANCH_COND = {'>': 'bigt', '<': 'bilt', '==': 'bieq', '!=': 'bineq', '>=': 'bigteq', '<=': 'bilteq'}

def translate_instruction(instr_parts, func_ctx):
    """
    Trabalha com o novo RegisterAllocator para traduzir uma única linha de IR
    para um assembly mais eficiente e conceitualmente correto.
    """
    print(f"\n--- [TRANSLATE] Processando IR: {' '.join(instr_parts)} ---")
    alloc = func_ctx.allocator
    opcode = instr_parts[0]

    if opcode.endswith(':'):
        print(f"[TRANSLATE] -> Rótulo detectado: {opcode}")
        alloc.spill_all_dirty()
        func_ctx.add_instruction(opcode)
        return

    if opcode == 'goto':
        print(f"[TRANSLATE] -> Desvio incondicional detectado: {instr_parts[1]}")
        alloc.spill_all_dirty()
        func_ctx.add_instruction(f"\tbi: {instr_parts[1]}")
        return

    if ':=' in instr_parts:
        dest, _, *expr_parts = instr_parts
        print(f"[TRANSLATE] -> Detalhes: Destino='{dest}', Expressão='{' '.join(expr_parts)}'")

        if len(expr_parts) > 1 and expr_parts[1] in ['<', '<=', '>', '>=', '==', '!=']:
            print("[TRANSLATE] -> Caminho: Comparação (condicional)")

            arg1, op_str, arg2 = expr_parts

            reg1 = alloc.ensure_var_in_reg(arg1)
            reg2 = alloc.ensure_var_in_reg(arg2)

            func_ctx.add_instruction(f"\tsubs: r0 = {reg1}, {reg2}")

            func_ctx.last_comparison = op_str

            return

        elif len(expr_parts) > 1 and expr_parts[1] in ['+', '-', '*', '/']:
            print("[TRANSLATE] -> Caminho: Operação Aritmética")
            op_map = {
                '+': 'add', '-': 'sub', '*': 'mul', '/': 'div',
                '<': 'slt', '<=': 'sle', '>': 'sgt', '>=': 'sge',
                '==': 'seq', '!=': 'sne'
            }
            arg1, op_str, arg2 = expr_parts
            reg1 = alloc.ensure_var_in_reg(arg1)
            assembly_op = op_map[op_str]

            if arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit()):
                assembly_op += 'i'
                op2_val = arg2
                print(f"[TRANSLATE] -> Operando 2 é um imediato: {op2_val}")
            else:
                op2_val = alloc.ensure_var_in_reg(arg2)

            dest_reg = alloc.get_reg_for_temp(dest)
            func_ctx.add_instruction(f"\t{assembly_op}: {dest_reg} = {reg1}, {op2_val}")

        elif expr_parts[0].startswith('&'):
            print("[TRANSLATE] -> Caminho: Obter Endereço (&)")
            var_name = expr_parts[0][1:]
            dest_reg = alloc.get_reg_for_temp(dest)
            addr = func_ctx.data_manager.get_address(var_name)
            func_ctx.add_instruction(f"\tmovi: {dest_reg} = {addr}")

        elif expr_parts[0].startswith('*'):
            print("[TRANSLATE] -> Caminho: Carregar de Ponteiro (*)")
            var_name_to_load_from = expr_parts[0][1:]

            src_reg_with_value = alloc.ensure_var_in_reg(var_name_to_load_from)

            alloc.update_var_from_reg(dest, src_reg_with_value)

            print(f"[TRANSLATE] -> Valor de '{var_name_to_load_from}' agora em {src_reg_with_value}, mapeado para '{dest}'.")

        elif dest.startswith('*'):
            print("[TRANSLATE] -> Caminho: Armazenar em Ponteiro (*)")
            addr_var_name = dest[1:]
            value_to_store = expr_parts[0]

            src_reg = alloc.ensure_var_in_reg(value_to_store)

            if addr_var_name.startswith('t'):
                print("[TRANSLATE] -> Endereço de destino é uma variável temporária. Usando registrador temporário.")
                addr_reg = alloc.ensure_var_in_reg(addr_var_name)
            else:
                print("[TRANSLATE] -> Endereço de destino é uma variável real. Obtendo endereço em registrador.")
                addr_reg = alloc.get_address_in_reg(addr_var_name)

            func_ctx.add_instruction(f"\tstore: [{addr_reg}] = {src_reg}")

            alloc.free_reg_if_temp(src_reg)
            alloc._unassign_reg(addr_reg)

        elif 'call' in expr_parts:
            print("[TRANSLATE] -> Caminho: Chamada de Função com Retorno")
            func_name = expr_parts[1].replace(',', '')

            alloc.spill_all_dirty()

            if func_name == 'input':
                dest_reg = alloc.get_reg_for_temp(dest)
                func_ctx.add_instruction(f"\tin: {dest_reg}")
            elif func_name == 'output':
                hit_reg = expr_parts[1].split(',', 1)[1]
                print(f"[TRANSLATE] -> Função chamada: {func_name}, argumento: {hit_reg}")
                print(f"[TRANSLATE] -> Chamada de função 'output' detectada. Registrador a ser retornado: {hit_reg}.")
                func_ctx.add_instruction(f"\tout: {hit_reg}")
            else:
                return_label = func_ctx.new_label()
                ret_reg = alloc.get_reg_for_temp(f"t_ret_{len(func_ctx.instructions)}")
                _initialize_call_args(func_ctx, func_name, int(expr_parts[2]))
                func_ctx.add_instruction(f"\tmovi: {ret_reg} = {return_label}")
                func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['lr']} = {ret_reg}")
                func_ctx.add_instruction(f"\tbl: {func_name}")
                alloc.free_reg_if_temp(ret_reg)
                func_ctx.add_instruction(f"{return_label}:")
                dest_reg = alloc.get_reg_for_temp(dest)
                func_ctx.add_instruction(f"\tmov: {dest_reg} = {SPECIAL_REGS['retval']}")
            alloc.invalidate_vars(func_ctx.arg_vars)
            func_ctx.arg_vars.clear()
            func_ctx.arg_count = 0

        elif opcode == "if_false":
            print(f"[TRANSLATE] -> Caminho: Desvio Condicional (if_false)")
            target_label = instr_parts[3]

            if not hasattr(func_ctx, 'last_comparison'):
                print("[TRANSLATE_ERROR] -> 'if_false' sem comparação prévia!")
                return

            original_op = func_ctx.last_comparison
            branch_instruction = IR_TO_ASSEMBLY_BRANCH[original_op]

            func_ctx.add_instruction(f"\t{branch_instruction}: {target_label}")

            del func_ctx.last_comparison
            return


        else:
            print("[TRANSLATE] -> Caminho: Atribuição Simples (mov)")
            reg_src = alloc.ensure_var_in_reg(expr_parts[0])
            alloc.update_var_from_reg(dest, reg_src)

    elif opcode == 'call':
        print("[TRANSLATE] -> Caminho: Chamada de Procedimento")
        func_name = instr_parts[1].replace(',', '')
        num_args = int(instr_parts[2]) if len(instr_parts) > 2 else 0
        _initialize_call_args(func_ctx, func_name, num_args)
        alloc.spill_all_dirty()
        if func_name == 'output':
            output_reg = ARG_REGS[0]

            func_ctx.add_instruction(f"\tout: {output_reg}")
        else:
            return_label = func_ctx.new_label()
            func_ctx.add_instruction(f"\tmovi: {SPECIAL_REGS['lr']} = {return_label}")
            func_ctx.add_instruction(f"\tbl: {func_name}")
            func_ctx.add_instruction(f"{return_label}:")
        alloc.invalidate_vars(func_ctx.arg_vars)
        func_ctx.arg_vars.clear()
        func_ctx.arg_count = 0


    elif opcode == 'arg':
        print(f"[TRANSLATE] -> Caminho: Passagem de Argumento (arg {func_ctx.arg_count+1})")
        if func_ctx.arg_count < len(ARG_REGS):
            src_reg = alloc.ensure_var_in_reg(instr_parts[1])
            dest_reg = ARG_REGS[func_ctx.arg_count]
            func_ctx.add_instruction(f"\tmov: {dest_reg} = {src_reg}")
            func_ctx.arg_vars.append(instr_parts[1])
            func_ctx.arg_count += 1
        else:
            print(f"[TRANSLATE_WARN] -> Aviso: Mais de {len(ARG_REGS)} argumentos. Passagem pela pilha não implementada.")
        return

    elif opcode == 'return':
        print("[TRANSLATE] -> Caminho: Retorno de Função")
        if len(instr_parts) > 1 and instr_parts[1] != '_':
            reg = alloc.ensure_var_in_reg(instr_parts[1])
            func_ctx.add_instruction(f"\tmov: {SPECIAL_REGS['retval']} = {reg}")
        alloc.spill_all_dirty()
        func_ctx.add_instruction(f"\tbi: {func_ctx.name}_epilogue")
        return

    elif opcode == 'if_false':
        print(f"[TRANSLATE] -> Caminho: Desvio Condicional (if_false)")
        target_label = instr_parts[3]

        if not hasattr(func_ctx, 'last_comparison'):
            print("[TRANSLATE_ERROR] -> 'if_false' sem comparação prévia!")
            return

        original_op = func_ctx.last_comparison
        branch_instruction = IR_TO_ASSEMBLY_BRANCH[original_op]

        func_ctx.add_instruction(f"\t{branch_instruction}: {target_label}")

        del func_ctx.last_comparison
        return

def generate_assembly(ir_list):
    print("\n\n=== INICIANDO GERAÇÃO DE ASSEMBLY ===")
    functions = collections.OrderedDict()
    all_vars = set()
    data_manager = DataMemoryManager(base_address=int(DATA_MEMORY_SIZE/2))

    print("\n--- Passagem 1: Coletando funções e variáveis globais do IR ---")
    for i, line in enumerate(ir_list):
        parts = line.strip().split()
        if not parts: continue

        variable_pattern = re.compile(r'\b(?!t\d+\b|L\d+\b)([a-zA-Z_]\w*)\b')
        keywords = {'call', 'goto', 'arg', 'return', 'if_false', 'input', 'output'}
        matches = variable_pattern.findall(line)
        for var_name in matches:
            if var_name not in keywords and not (var_name.startswith('t') and var_name[1:].isdigit()):
                if var_name not in all_vars:
                    print(f"[Passagem 1] Variável global encontrada: '{var_name}' na linha {i+1}")
                    all_vars.add(var_name)

        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if not func_name.startswith('L'):
                if func_name not in functions:
                    print(f"[Passagem 1] Função encontrada: '{func_name}'")
                    functions[func_name] = FunctionContext(func_name, data_manager)

    if not functions and any(ir_list):
        print("[Passagem 1] Nenhuma função explícita encontrada. Assumindo função 'main'.")
        functions['main'] = FunctionContext('main', data_manager)


    for var in all_vars:
        if var not in functions and not (var.startswith('t') and var[1:].isdigit()):
            data_manager.register_variable(var)
    print(f"--- Fim da Passagem 1: {len(functions)} funções e {len(all_vars)} variáveis encontradas. ---\n")


    keywords = {'call', 'goto', 'arg', 'return', 'if_false', 'input', 'output', '_'}
    func_names = set(functions.keys())
    for func_name in functions:
        in_func = False
        func_ir = []
        for line in ir_list:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(func_name + ':'):
                in_func = True
                continue
            if stripped.endswith(':') and not stripped.startswith('L'):
                if stripped[:-1] in functions and stripped[:-1] != func_name:
                    in_func = False
            if in_func:
                func_ir.append(stripped)

        order = []
        defined = set()
        seen = set()
        for l in func_ir:
            if ':=' in l:
                dest = l.split(':=')[0].strip()
                dest_var = re.sub(r'^\*', '', dest).strip()
                if dest_var and not dest_var.startswith('t') and dest_var not in keywords and dest_var not in func_names:
                    defined.add(dest_var)
            tokens = re.findall(r'\b(?!t\d+\b|L\d+\b)([a-zA-Z_]\w*)\b', l)
            for t in tokens:
                if t in keywords or t in func_names or t == func_name:
                    continue
                if t not in seen:
                    seen.add(t)
                    order.append(t)
        params = [v for v in order if v not in defined]
        functions[func_name].param_names = params
        FUNCTION_PARAM_MAP[func_name] = params

    print("--- Passagem 2: Traduzindo o IR para cada função ---")
    for func_name, func_ctx in functions.items():
        print(f"\n[Processando Função] -> '{func_name}'")
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

        print(f"-> IR isolado para '{func_name}' contém {len(func_ir)} instruções.")

        func_ctx.instructions.clear()
        for line in func_ir:
            translate_instruction(line.split(), func_ctx)

        print(f"-> Finalizando a função '{func_name}', fazendo spill de todos os registradores sujos.")
        func_ctx.allocator.spill_all_dirty()
    print("--- Fim da Passagem 2 ---\n")

    print("--- Montagem Final: Construindo o arquivo assembly completo ---")
    final_code = [".text", ".global main", ""]
    first_func = True
    for func_name, func_ctx in functions.items():
        print(f"[Montagem] Processando função '{func_name}' com {len(func_ctx.instructions)} instruções.")

        if first_func:
            print("[Montagem] Adicionando código de inicialização (ida para a função 'main').")
            first_func = False
            final_code.append(f"\tbi: main")

        print(f"[Montagem] Adicionando código para a função '{func_name}'.")
        final_code.append(f"{func_name}:")

        if len(functions.values()) > 1:
            if func_name == 'main':
                final_code.append(f"\tmovi: {SPECIAL_REGS['sp']} = stack_space")


                final_code.append(f"\tmov: {SPECIAL_REGS['fp']} = {SPECIAL_REGS['sp']}")
            else:



                final_code.append(f"\tsubi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, 1")

                final_code.append(f"\tstore: [{SPECIAL_REGS['sp']}] = {SPECIAL_REGS['lr']}")

                final_code.append(f"\tsubi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, 1")

                final_code.append(f"\tstore: [{SPECIAL_REGS['sp']}] = {SPECIAL_REGS['fp']}")


                final_code.append(f"\tmov: {SPECIAL_REGS['fp']} = {SPECIAL_REGS['sp']}")

        final_code.extend(func_ctx.instructions)

        if not func_ctx.instructions or func_ctx.instructions[-1].strip() != f"bi: {func_name}_epilogue":
            final_code.append(f"\tbi: {func_name}_epilogue")

        final_code.append(f"{func_name}_epilogue:")

        if len(functions.values()) > 1:


            final_code.append(f"\tmov: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['fp']}")

            final_code.append(f"\tload: {SPECIAL_REGS['fp']} = [{SPECIAL_REGS['sp']}]")

            final_code.append(f"\taddi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, 1")

            final_code.append(f"\tload: {SPECIAL_REGS['lr']} = [{SPECIAL_REGS['sp']}]")

            final_code.append(f"\taddi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, 1")

        if func_name == 'main':
            final_code.append("\tret:")
        else:
            final_code.append(f"\tb: {SPECIAL_REGS['lr']}")

        final_code.append("")

    print("[Montagem] Adicionando a seção .data.")
    final_code.append(".data")
    final_code.append(f"stack_space: .space {DATA_MEMORY_SIZE}")
    directives = data_manager.generate_data_directives()
    print(f"[Montagem] -> Variáveis a serem declaradas: {list(data_manager.var_to_address.keys())}")
    final_code.extend(directives)

    print("=== GERAÇÃO DE ASSEMBLY CONCLUÍDA ===")
    return "\n".join(final_code)
