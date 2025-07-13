# codegen/codegen.py

class RegisterAllocator:
    """
    Gerencia o mapeamento de variáveis temporárias do IR (t0, t1, ...)
    para registradores físicos do processador (r0, r1, ...).
    Também trata variáveis nomeadas (x, y) como endereços de memória.
    """
    def __init__(self):
        self.temp_to_reg_map = {}
        self.next_free_reg = 0
        # Mapeamento para variáveis que serão tratadas como endereços de memória
        self.name_to_mem_map = {}

    def get_reg(self, temp_var):
        """Obtém o registrador físico para uma variável temporária."""
        if temp_var not in self.temp_to_reg_map:
            reg = f"r{self.next_free_reg}"
            self.temp_to_reg_map[temp_var] = reg
            self.next_free_reg += 1
            # Em um compilador real, aqui se trataria o esgotamento de registradores (spilling)
        return self.temp_to_reg_map[temp_var]

    def get_mem(self, name):
        """Retorna o nome do endereço de memória para uma variável."""
        if name not in self.name_to_mem_map:
            # Para simplificar, o nome da variável é usado como label de memória
            self.name_to_mem_map[name] = name
        return self.name_to_mem_map[name]

    def reset(self):
        """Reseta o alocador, útil para o início de novas funções."""
        self.temp_to_reg_map.clear()
        self.next_free_reg = 0
        self.name_to_mem_map.clear()

# --- Mapeamento de operadores do IR para mnemônicos de condição do Assembly ---
IR_TO_COND = {
    '>': ('gt', 'lteq'),
    '<': ('lt', 'gteq'),
    '==': ('eq', 'neq'),
    '!=': ('neq', 'eq'),
    '>=': ('gteq', 'lt'),
    '<=': ('lteq', 'gt')
}

# --- Funções de Tradução ---

def translate_label(parts, allocator):
    """Traduz um label. Ex: 'L0:' -> 'L0:'"""
    return [f"{parts[0]}"]

def translate_goto(parts, allocator):
    """Traduz um desvio incondicional. Ex: 'goto L1' -> 'b: L1'"""
    label = parts[1]
    return [f"\tb: {label}"]

def translate_if_false(parts, allocator):
    """
    Traduz um desvio condicional.
    Ex: 'if_false t4 goto L0' -> 'cmpis: r0 = r_t4, #0' e 'beq: L0'
    A instrução 'cmp' é uma forma conveniente de pensar em 'sub' com o bit 's'.
    """
    temp_reg = allocator.get_reg(parts[1])
    label = parts[3]
    # Compara o registrador com 0 para atualizar as flags do CPSR
    # subis r0, r_t4, #0 -> subtrai 0, não altera o valor mas atualiza as flags
    compare_instruction = f"\tsubis: r0, {temp_reg}, #0"
    # Branch if Equal (se o resultado for zero, a condição era falsa)
    branch_instruction = f"\tbeq: {label}"
    return [compare_instruction, branch_instruction]

def translate_binary_op(destination, arg1, op, arg2, allocator):
    """
    Traduz uma operação binária como 't4 := t2 > t3'.
    Isso se decompõe em uma comparação e dois movimentos condicionais.
    """
    dest_reg = allocator.get_reg(destination)
    arg1_reg = allocator.get_reg(arg1)
    arg2_reg = allocator.get_reg(arg2)

    # 1. Comparar os dois operandos para setar as flags (CPSR)
    #    'subis' (SUB com 's') é usado para a comparação, o resultado em r0 é descartado.
    compare_instr = f"\tsubis: r0, {arg1_reg}, {arg2_reg}"

    # 2. Obter os mnemônicos de condição
    cond_true, cond_false = IR_TO_COND[op]

    # 3. Mover 1 para o registrador de destino se a condição for verdadeira
    mov_true_instr = f"\tmov{cond_true}i: {dest_reg}, #1"

    # 4. Mover 0 para o registrador de destino se a condição for falsa
    mov_false_instr = f"\tmov{cond_false}i: {dest_reg}, #0"

    return [compare_instr, mov_true_instr, mov_false_instr]


def translate_assignment(parts, allocator):
    """
    Traduz operações de atribuição, abrangendo chamadas de função,
    acesso à memória e operações binárias.
    """
    destination = parts[0]

    # Caso 1: Chamada de função (ex: t0 := call input, 0)
    if 'call' in parts:
        func_name = parts[3].replace(',', '')
        call_instr = f"\tbl: {func_name}"
        # A convenção dita que o valor de retorno está em 'retval' (r0 no assembler)
        dest_reg = allocator.get_reg(destination)
        mov_instr = f"\tmov: {dest_reg}, retval" # 'retval' será tratado pelo montador
        return [call_instr, mov_instr]

    # Caso 2: Store (ex: *x := t0)
    if destination.startswith('*'):
        mem_addr = allocator.get_mem(destination[1:])
        source_reg = allocator.get_reg(parts[2])
        return [f"\tstore: [{mem_addr}], {source_reg}"]

    # Caso 3: Load (ex: t2 := *x)
    if parts[2].startswith('*'):
        dest_reg = allocator.get_reg(destination)
        mem_addr = allocator.get_mem(parts[2][1:])
        return [f"\tload: {dest_reg}, [{mem_addr}]"]

    # Caso 4: Operação Binária (ex: t4 := t2 > t3)
    if len(parts) > 3 and parts[3] in IR_TO_COND:
        return translate_binary_op(destination, parts[2], parts[3], parts[4], allocator)

    # Caso 5: Simples MOV (ex: t1 := t0)
    dest_reg = allocator.get_reg(destination)
    source_reg = allocator.get_reg(parts[2])
    return [f"\tmov: {dest_reg}, {source_reg}"]

def translate_arg(parts, allocator):
    """Traduz a passagem de argumentos. (Ex: arg t5)"""
    source_reg = allocator.get_reg(parts[1])
    # A convenção dita que os argumentos são passados através de registradores específicos.
    # Aqui, vamos assumir que o montador lidará com o 'arg' movendo o registrador
    # para o local correto (ex: r0, r1, ...).
    return [f"\tmov: arg, {source_reg}"] # 'arg' será um alias para o registrador de argumento

def translate_call(parts, allocator):
    """Traduz uma chamada de procedimento (sem valor de retorno)."""
    func_name = parts[1].replace(',', '')
    return [f"\tbl: {func_name}"]

def translate_return(parts, allocator):
    """Traduz uma instrução de retorno."""
    if len(parts) > 1 and parts[1] != '_':
        source_reg = allocator.get_reg(parts[1])
        # Mover o valor de retorno para o registrador de retorno convencional ('retval')
        return [f"\tmov: retval, {source_reg}", "\tret"]
    return ["\tret"]

# --- Lógica Principal de Tradução ---

def generate_assembly(ir_list):
    """
    Função principal para traduzir uma lista de instruções de IR para código assembly.
    """
    assembly_code = []
    reg_allocator = RegisterAllocator()

    # Mapeamento de opcodes do IR para funções de tradução
    IR_TRANSLATORS = {
        "goto": translate_goto,
        "if_false": translate_if_false,
        "return": translate_return,
        "arg": translate_arg,
        "call": translate_call,
    }

    # Diretivas iniciais do Assembly
    assembly_code.append(".text")
    assembly_code.append(".global main")
    assembly_code.append("")

    for line in ir_list:
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        opcode = parts[0]

        # Lógica de despacho
        translated_lines = []
        if opcode.endswith(':'):
            translated_lines = translate_label(parts, reg_allocator)
        elif ':=' in parts:
            translated_lines = translate_assignment(parts, reg_allocator)
        elif opcode in IR_TRANSLATORS:
            translator_func = IR_TRANSLATORS[opcode]
            translated_lines = translator_func(parts, reg_allocator)
        else:
            translated_lines = [f"\t# [AVISO] IR não tratado: {line}"]

        assembly_code.extend(translated_lines)

    return "\n".join(assembly_code)