import collections
import re
from symbol_table import Type, IntegerType, ArrayType, Symbol, SymbolTable # <-- ADICIONE ESTA LINHA

IR_TO_ASSEMBLY_BRANCH = {
    # IR op: Assembly branch instruction
    '<': 'bigteq',  # if_false (a < b)  -> branch if (a >= b)
    '<=': 'bigt',   # if_false (a <= b) -> branch if (a > b)
    '>': 'bilteq',  # if_false (a > b)  -> branch if (a <= b)
    '>=': 'bilt',   # if_false (a >= b) -> branch if (a < b)
    '==': 'bineq',  # if_false (a == b) -> branch if (a != b)
    '!=': 'bieq',   # if_false (a != b) -> branch if (a == b)
}

DATA_MEMORY_SIZE = 256 
SPECIAL_REGS = {  'retval': 'r0', 'pseudo': 'r27', 'lr': 'r28', 'sp': 'r29','spill': 'r30', 'fp': 'r31'}
ARG_REGS = ['r1', 'r2', 'r3']

# Contador para alocar regiões únicas de memória para cada chamada de função
CALL_ALLOC_COUNTER = collections.defaultdict(int)

class DataMemoryManager:
    """
    Gerencia alocação de endereços na seção .data para variáveis definidas no IR.
    
    Cada variável recebe um endereço único em memória de dados, com base
    em um ponteiro de base que avança conforme definimos novos símbolos.
    """
    def __init__(self, base_address=0):
        # Endereço inicial da seção de dados (em palavras)
        self.base_address = base_address
        # Próximo offset livre (em palavras)
        self.next_offset = 0
        # Mapeamento de nome de variável -> endereço absoluto
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
        # Avança o ponteiro de offset pelo tamanho da variável
        self.next_offset += size
        return address
    
    def get_address(self, var_name):
        """
        Retorna o endereço previamente registrado de uma variável.
        Levanta KeyError se a variável não tiver sido registrada.
        """
        return self.var_to_address[var_name]
    
    def generate_data_directives(self, symbol_table):
        """
        Gera listas de diretivas .word ou .space para inclusão na seção .data,
        usando a SymbolTable para determinar o tipo de cada variável.
        """
        directives = []
        
        # Filtra apenas os símbolos que são variáveis globais para evitar processar funções, etc.
        global_vars = [s for s in symbol_table.symbols.values() if s.scope == "global" and isinstance(s.type, (IntegerType, ArrayType))]
        
        # Ordena os símbolos pelo seu endereço de memória para manter a ordem no arquivo .data
        sorted_symbols = sorted(global_vars, key=lambda s: s.address)

        for symbol in sorted_symbols:
            if isinstance(symbol.type, ArrayType):
                # Se for um vetor, gera a diretiva .space com o seu tamanho
                directives.append(f"var_{symbol.name}: .space {symbol.type.num_elements}")
            elif isinstance(symbol.type, IntegerType):
                # Se for um inteiro simples, gera a diretiva .word
                # O valor inicial 0 é um padrão seguro.
                directives.append(f"var_{symbol.name}: .word 0")
                
        return directives

class RegisterAllocator:
    """
    Gerencia o uso de registradores de forma inteligente, distinguindo entre
    registradores "caller-saved" (voláteis) e "callee-saved" (preservados).
    """
    def __init__(self, func_context):
        self.func_context = func_context
        print(f"[ALLOC_INIT] Inicializando alocador para a função '{func_context.name}'")

        # Prioriza o uso de registradores Callee-Saved para variáveis locais
        # e Caller-Saved para cálculos rápidos e temporários.
        self.callee_saved_pool = [f"r{i}" for i in range(12, 27)]
        self.caller_saved_pool = [f"r{i}" for i in range(4, 12)]

        self.reg_pool = self.caller_saved_pool + self.callee_saved_pool
        self.SPILL_TEMP_REG = SPECIAL_REGS['spill']  # Registrador para spill temporário 
        print(f"[ALLOC_INIT] Pool de registradores definido: {self.reg_pool}")
        print(f"[ALLOC_INIT] Registrador de spill reservado: {self.SPILL_TEMP_REG}")
        
        # Estruturas para rastrear o estado dos registradores
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
        
        # Se a variável já está em um registrador, apenas o retorna.
        if var_name in self.var_to_reg:
            reg = self.var_to_reg[var_name]
            self._mark_as_used(reg)
            print(f"[ENSURE] -> Sucesso! '{var_name}' já está em {reg}.")
            return reg
        
        # Se foi derramado para a pilha, recupera.
        if var_name in self.spilled_temps:
            reg = self._get_free_reg()
            offset = self.spilled_temps[var_name]
            self.func_context.add_instruction(f"\tloadi: {reg} = [fp, #{offset}]")
            print(f"[ENSURE] -> Recuperando '{var_name}' da pilha [fp, #{offset}] para {reg}.")
            del self.spilled_temps[var_name]
            self._assign_reg_to_var(reg, var_name)
            self.dirty_regs.add(reg)
            return reg

        # Se for uma constante numérica, move o valor para um novo registrador.
        if var_name.isdigit() or (var_name.startswith('-') and var_name[1:].isdigit()):
            reg = self._get_free_reg()
            print(f"[ENSURE] -> Alocando {reg} para a constante '{var_name}'.")
            self.func_context.add_instruction(f"\tmovi: {reg} = {var_name}")
            return reg
        
        if var_name.startswith('t'):
            # Se for uma variável temporária, aloca um novo registrador.
            reg = self.get_reg_for_temp(var_name)
            print(f"[ENSURE] -> Variável temporária '{var_name}' alocada em {reg}.")
            return reg
        
        if var_name in self.func_context.stack_layout:
            print(f"[ENSURE] -> '{var_name}' é uma variável da pilha. Carregando...")
            offset = self.func_context.stack_layout[var_name]
            reg = self._get_free_reg()
            
            # Expande a pseudo-instrução: reg = [fp + offset]
            scratch_reg, fp_reg = self.SPILL_TEMP_REG, SPECIAL_REGS['fp']
            self.func_context.add_instruction(f"\tsubi: {scratch_reg} = {fp_reg}, {-offset}")
            self.func_context.add_instruction(f"\tload: {reg} = [{scratch_reg}]")
            
            self._assign_reg_to_var(reg, var_name)
            return reg
        
        # Se for uma variável real, carrega da memória.
        print(f"[ENSURE] -> Variável '{var_name}' não está em um registrador. Carregando da memória.")
        reg = self._get_free_reg()
        addr_reg = self._get_free_reg()
        
        # Pega nome da variável
        addr = self.func_context.data_manager.get_address(var_name)
        # Coleta endereço da variável para a memória 
        self.func_context.add_instruction(f"\tmovi: {addr_reg} = {addr}")
        print(f"[ENSURE] -> Usando {reg} para o valor e {addr_reg} para o endereço {addr}.")
        
        self.func_context.add_instruction(f"\tload: {reg} = [{addr_reg}]")
        self._assign_reg_to_var(reg, var_name)
        self._unassign_reg(addr_reg) # Libera o registrador de endereço
        return reg
    
    def get_address_in_reg(self, var_name):
        """
        Garante que o ENDEREÇO de uma variável (global ou da pilha)
        esteja em um registrador.
        """
        print(f"[GET_ADDR] Obtendo endereço para '{var_name}'.")
        addr_reg = self._get_free_reg()
        
        if var_name in self.func_context.stack_layout:
            # A variável está na pilha. Seu endereço é "fp + offset".
            offset = self.func_context.stack_layout[var_name]
            fp_reg = SPECIAL_REGS['fp']
            print(f"[GET_ADDR] -> '{var_name}' está na pilha. Calculando endereço [fp, #{offset}].")
            self.func_context.add_instruction(f"\tsubi: {addr_reg} = {fp_reg}, {-offset}")
        else:
            # A variável é global. Pega o endereço do DataManager.
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
        # Lógica de spill aprimorada
        reg_to_spill = None
        # Tenta primeiro encontrar um registrador com uma variável real para derramar
        for reg in self.lru_order:
            var_name = self.reg_to_var.get(reg)
            if var_name and not var_name.startswith('t'):
                reg_to_spill = reg
                break
        
        # Se não encontrou, pega o menos usado recentemente, seja ele qual for
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
                if var_name not in self.func_context.stack_layout:
                    self.func_context.stack_layout[var_name] = self.func_context.next_stack_slot
                    self.func_context.next_stack_slot -= 1 
                
                offset = self.func_context.stack_layout[var_name]
                
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
        self.param_names = []  
        self.local_vars = []
        self.local_stack_size = 0
        self.stack_layout = {}
        self.next_stack_slot = -1
        self.last_comparison = None
        self.last_instr_type = None
        self.label_counter = 0
        print(f"[FUNC_CTX] Contexto para a função '{name}' criado.")

    def add_instruction(self, instruction):
        print(f"[ADD_INSTR] Adicionando instrução para '{self.name}': {instruction.strip()}")
        self.instructions.append(instruction)
    
    def new_label(self, prefix="Lret"):
        label = f"{self.name}_{prefix}{self.label_counter}"
        self.label_counter += 1
        return label

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
        # Se a última instrução já foi um desvio incondicional ou um retorno,
        # este 'goto' provavelmente é redundante e pode ser ignorado.
        if func_ctx.last_instr_type in ['goto', 'return']:
            print(f"[TRANSLATE_SKIP] -> Ignorando 'goto' redundante após um '{func_ctx.last_instr_type}'.")
            return
        
        print(f"[TRANSLATE] -> Desvio incondicional detectado: {instr_parts[1]}")
        alloc.spill_all_dirty()
        func_ctx.add_instruction(f"\tbi: {instr_parts[1]}")
        func_ctx.last_instr_type = 'goto'
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
            
            alloc.free_reg_if_temp(reg1)
            if not (arg2.isdigit() or (arg2.startswith('-') and arg2[1:].isdigit())):
                alloc.free_reg_if_temp(op2_val)
        
        elif expr_parts[0].startswith('&'):
            print("[TRANSLATE] -> Caminho: Obter Endereço (&)")
            var_name = expr_parts[0][1:]
            dest_reg = alloc.get_reg_for_temp(dest)
            addr = func_ctx.data_manager.get_address(var_name)
            func_ctx.add_instruction(f"\tmovi: {dest_reg} = {addr}")

        elif expr_parts[0].startswith('*'):
            print("[TRANSLATE] -> Caminho: Carregar de Ponteiro (*)")
            ptr_name = expr_parts[0][1:] 
            
            addr_reg = None
            # Diferencia o tratamento para temporárias vs. variáveis nomeadas
            if ptr_name.startswith('t'):
                # Se for uma temporária (ex: *t9), ela JÁ contém o endereço.
                # Então, precisamos do VALOR dela em um registrador.
                print(f"[TRANSLATE] -> Ponteiro é uma temporária ('{ptr_name}'). Usando seu valor como endereço.")
                addr_reg = alloc.ensure_var_in_reg(ptr_name)
            else:
                # Se for uma variável nomeada, precisamos buscar o ENDEREÇO dela.
                print(f"[TRANSLATE] -> Ponteiro é uma variável nomeada ('{ptr_name}'). Buscando seu endereço.")
                addr_reg = alloc.get_address_in_reg(ptr_name)
            
            dest_reg = alloc.get_reg_for_temp(dest)
            
            # A instrução de load agora funciona para ambos os casos
            func_ctx.add_instruction(f"\tload: {dest_reg} = [{addr_reg}]")
            
            # Libera o registrador que continha o endereço
            alloc.free_reg_if_temp(addr_reg) 
            
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
            
            alloc._unassign_reg(src_reg) 
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
            if expr_parts[0].startswith('t'):
                alloc.free_reg_if_temp(reg_src)

    elif opcode == 'call':
        print("[TRANSLATE] -> Caminho: Chamada de Procedimento")
        func_name = instr_parts[1].replace(',', '')
        num_args = int(instr_parts[2]) if len(instr_parts) > 2 else 0
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
    data_manager = DataMemoryManager(base_address=int(DATA_MEMORY_SIZE/2))
    
    # --- Etapa 1: Análise Estática ---

    print("\n--- Passagem 1A: Coletando definições de funções ---")
    for line in ir_list:
        parts = line.strip().split()
        if not parts: continue
        if parts[0].endswith(':'):
            func_name = parts[0][:-1]
            if not func_name.startswith('L'):
                if func_name not in functions:
                    print(f"[Passagem 1A] Função encontrada: '{func_name}'")
                    functions[func_name] = FunctionContext(func_name, data_manager)

    if not functions and any(ir_list):
        functions['main'] = FunctionContext('main', data_manager)

    # 1B: Constrói a Tabela de Símbolos para variáveis GLOBAIS.
    print("\n--- Passagem 1B: Construindo a Tabela de Símbolos Globais ---")
    symbol_table = SymbolTable()

    # Itera sobre a IR para encontrar todas as declarações de dados globais.
    for line in ir_list:
        # Pula linhas que não são de atribuição/declaração
        if ':=' not in line:
            continue

        # Separa o nome da variável do resto da instrução
        parts = [p.strip() for p in line.strip().split(':=', 1)]
        var_name = parts[0]
        declaration_part = parts[1]

        # Verifica se é uma diretiva de declaração (.space ou .word)
        if '.space' in declaration_part or '.word' in declaration_part:
            # Separa a diretiva do tamanho
            decl_parts = [p.strip() for p in declaration_part.split(',')]
            directive = decl_parts[0]
            size_str = decl_parts[1]
            
            # Garante que estamos processando apenas globais (não dentro de uma função)
            is_global = True
            for func_name in functions:
                if f'{func_name}:' in ir_list[:ir_list.index(line)]:
                    is_global = False
                    break
            if not is_global: continue

            symbol_type = None
            allocated_size = 1 # Padrão para .word

            if directive == '.space':
                array_size = int(size_str)
                print(f"[Passagem 1B] Declaração de Vetor Global encontrada: '{var_name}' de tamanho {array_size}")
                symbol_type = ArrayType(IntegerType(), array_size)
                allocated_size = symbol_type.size
            elif directive == '.word':
                print(f"[Passagem 1B] Declaração de Inteiro Global encontrada: '{var_name}'")
                symbol_type = IntegerType()
            
            if symbol_type:
                addr = data_manager.register_variable(var_name, size=allocated_size)
                symbol = Symbol(var_name, symbol_type, "global", address=addr)
                symbol_table.add_symbol(symbol)
    
    print(f"--- Fim da Passagem 1: {len(symbol_table.symbols)} símbolos globais encontrados. ---\n")

    # --- Etapa 2: Geração de Código para cada função ---
    print("--- Passagem 2: Traduzindo o IR para cada função ---")
    for func_name, func_ctx in functions.items():
        print(f"\n[Processando Função] -> '{func_name}'")
        func_ir = []
        in_func = False
        for line in ir_list:
            stripped = line.strip()
            if not stripped: continue
            if stripped.startswith(func_name + ':'): in_func = True; continue
            if stripped.endswith(':') and not stripped.startswith('L'):
                if stripped[:-1] in functions and stripped[:-1] != func_name: in_func = False
            if in_func: func_ir.append(stripped)
        
        print(f"-> IR isolado para '{func_name}' contém {len(func_ir)} instruções.")
        
        # 2A: Descobre parâmetros e variáveis locais da função
        defined_vars = set()
        all_vars_in_func = set()
        var_pattern = re.compile(r'\b([a-zA-Z_]\w*)\b')

        for line in func_ir:
            if ':=' in line:
                dest = line.split(':=')[0].strip()
                dest_var = re.sub(r'^\*', '', dest).strip()
                if not dest_var.startswith('t'):
                    defined_vars.add(dest_var)
            
            matches = var_pattern.findall(line)
            for var in matches:
                if var not in functions and not var.startswith('t') and var not in ['if_false', 'goto', 'call', 'arg', 'return']:
                    all_vars_in_func.add(var)

        func_ctx.param_names = [var for var in all_vars_in_func if var not in defined_vars]
        print(f"--> Parâmetros para '{func_name}': {func_ctx.param_names}")

        local_vars = {var for var in all_vars_in_func if var not in func_ctx.param_names and not symbol_table.get_symbol(var)}
        func_ctx.local_vars = list(local_vars)
        print(f"--> Variáveis Locais para '{func_name}': {func_ctx.local_vars}")

        # 2B: Atribui um offset na pilha para cada parâmetro e variável local
        print(f"--> Criando o layout da pilha para '{func_name}'...")
        current_offset = -1
        for var_name in (func_ctx.param_names + func_ctx.local_vars):
            if var_name not in func_ctx.stack_layout:
                func_ctx.stack_layout[var_name] = current_offset
                print(f"    -> Mapeando '{var_name}' para o offset [fp, #{current_offset}]")
                current_offset -= 1
                
        # 2C: Calcula o tamanho total do frame (parâmetros + locais + temporários)
        all_stack_vars = set()
        for line in func_ir:
            matches = re.findall(r'\b(t\d+)\b', line)
            for var in matches: all_stack_vars.add(var)
        
        all_stack_vars.update(func_ctx.param_names)
        all_stack_vars.update(func_ctx.local_vars)
            
        func_ctx.local_stack_size = len(all_stack_vars)
        print(f"--> Tamanho total do frame para '{func_name}': {func_ctx.local_stack_size} palavras.")
        
        # Inicia a geração de código
        func_ctx.instructions.clear()
        
        # Gera o código para salvar os parâmetros na pilha
        for idx, param_name in enumerate(func_ctx.param_names):
            if idx < len(ARG_REGS):
                arg_reg = ARG_REGS[idx]
                offset = func_ctx.stack_layout[param_name]
                scratch_reg, fp_reg = SPECIAL_REGS['spill'], SPECIAL_REGS['fp']
                
                func_ctx.add_instruction(f"\tsubi: {scratch_reg} = {fp_reg}, {-offset}")
                func_ctx.add_instruction(f"\tstore: [{scratch_reg}] = {arg_reg}")
        
        # Traduz o resto do corpo da função a partir do IR
        for line in func_ir:
            translate_instruction(line.split(), func_ctx)
        
        print(f"-> Finalizando a função '{func_name}', fazendo spill de todos os registradores sujos.")
        func_ctx.allocator.spill_all_dirty()
    print("--- Fim da Passagem 2 ---\n")

    # --- Etapa 3: Montagem Final ---
    print("--- Montagem Final: Construindo o arquivo assembly completo ---")
    final_code = [".text", ".global main", ""]
    first_func = True
    for func_name, func_ctx in functions.items():
        print(f"[Montagem] Processando função '{func_name}' com {len(func_ctx.instructions)} instruções.")
        
        if first_func:
            final_code.append(f"\tbi: main")
            first_func = False
            
        final_code.append(f"{func_name}:")
        
        if func_name == 'main':
            final_code.append(f"\tmovi: {SPECIAL_REGS['sp']} = {DATA_MEMORY_SIZE - 1}")
            final_code.append(f"\tmov: {SPECIAL_REGS['fp']} = {SPECIAL_REGS['sp']}")
        else:
            final_code.append(f"\tsubi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, 1") 
            final_code.append(f"\tstore: [{SPECIAL_REGS['sp']}] = {SPECIAL_REGS['lr']}") 
            final_code.append(f"\tsubi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, 1")
            final_code.append(f"\tstore: [{SPECIAL_REGS['sp']}] = {SPECIAL_REGS['fp']}")
            final_code.append(f"\tmov: {SPECIAL_REGS['fp']} = {SPECIAL_REGS['sp']}")
        
        if func_ctx.local_stack_size > 0:
            final_code.append(f"\tsubi: {SPECIAL_REGS['sp']} = {SPECIAL_REGS['sp']}, {func_ctx.local_stack_size}")
        
        final_code.extend(func_ctx.instructions)
        
        if not func_ctx.instructions or func_ctx.instructions[-1].strip() != f"bi: {func_name}_epilogue":
            final_code.append(f"\tbi: {func_name}_epilogue")
        
        final_code.append(f"{func_name}_epilogue:")
        if func_name != 'main':
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
    directives = data_manager.generate_data_directives(symbol_table)
    print(f"[Montagem] -> Variáveis a serem declaradas: {[s.name for s in symbol_table.symbols.values()]}")
    final_code.extend(directives)
    
    print("=== GERAÇÃO DE ASSEMBLY CONCLUÍDA ===")
    return "\n".join(final_code)