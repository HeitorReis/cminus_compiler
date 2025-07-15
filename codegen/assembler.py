# codegen/assembler.py

import re

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
    def __init__(self, assembly_single_line: str, symbol_table: dict, current_address: int):
        self.assembly_line = assembly_single_line.strip()
        self.symbol_table = symbol_table
        self.current_address = current_address
        self.binary32_line = ""
        self.debug_line = ""
        self.response = '-> Success'
        self.op_details = {}

        if self.assembly_line.startswith('.') or (self.assembly_line.endswith(':') and self.assembly_line != 'ret:'):
            self.response = '-> Skipped: Directive or Label'
            return

        self.op_details = self.disassemble(self.assembly_line)
        if 'Error' in self.op_details:
            self.response = self.op_details['Error']
            return

        self.binary32_line, self.debug_line = self.encode()
        if 'Error' in self.binary32_line:
            self.response = self.binary32_line
            return

    def get_op_type(self, opcode):
        for type_code, op_list in type_codes.items():
            if opcode in op_list:
                return type_code
        if any(opcode.startswith(br) for br in ['bi']):
            return '11'
        return None

    def disassemble(self, line: str) -> dict:
        """
        Analisa a linha de assembly e extrai suas partes.
        *** LÓGICA DE ANÁLISE FINAL E CORRIGIDA ***
        """
        details = {'cond': 'do', 'supp': 'na'}
        
        if line == 'ret:':
            details['opcode'] = 'ret'
            details['type'] = '11'
            return details

        try:
            op_part, rest_part = line.split(':', 1)
            rest_part = rest_part.strip()
        except ValueError:
            return {'Error': f'-> Error: Syntax (missing ":" separator) in line "{line}"'}

        op_part = op_part.strip()

        sorted_conditions = sorted(condition_setting.keys(), key=len, reverse=True)
        for cond_suffix in sorted_conditions:
            if cond_suffix != 'do' and op_part.endswith(cond_suffix):
                details['cond'] = cond_suffix
                op_part = op_part[:-len(cond_suffix)]
                break
        
        if op_part.endswith(('is', 'si')):
            details['supp'] = 'is'
            op_part = op_part[:-2]
        elif op_part.endswith('i'):
            details['supp'] = 'i'
            op_part = op_part[:-1]
        elif op_part.endswith('s'):
            details['supp'] = 's'
            op_part = op_part[:-1]
            
        details['opcode'] = op_part
        details['type'] = self.get_op_type(details['opcode'])

        if details['type'] is None and not details['opcode'].startswith("bi"):
            return {'Error': f"-> Error: Unknown instruction opcode '{details['opcode']}'"}

        rest_part = rest_part.replace('retval', 'r0').replace('arg0', 'r0')

        # Analisar operandos com base no tipo de instrução
        if details['type'] == '11': # Branch
            details['op2'] = rest_part
        elif '=' not in rest_part:
            # ex: in: r1
            details['rd'] = rest_part if rest_part else 'r0'
            details['rh'] = 'r0'
            details['op2'] = '0'
        else: # Instruções com '='
            dest, source = map(str.strip, rest_part.split('=', 1))
            
            # Sintaxe: storei: 152 = r4
            if details['opcode'] == 'store' and 'i' in details['supp']:
                details['op2'] = dest       # Endereço imediato
                details['rh'] = source      # Registrador com o valor
                details['rd'] = 'r0'        # Rd não é usado, mas precisa de um valor padrão
            else:
            # Sintaxe: rd = ...
                details['rd'] = dest
                source_parts = list(map(str.strip, source.split(',')))
                details['rh'] = source_parts[0]
                if len(source_parts) > 1:
                    details['op2'] = source_parts[1]
                else: # Implícito em loadi rd = imm, onde rh é opcional
                    if 'i' in details['supp']:
                        details['op2'] = details['rh']
                        details['rh'] = 'r0' # Base padrão
                    else:
                        details['op2'] = 'r0' # operando2 padrão

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
        
        cond_bin = condition_setting.get(d['cond'], '0000')
        type_bin = d.get('type', '00')
        supp_bin = support_bits_map[d['supp']]

        base_opcode = d['opcode']
        if base_opcode.startswith('bi'):
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
                if target in self.symbol_table:
                    offset = self.symbol_table[target] - (self.current_address + 4)
                else:
                    offset = int(target)
                
                offset_val = offset // 4
                offset_bin = self.get_signed_binary(str(offset_val), 20)
                if 'Error' in offset_bin: return offset_bin, ""
                binary += offset_bin
                debug += f"offset_calc[({self.symbol_table.get(target, 'imm')} - {self.current_address + 4})/4 = {offset_val}]->bin[{offset_bin}]"
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
        self.assembly_list = [line.strip() for line in assembly_code_lines if line.strip()]
        self.symbol_table = {'output': 4}
        self.full_code = ""
        self.debug_output = ""
        self.response = '-> Success'
        
        self.first_pass()
        if 'Error' in self.response:
            return

        self.second_pass()

    def first_pass(self):
        current_address = 0
        in_data_section = False
        for line in self.assembly_list:
            if line.startswith(".data"):
                in_data_section = True
                continue
            if in_data_section: continue
            if line.endswith(':') and line != 'ret:':
                label = line[:-1]
                if label in self.symbol_table:
                    self.response = f"Error: Duplicate label '{label}'"
                    return
                self.symbol_table[label] = current_address
            elif not line.startswith('.'):
                current_address += 4
        
        data_base_address = current_address
        current_address = data_base_address
        in_data_section = False
        for line in self.assembly_list:
            if line.startswith(".data"):
                in_data_section = True
                continue
            if not in_data_section: continue
            if ':' in line:
                label, directive = map(str.strip, line.split(':', 1))
                if label in self.symbol_table:
                    self.response = f"Error: Duplicate symbol '{label}'"
                    return
                self.symbol_table[label] = current_address
                if '.word' in directive:
                    current_address += 4
        
        print("--- SYMBOL TABLE (1st Pass) ---")
        for symbol, address in self.symbol_table.items():
            print(f"{symbol}: {address}")
        print("---------------------------------")

    def second_pass(self):
        all_lines_data = []
        current_address = 0
        in_data_section = False
        for line_num, line in enumerate(self.assembly_list):
            if line.startswith(".data"):
                in_data_section = True
                continue
            if in_data_section: continue
            if line.startswith('.') or (line.endswith(':') and line != 'ret:'): continue
            
            line_instruction = Instruction(line, self.symbol_table, current_address)
            
            if 'Error' in line_instruction.response:
                self.response = f"{line_instruction.response} in line {line_num + 1} ('{line.strip()}')"
                return
            
            all_lines_data.append((line_instruction.binary32_line, line_instruction.debug_line))
            current_address += 4

        self.full_code = "\n".join([f"{data[0]}" for data in all_lines_data]) + "\n"
        self.debug_output = "\n".join([f"{data[0]} -> {data[1]}" for data in all_lines_data])