# codegen/assembler.py

import re
import collections

# Dicionários de mapeamento da arquitetura do processador
instructions = {
    # Data-Processing (Type 00)
    'add': '0000', 'sub': '0001', 'mul': '0010', 'div': '0011',
    'and': '0100', 'or':  '0101', 'xor': '0110', 'not': '0111',
    'mov': '1000', 'in': '1001',
    
    # Load/Store (Type 01)
    'store': '0000', 'load': '0001',
    
    # Branch (Type 11)
    'b': '0000', 'bl': '1000', 'ret': '1111'
}

type_codes = {
    '00': ['add', 'sub', 'mul', 'div', 'and', 'or', 'xor', 'not', 'mov', 'in'],
    '01': ['load', 'store'],
    '11': ['b', 'bl', 'ret', 'bieq', 'bineq', 'bigt', 'bigteq', 'bilt', 'bilteq']
}

condition_setting = {
    'do': '0000', 'eq': '0001', 'neq': '0010', 'gt': '0011',
    'gteq': '0100', 'lt': '0101', 'lteq': '0110'
}

support_bits_map = {
    'i': '10', 's': '01', 'is': '11', 'si': '11', 'na': '00'
}

class Instruction:
    def __init__(
        self, 
        assembly_single_line: str, 
        symbol_table: dict, 
        current_address: int,
        literal_pool: dict
        ):
        print(f"\n--- [INSTRUCTION] Nova instrução em processamento na linha de montagem: '{assembly_single_line.strip()}' ---")
        self.assembly_line = assembly_single_line.strip()
        self.symbol_table = symbol_table
        self.current_address = current_address
        self.literal_pool = literal_pool
        self.binary32_line = ""
        self.debug_line = ""
        self.response = '-> Success'
        self.op_details = {}
        self.binary32_lines = []
        self.debug_lines = []

        if self.assembly_line.startswith('.') or (self.assembly_line.endswith(':') and self.assembly_line != 'ret:'):
            self.response = '-> Skipped: Directive or Label'
            print(f"[INSTRUCTION] -> Linha ignorada: {self.response}")
            return

        print("[INSTRUCTION] -> Passo 1: Desmontando a linha de assembly...")
        self.op_details = self.disassemble(self.assembly_line)
        if 'Error' in self.op_details:
            self.response = self.op_details['Error']
            print(f"[INSTRUCTION] -> Erro na desmontagem: {self.response}")
            return
        
        print(f"[INSTRUCTION] -> Desmontagem concluída. Detalhes: {self.op_details}")
        print("[INSTRUCTION] -> Passo 2: Codificando para binário...")
        result = self.encode()
        if result is None:
            # Pseudo-instrução foi tratada dentro do encode
            if self.binary32_lines:
                print(f"[INSTRUCTION] -> Codificação de pseudo-instrução concluída. Gerou {len(self.binary32_lines)} linhas binárias.")
            return

        self.binary32_line, self.debug_line = result
        if 'Error' in self.binary32_line:
            self.response = self.binary32_line
            print(f"[INSTRUCTION] -> Erro na codificação: {self.response}")
            return
        
        print(f"[INSTRUCTION] -> Codificação concluída. Binário: {self.binary32_line}")

    def get_op_type(self, opcode):
        for type_code, op_list in type_codes.items():
            if opcode in op_list:
                return type_code
        if any(opcode.startswith(br) for br in ['b']):
            return '11'
        return None

    def disassemble(self, line: str) -> dict:
        print(f"[DISASSEMBLE] Analisando: '{line}'")
        details = {'cond': 'do', 'supp': 'na'}
        
        if line == 'ret:':
            details['opcode'] = 'ret'
            details['type'] = '11'
            print(f"[DISASSEMBLE] -> Instrução 'ret' identificada.")
            return details

        try:
            op_part, rest_part = line.split(':', 1)
            rest_part = rest_part.strip()
        except ValueError:
            return {'Error': f'-> Error: Syntax (missing ":" separator) in line "{line}"'}

        op_part = op_part.strip()
        print(f"[DISASSEMBLE] -> Parte do opcode: '{op_part}', Parte dos operandos: '{rest_part}'")

        branch_ops = ['bieq', 'bineq', 'bigt', 'bigteq', 'bilt', 'bilteq']
        if op_part in branch_ops:
            details['opcode'] = 'b'          # A instrução base é sempre 'b' (branch)
            details['cond'] = op_part[2:]    # A condição são os últimos caracteres (ex: 'lteq')
            details['type'] = '11'
            details['supp'] = 'na' # A lógica de branch não precisa de 'i' aqui.
            details['op2'] = rest_part       # O alvo do desvio
            return details
        
        branch_ops = ['beq', 'bneq', 'bgt', 'bgteq', 'blt', 'blteq']
        if op_part in branch_ops:
            details['opcode'] = 'b'          # A instrução base é sempre 'b' (branch)
            details['cond'] = op_part[1:]    # A condição são os últimos caracteres (ex: 'lteq')
            details['type'] = '11'
            details['supp'] = 'na' # A lógica de branch não precisa de 'i' aqui.
            details['op2'] = rest_part       # O alvo do desvio
            return details

        
        if op_part.endswith(('is', 'si')):
            details['supp'] = 'is'
            op_part = op_part[:-2]
        elif op_part.endswith('i'):
            details['supp'] = 'i'
            op_part = op_part[:-1]
        elif op_part.endswith('s'):
            details['supp'] = 's'
            op_part = op_part[:-1]
            
        if details['supp'] != 'na':
            print(f"[DISASSEMBLE] -> Sufixo de suporte encontrado: '{details['supp']}'. Opcode final é '{op_part}'")
            
        details['opcode'] = op_part
        details['type'] = self.get_op_type(details['opcode'])
        print(f"[DISASSEMBLE] -> Opcode final: '{details['opcode']}', Tipo: {details['type']}")

        if details['type'] is None and not details['opcode'].startswith("b"):
            return {'Error': f"-> Error: Unknown instruction opcode '{details['opcode']}'"}

        rest_part = rest_part.replace('retval', 'r0').replace('arg0', 'r0')

        if details['type'] == '11': # Branch
            print(f"[DISASSEMBLE] -> Instrução de Branch. Alvo: '{rest_part}'")
        elif '=' not in rest_part:
            details['rd'] = rest_part if rest_part else 'r0'
            details['rh'] = 'r0'
            details['op2'] = '0'
            print(f"[DISASSEMBLE] -> Instrução de operando único. Rd: '{details['rd']}'")
        else: # Instruções com '='
            dest, source = map(str.strip, rest_part.split('=', 1))
            
            if details['opcode'] == 'store' and 'i' in details['supp']:
                print("[DISASSEMBLE] -> Caso especial 'storei' identificado.")
                details['op2'] = dest
                details['rh'] = source
                details['rd'] = 'r0'
            elif source.startswith('[') and source.endswith(']') or dest.startswith('[') and dest.endswith(']'):
                if details['opcode'] == 'load':
                    details['rd'] = dest
                    details['rh'] = source.strip('[]')
                    details['op2'] = '0'
                elif details['opcode'] == 'store':
                    details['rd'] = 'r0'
                    details['rh'] = dest.strip('[]')
                    details['op2'] = source
                details['supp'] = 'na'
                print("[DISASSEMBLE] -> Instrução Load/Store com endereçamento por registrador.")
            
            else:
                details['rd'] = dest
                source_parts = list(map(str.strip, source.split(',')))
                details['rh'] = source_parts[0]
                print(f"[DISASSEMBLE] -> Instrução com atribuição. Destino: '{dest}', Origem: '{source}'")
                
                if len(source_parts) > 1:
                    details['op2'] = source_parts[1]
                else:
                    if 'i' in details['supp']:
                        details['op2'] = details['rh']
                        details['rh'] = 'r0'
                    else:
                        details['op2'] = 'r0'
                print("[DISASSEMBLE] -> Operandos finais: Rd='{}', Rh='{}', Op2='{}'".format(details.get('rd'), details.get('rh'), details.get('op2')))
        return details

    def get_signed_binary(self, value_str: str, bits: int) -> str:
        try:
            value = int(value_str)
            if value >= 0:
                return format(value, f'0{bits}b')
            else: # Complemento de dois
                return format((1 << bits) + value, f'0{bits}b')
        except (ValueError, TypeError):
            return f"Error: Invalid immediate value '{value_str}'"

    def encode(self) -> (str, str):
        d = self.op_details
        print(f"[ENCODE] Iniciando codificação para a instrução: {d}")
        
        if d['opcode'] == 'mov' and d['supp'] == 'i':
            imm_val_str = d.get('op2', '0')
            imm_val = self.symbol_table.get(imm_val_str, imm_val_str)
            
            try:
                numeric_val = int(imm_val)
                if not (-512 <= numeric_val <= 511):
                    print(f"[ENCODE] -> Valor imediato '{numeric_val}' é muito grande para 10 bits. Tratando como pseudo-instrução.")
                    
                    literal_label = None
                    for label, value in self.literal_pool.items():
                        if value == numeric_val:
                            literal_label = label
                            break
                    
                    if literal_label is None:
                        return f"Error: Literal for value {numeric_val} not found in pool", ""
                    
                    print(f"[ENCODE] -> Gerando pseudo-instrução: movi r12, {literal_label} (load do valor)")
                    movi_details = d.copy()
                    movi_details['rd'] = 'r12'  # Usamos r12 como registrador de rascunho
                    movi_details['op2'] = literal_label
                    
                    bin1, deb1 = self._encode_single_instruction(movi_details)
                    if "Error" in bin1: 
                        self.response = bin1
                        return None, None
                    self.binary32_lines.append(bin1)
                    self.debug_lines.append(f"{self.assembly_line} -> (Pseudo) {deb1}")
                    print(f"[ENCODE] -> Gerando segunda parte: load {d['rd']}, [r12]")
                    
                    load_details = {
                        'opcode': 'load', 'type': '01', 'cond': d['cond'],
                        'supp': 'na', 'rd': d['rd'], 'rh': 'r12', 'op2': '0'
                    }
                    bin2, deb2 = self._encode_single_instruction(load_details, is_pseudo=True)
                    if "Error" in bin2:
                        self.response = bin2
                        return None, None
                    self.binary32_lines.append(bin2)
                    self.debug_lines.append(f"{' ': <{len(self.assembly_line)}} -> (Pseudo) {deb2}")
                    
                    return None, None
                
            except (ValueError, KeyError):
                pass
            
        print("[ENCODE] -> Tratando como instrução normal.")
        return self._encode_single_instruction(self.op_details)

    def _encode_single_instruction(self, d, is_pseudo=False):
        cond_bin = condition_setting.get(d['cond'], '0000')
        type_bin = d.get('type', '00')
        supp_bin = support_bits_map[d['supp']]

        base_opcode = d['opcode']
        if base_opcode.startswith('b'):
            d['cond'] = base_opcode[2:]
            base_opcode = 'b'
            cond_bin = condition_setting.get(d['cond'], '0000')
        
        funct_bin = instructions.get(base_opcode)
        if funct_bin is None:
            return f"Error: Instruction '{base_opcode}' not found", ""

        debug = f"cond[{cond_bin}] type[{type_bin}] supp[{supp_bin}] op[{funct_bin}] "
        binary = cond_bin + type_bin + supp_bin + funct_bin
        
        if base_opcode == 'ret':
            binary += '0' * 20
            debug += "n/a[0...19]"
            return binary, debug
        
        if d['type'] == '11': # Branch
            try:
                target = d['op2']
                offset = 0
                
                next_instruction_address = self.current_address + (2 if is_pseudo else 1)
                
                if target in self.symbol_table:
                    # offset = destino - (PC + 1)
                    offset = self.symbol_table[target] - next_instruction_address
                else:
                    offset = int(target)
                
                offset_val = offset
                offset_bin = self.get_signed_binary(str(offset_val), 20)
                if 'Error' in offset_bin: return offset_bin, ""
                binary += offset_bin
                debug += f"offset_calc[({self.symbol_table.get(target, 'imm')} - {next_instruction_address}) = {offset_val}]->bin[{offset_bin}]"
            except (ValueError, KeyError) as e:
                return f"Error resolving branch target '{d['op2']}': {e}", ""
        else: # Data-Proc e Load/Store
            rd_bin = self.get_signed_binary(d.get('rd', 'r0').replace('r', ''), 5)
            rh_bin = self.get_signed_binary(d.get('rh', 'r0').replace('r', ''), 5)
            debug += f"Rd[{rd_bin}] Rh[{rh_bin}] "
            
            op2_str = d.get('op2', '0')
            op2_bin = ""
            is_immediate = 'i' in d['supp']

            if is_immediate:
                imm_val_str = op2_str.replace('[', '').replace(']', '').replace('#', '')
                imm_val = self.symbol_table.get(imm_val_str, imm_val_str)
                op2_bin = self.get_signed_binary(str(imm_val), 10)
                debug += f"imm[{op2_str}={imm_val}]->[{op2_bin}]"
            else: # Registrador
                ro_num_str = op2_str.replace('r', '')
                ro_bin = self.get_signed_binary(ro_num_str, 5)
                op2_bin = ro_bin + '00000'
                debug += f"Ro[{ro_bin}] pad[00000]"

            if 'Error' in rd_bin or 'Error' in rh_bin or 'Error' in op2_bin:
                return "Error during operand encoding", ""

            binary += rd_bin + rh_bin + op2_bin

        if len(binary) != 32:
            return f"Error: Generated instruction has invalid length {len(binary)}", debug

        return binary, debug

class FullCode:
    def __init__(self, assembly_code_lines: list):
        print("\n\n=== INICIANDO PROCESSO DE MONTAGEM (FullCode) ===")
        self.assembly_list = [line.strip() for line in assembly_code_lines if line.strip()]
        self.symbol_table = {'output': 1} 
        self.literal_pool = collections.OrderedDict()
        self.full_code = ""
        self.debug_output = ""
        self.response = '-> Success'
        
        print("[INIT] Executando a primeira passagem para construir a tabela de símbolos...")
        self.first_pass()
        if 'Error' in self.response:
            print(f"[INIT] Erro detectado na primeira passagem: {self.response}")
            return

        print(f"[INIT] Tabela de símbolos após a primeira passagem: {self.symbol_table}")
        print("[INIT] Executando a segunda passagem para codificar as instruções...")
        self.second_pass()
        print("=== PROCESSO DE MONTAGEM CONCLUÍDO ===")

    def first_pass(self):
        print("\n--- [PASS 1] Iniciando a Primeira Passagem ---")
        current_address = 0
        instruction_sizes = {}
        
        # ETAPA 1: Prever o tamanho das instruções
        print("[PASS 1] Etapa 1: Prevendo o tamanho de cada instrução na seção .text...")
        in_text_section = True
        for i, line in enumerate(self.assembly_list):
            if line.startswith(".data"):
                in_text_section = False
                continue
            if not in_text_section or line.startswith(".") or (line.endswith(':') and line != 'ret:'):
                continue

            details = self._disassemble_for_pass1(line)
            if details.get('opcode') == 'mov' and details.get('supp') == 'i':
                try:
                    imm_val = int(details.get('op2', '0'))
                    if not (-512 <= imm_val <= 511):
                        instruction_sizes[i] = 2
                        print(f"[PASS 1] -> Linha {i+1} ('{line}') é uma pseudo-instrução (tamanho 2).")
                    else:
                        instruction_sizes[i] = 1
                except ValueError:
                    instruction_sizes[i] = 2 
                    print(f"[PASS 1] -> Linha {i+1} ('{line}') tratada como pseudo-instrução (tamanho 2).")
            else:
                instruction_sizes[i] = 1
        
        # ETAPA 2: Construir tabela de símbolos para rótulos de CÓDIGO
        print("\n[PASS 1] Etapa 2: Mapeando os rótulos de código para endereços...")
        current_address = 0
        in_text_section = True
        for i, line in enumerate(self.assembly_list):
            if line.startswith(".data"):
                in_text_section = False
                continue
            if not in_text_section: continue
            
            if line.endswith(':') and line != 'ret:':
                label = line[:-1]
                if label in self.symbol_table:
                    self.response = f"Error: Rótulo duplicado '{label}'"
                    return
                self.symbol_table[label] = current_address
                print(f"[PASS 1] -> Rótulo '{label}' mapeado para o endereço {current_address}.")
            elif i in instruction_sizes:
                current_address += instruction_sizes[i]
        
        # ETAPA 3: Definir o início da seção de dados
        self.data_section_start_address = current_address
        print(f"\n[PASS 1] Etapa 3: A seção de código termina no endereço {current_address - 1}. A seção .data começará em {self.data_section_start_address}.")
        
        # ETAPA 4: Mapear rótulos de DADOS
        print("\n[PASS 1] Etapa 4: Mapeando os rótulos da seção .data...")
        data_base_address = self.data_section_start_address
        in_data_section = False
        for line in self.assembly_list:
            if line.startswith(".data"):
                in_data_section = True
                continue
            if not in_data_section: continue
            if ':' in line:
                label, directive = map(str.strip, line.split(':', 1))
                if label in self.symbol_table:
                    self.response = f"Error: Símbolo duplicado '{label}'"
                    return
                self.symbol_table[label] = data_base_address
                print(f"[PASS 1] -> Rótulo de dados '{label}' mapeado para o endereço {data_base_address}.")
                if '.word' in directive:
                    data_base_address += 1
        print("--- Fim da Primeira Passagem ---")

    def second_pass(self):
        print("\n--- [PASS 2] Iniciando a Segunda Passagem ---")
        all_lines_data = []
        current_address = 0
        
        # ETAPA 1: Atribuir endereços aos literais
        print("[PASS 2] Etapa 1: Coletando literais grandes e atribuindo endereços a eles...")
        literal_address = max(self.symbol_table.values(), default=-1) + 1
        for line in self.assembly_list:
            if line.startswith(".") or (line.endswith(':') and line != 'ret:'): continue
            
            details = self._disassemble_for_pass1(line)
            if details.get('opcode') == 'mov' and details.get('supp') == 'i':
                try:
                    imm_val_str = details.get('op2', '0')
                    imm_val = self.symbol_table.get(imm_val_str, imm_val_str)
                    numeric_val = int(imm_val)
                    if not (-512 <= numeric_val <= 511):
                        if numeric_val not in self.literal_pool.values():
                            literal_label = f".Lconst{len(self.literal_pool)}"
                            self.literal_pool[literal_label] = numeric_val
                            self.symbol_table[literal_label] = literal_address
                            print(f"[PASS 2] -> Literal grande '{numeric_val}' encontrado. Rótulo '{literal_label}' mapeado para o endereço {literal_address}.")
                            literal_address += 1
                except (ValueError, KeyError):
                    pass 
        if self.literal_pool:
            print(f"[PASS 2] -> Pool de literais final: {self.literal_pool}")
        else:
            print("[PASS 2] -> Nenhum literal grande encontrado.")

        # ETAPA 2: Codificar as instruções
        print("\n[PASS 2] Etapa 2: Codificando cada linha de instrução para binário...")
        for line_num, line in enumerate(self.assembly_list):
            if line.startswith(".") or (line.endswith(':') and line != 'ret:'): continue
            
            line_instruction = Instruction(line, self.symbol_table, current_address, self.literal_pool)
            if 'Error' in line_instruction.response:
                self.response = f"{line_instruction.response} na linha {line_num + 1} ('{line.strip()}')"
                return
            
            if line_instruction.binary32_lines:
                for i in range(len(line_instruction.binary32_lines)):
                    all_lines_data.append((line_instruction.binary32_lines[i], line_instruction.debug_lines[i]))
                    current_address += 1
            elif line_instruction.binary32_line:
                all_lines_data.append((line_instruction.binary32_line, line_instruction.debug_line))
                current_address += 1

        self.full_code = "\n".join([f"{data[0]}" for data in all_lines_data])
        self.debug_output = "\n".join([f"{data[0]} -> {data[1]}" for data in all_lines_data])
        print(f"\n[PASS 2] -> {len(all_lines_data)} linhas de código de máquina geradas.")

        # ETAPA 3: Adicionar dados e literais ao código de máquina
        print("\n[PASS 2] Etapa 3: Adicionando a seção de dados e literais ao código de máquina final...")
        data_section_code = []
        data_vars = {}
        in_data_section = False
        for line in self.assembly_list:
            if line.startswith('.data'): in_data_section = True; continue
            if not in_data_section: continue
            if '.word' in line:
                label = line.split(':')[0]
                val_str = line.split('.word')[1].strip()
                data_vars[self.symbol_table[label]] = val_str

        for label, value in self.literal_pool.items():
            data_vars[self.symbol_table[label]] = str(value)
        
        sorted_data = sorted(data_vars.items())
        print(f"[PASS 2] -> Dados a serem adicionados (endereço: valor): {sorted_data}")
        
        for addr, value in sorted_data:
            data_section_code.append(self.get_signed_binary(value, 32))
        
        if data_section_code:
            self.full_code += "\n" + "\n".join(data_section_code)
        print("--- Fim da Segunda Passagem ---")
            
    def _disassemble_for_pass1(self, line):
        details = {}
        try:
            op_part, rest_part = line.split(':', 1)
            op_part = op_part.strip()
            details['supp'] = 'i' if 'i' in op_part else 'na'
            op_part_no_cond = op_part
            for cond in condition_setting:
                if op_part_no_cond.endswith(cond):
                    op_part_no_cond = op_part_no_cond[:-len(cond)]
            details['opcode'] = op_part_no_cond.rstrip('is')
            if '=' in rest_part:
                dest, source = map(str.strip, rest_part.split('=', 1))
                if 'mov' in details['opcode'] and 'i' in details['supp']:
                    details['op2'] = source.split(',')[0].strip()
                elif 'store' in details['opcode'] and 'i' in details['supp']:
                    details['op2'] = dest
                else:
                    details['op2'] = source.split(',')[0].strip()
        except ValueError:
            pass
        return details

    def get_signed_binary(self, value_str: str, bits: int) -> str:
        try:
            value = int(value_str)
            if value >= 0:
                return format(value, f'0{bits}b')
            else:
                return format((1 << bits) + value, f'0{bits}b')
        except (ValueError, TypeError):
            return f"Error: Invalid immediate value '{value_str}'"