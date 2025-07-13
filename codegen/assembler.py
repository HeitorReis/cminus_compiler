# python_assembler.py

# Dicionários de mapeamento da arquitetura do processador
instructions = {
    'add': ['00', '0000'], 'sub': ['00', '0001'], 'mul': ['00', '0010'],
    'div': ['00', '0011'], 'and': ['00', '0100'], 'or':  ['00', '0101'],
    'xor': ['00', '0110'], 'not': ['00', '0111'], 'mov': ['00', '1000'],
    'in':  ['00', '1001'],
    'load': ['01', '0001'], 'store': ['01', '0000'],
    'b': ['11', '0000'], 'bl': ['11', '1000'],
    'l': ['11', '0100'], 'll': ['11', '1100']
}

condition_setting = {
    'do': '0000', 'eq': '0001', 'neq': '0010', 'gt': '0011',
    'gteq': '0100', 'lt': '0101', 'lteq': '0110'
}

support_bits = {
    'i': '10', 's': '01', 'is': '11', 'si': '11', 'na': '00'
}

class Instruction:
    """
    Representa e processa uma única linha de código assembly,
    ignorando diretivas e labels.
    """
    def __init__(self, assembly_single_line: str):
        self.assembly_line = assembly_single_line.strip()
        self.binary32_line = ""
        self.debug_line = ""
        self.condition = "do"
        self.opCode = ""
        self.supportBits = "na"
        self.destinyRegister = ""
        self.hitRegister = ""
        self.operandRegister = ""
        self.immediateValue = "0"
        self.response = '-> Success'

        # Se a linha estiver vazia, ou for uma diretiva (começa com '.'), ou um label (termina com ':'), pule.
        if not self.assembly_line or self.assembly_line.startswith('.') or self.assembly_line.endswith(':'):
            self.response = '-> Skipped: Directive, Label, or Empty line'
            return

        self.disassemble(self.assembly_line)

        if 'Error' not in self.response:
            self.decode_assembly()

    def disassemble(self, line: str):
        """
        Analisa a linha de assembly e preenche os atributos da classe.
        """
        try:
            op_part, rest_part = line.split(':', 1)
            rest_part = rest_part.strip()
        except ValueError:
            self.response = f'-> Error: Syntax (missing ":" separator)'
            return

        self.get_op_cond_support(op_part)
        if 'Error' in self.response:
            return

        # Lógica para tratar aliases como 'retval' e 'arg'
        if 'retval' in rest_part: rest_part = rest_part.replace('retval', 'r0')
        if 'arg' in rest_part: rest_part = rest_part.replace('arg', 'r0') # Simplificação: assumindo que o primeiro argumento vai para r0


        if self.opCode in ('l', 'll', 'ret'): # Adicionado 'ret' para ser ignorado aqui
            return

        if self.opCode == 'in':
            self.destinyRegister = rest_part
            return

        if self.opCode in ('b', 'bl'):
            # Para branches, o 'rest_part' é o label e não será convertido para binário aqui
            # A resolução de labels é uma etapa posterior do montador/linker.
            self.immediateValue = rest_part # Apenas guardamos o label
            return

        try:
            dest_part, source_part = rest_part.split('=', 1)
            self.destinyRegister = dest_part.strip()

            if ',' not in source_part:
                if '#' in source_part:
                    self.supportBits = 'i' # Detecta imediato pelo '#'
                    self.immediateValue = source_part.replace('#', '').strip()
                else:
                    self.hitRegister = source_part.strip()
                return

            source_parts = [p.strip() for p in source_part.split(',')]
            self.hitRegister = source_parts[0]
            if len(source_parts) > 1:
                if '#' in source_parts[1]:
                    self.supportBits = 'i'
                    self.immediateValue = source_parts[1].replace('#', '').strip()
                else:
                    self.operandRegister = source_parts[1]
        except (ValueError, IndexError):
            self.response = f"-> Error: Malformed operands for instruction '{self.opCode}'"
    
    # O restante da classe (decode_assembly, get_op_cond_support, getSignedBinary) permanece o mesmo...
    def decode_assembly(self):
        """
        Codifica os atributos para a representação binária de 32 bits e
        cria uma linha de depuração paralela.
        """
        try:
            cond_bits = condition_setting.get(self.condition, '0000')
            type_code, op_code_val = instructions.get(self.opCode, ["", ""])
            support = support_bits.get(self.supportBits, '00')
            
            self.binary32_line = cond_bits + type_code + support + op_code_val
            self.debug_line = f"cond[{cond_bits}] type[{type_code}] sup[{support}] op[{op_code_val}] "

            if self.opCode in ('b', 'bl'):
                self.binary32_line += format(0, '020b') # Placeholder para o endereço do label
                self.debug_line += f"label[{self.immediateValue}]"
                return

            if self.opCode in ('l', 'll', 'ret'):
                self.binary32_line += format(0, '020b')
                self.debug_line += "n/a[0...19]"
                return

            rd_bits = format(int(self.destinyRegister[1:]), '05b') if self.destinyRegister and 'r' in self.destinyRegister else '00000'
            self.binary32_line += rd_bits
            self.debug_line += f"Rd[{rd_bits}] "

            if self.opCode == 'in':
                self.binary32_line += format(0, '015b')
                self.debug_line += "n/a[0...14]"
                return

            rh_bits = format(int(self.hitRegister[1:]), '05b') if self.hitRegister and 'r' in self.hitRegister else '00000'
            self.binary32_line += rh_bits
            self.debug_line += f"Rh[{rh_bits}] "

            if 'i' in self.supportBits:
                imm_bits = self.getSignedBinary(self.immediateValue, 10)
                self.binary32_line += imm_bits
                self.debug_line += f"imm[{imm_bits}]"
            else:
                ro_bits = format(int(self.operandRegister[1:]), '05b') if self.operandRegister and 'r' in self.operandRegister else '00000'
                self.binary32_line += ro_bits + '00000'
                self.debug_line += f"Ro[{ro_bits}] pad[00000]"

        except Exception as e:
            self.response = f"-> Error: An unexpected error occurred during decoding: {e}"

    def get_op_cond_support(self, op_part: str):
        temp_op = op_part.strip()
        conditions = ['gteq', 'lteq', 'neq', 'eq', 'gt', 'lt']
        for cond in conditions:
            if temp_op.endswith(cond):
                self.condition = cond
                temp_op = temp_op[:-len(cond)]
                break
        else:
            self.condition = 'do'

        if temp_op.endswith(('is', 'si')):
            self.supportBits = 'is'
            temp_op = temp_op[:-2]
        elif temp_op.endswith('i'):
            self.supportBits = 'i'
            temp_op = temp_op[:-1]
        elif temp_op.endswith('s'):
            self.supportBits = 's'
            temp_op = temp_op[:-1]
        
        self.opCode = temp_op
        if self.opCode not in instructions and self.opCode != 'ret': # Permitir 'ret'
            self.response = f"-> Error: Syntax (invalid base OpCode '{self.opCode}')"

    def getSignedBinary(self, immediateValue: str, bits: int) -> str:
        value = int(immediateValue.replace('#', ''))
        if value >= 0:
            return format(value, f'0{bits}b')
        else:
            return format((1 << bits) + value, f'0{bits}b')

class FullCode:
    def __init__(self, assembly_code_lines: list):
        self.assembly_list = assembly_code_lines
        self.code_list = []
        self.full_code = ""
        self.debug_output = ""
        self.response = self.decode_full_code()

    def decode_full_code(self):
        all_lines_data = []
        for row_index, row in enumerate(self.assembly_list):
            line_instruction = Instruction(row)
            if 'Error' in line_instruction.response:
                return f"{line_instruction.response} in line {row_index + 1} ('{row.strip()}')"
            
            if 'Skipped' not in line_instruction.response:
                all_lines_data.append((line_instruction.binary32_line, line_instruction.debug_line))

        self.full_code = "".join([f"{data[0]}\n" for data in all_lines_data])
        self.debug_output = "\n".join([f"{data[0]} -> {data[1]}" for data in all_lines_data])
        
        return '-> Success'