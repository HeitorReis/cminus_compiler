import collections
import re
from dataclasses import dataclass

from constants import STACK_WORDS

CONDITION_CODES = {
    'do': '0000',
    'eq': '0001',
    'neq': '0010',
    'gt': '0011',
    'gteq': '0100',
    'lt': '0101',
    'lteq': '0110',
}

SUPPORT_BITS = {
    'na': '00',
    's': '01',
    'i': '10',
    'is': '11',
}

INSTRUCTION_INFO = {
    'add': ('00', '0000'),
    'sub': ('00', '0001'),
    'mul': ('00', '0010'),
    'div': ('00', '0011'),
    'and': ('00', '0100'),
    'or': ('00', '0101'),
    'xor': ('00', '0110'),
    'not': ('00', '0111'),
    'mov': ('00', '1000'),
    'in': ('00', '1001'),
    'out': ('00', '1010'),
    'store': ('01', '0000'),
    'load': ('01', '0001'),
    'b': ('11', '0000'),
    'bl': ('11', '1000'),
}

CONDITION_SUFFIXES = sorted([suffix for suffix in CONDITION_CODES if suffix != 'do'], key=len, reverse=True)
SUPPORT_SUFFIXES = ('is', 'si', 'i', 's')
REGISTER_PATTERN = re.compile(r'^r(\d+)$')
WORD_MASK_32 = (1 << 32) - 1


def is_integer_literal(token):
    return token.isdigit() or (token.startswith('-') and token[1:].isdigit())


def twos_complement(value, bits):
    min_value = -(1 << (bits - 1))
    max_value = (1 << (bits - 1)) - 1
    if value < min_value or value > max_value:
        raise ValueError(f"value {value} does not fit in {bits} bits")
    if value < 0:
        value = (1 << bits) + value
    return format(value, f'0{bits}b')


def register_bits(register_name):
    match = REGISTER_PATTERN.fullmatch(register_name)
    if not match:
        raise ValueError(f"invalid register '{register_name}'")
    register_index = int(match.group(1))
    if register_index < 0 or register_index > 31:
        raise ValueError(f"register out of range '{register_name}'")
    return format(register_index, '05b')


@dataclass
class ParsedInstruction:
    original: str
    mnemonic: str
    base_op: str
    cond: str
    supp: str
    operands: dict


class FullCode:
    def __init__(self, assembly_code_lines):
        self.assembly_list = [line.strip() for line in assembly_code_lines if line.strip()]
        self.response = '-> Success'
        self.debug_output = ''
        self.full_code = ''

        self.text_entries = []
        self.data_entries = []
        self.text_labels = {}
        self.data_labels = {}
        self.symbol_table = {}
        self.literal_pool = collections.OrderedDict()
        self.literal_addresses = {}
        self._instruction_sizes = {}
        self._instruction_plans = {}

        try:
            self._parse_source()
            self._build_data_labels()
            self._stabilize_text_layout()
            self._assign_literal_addresses()
            self._encode()
        except Exception as error:
            self.response = f"Error: {error}"

    def _parse_source(self):
        section = 'text'
        for line in self.assembly_list:
            if line.startswith('.text'):
                section = 'text'
                continue
            if line.startswith('.data'):
                section = 'data'
                continue
            if line.startswith('.global'):
                continue

            if section == 'text':
                if line.endswith(':') and line != 'ret:':
                    self.text_entries.append(('label', line[:-1]))
                else:
                    self.text_entries.append(('instruction', self._parse_instruction(line)))
            else:
                if ':' not in line:
                    raise ValueError(f"invalid data directive '{line}'")
                label, directive = [part.strip() for part in line.split(':', 1)]
                if directive.startswith('.space'):
                    amount = int(directive.split(None, 1)[1], 0)
                    self.data_entries.append((label, 'space', amount))
                elif directive.startswith('.word'):
                    value = int(directive.split(None, 1)[1], 0)
                    self.data_entries.append((label, 'word', value))
                else:
                    raise ValueError(f"unsupported data directive '{line}'")

    def _parse_instruction(self, line):
        if line == 'ret:':
            return ParsedInstruction(line, 'ret', 'ret', 'do', 'i', {'target': '0'})

        if ':' not in line:
            raise ValueError(f"missing ':' in instruction '{line}'")

        mnemonic, operands_text = [part.strip() for part in line.split(':', 1)]
        base_name, cond, supp = self._split_mnemonic(mnemonic)

        if base_name not in INSTRUCTION_INFO:
            raise ValueError(f"unknown opcode '{base_name}'")

        operands = self._parse_operands(base_name, operands_text, supp)
        resolved_supp = operands.pop('resolved_supp', supp)
        return ParsedInstruction(line, mnemonic, base_name, cond, resolved_supp, operands)

    def _split_mnemonic(self, mnemonic):
        candidates = []

        base_part = mnemonic
        cond = 'do'
        supp = 'na'
        for suffix in CONDITION_SUFFIXES:
            if base_part.endswith(suffix):
                candidates.append((base_part[:-len(suffix)], suffix, supp))
                break
        candidates.append((base_part, cond, supp))

        tried = []
        for candidate_base, candidate_cond, candidate_supp in candidates:
            for support_suffix in SUPPORT_SUFFIXES:
                if candidate_base.endswith(support_suffix):
                    normalized_support = 'is' if support_suffix in ('is', 'si') else support_suffix
                    base_name = candidate_base[:-len(support_suffix)]
                    tried.append((base_name, candidate_cond, normalized_support))
            tried.append((candidate_base, candidate_cond, candidate_supp))

        for candidate_base, candidate_cond, candidate_supp in tried:
            if candidate_base in INSTRUCTION_INFO:
                return candidate_base, candidate_cond, candidate_supp

        for support_suffix in SUPPORT_SUFFIXES:
            if mnemonic.endswith(support_suffix):
                base_after_support = mnemonic[:-len(support_suffix)]
                normalized_support = 'is' if support_suffix in ('is', 'si') else support_suffix
                for cond_suffix in CONDITION_SUFFIXES:
                    if base_after_support.endswith(cond_suffix):
                        base_name = base_after_support[:-len(cond_suffix)]
                        if base_name in INSTRUCTION_INFO:
                            return base_name, cond_suffix, normalized_support

        return mnemonic, 'do', 'na'

    def _parse_operands(self, base_op, operands_text, supp):
        operands = {}

        if base_op in ('b', 'bl'):
            target = operands_text.strip()
            if not target:
                raise ValueError(f"missing branch target in '{base_op}'")
            operands['target'] = target
            operands['resolved_supp'] = 'na' if REGISTER_PATTERN.fullmatch(target) else 'i'
            return operands

        if base_op == 'out':
            source = operands_text.strip()
            if not source:
                raise ValueError("missing operand for out")
            operands['op2'] = source
            operands['rd'] = 'r0'
            operands['rh'] = 'r0'
            operands['resolved_supp'] = 'na' if REGISTER_PATTERN.fullmatch(source) else 'i'
            return operands

        if base_op == 'in':
            operands['rd'] = operands_text.strip()
            operands['rh'] = 'r0'
            operands['op2'] = 'r0'
            operands['resolved_supp'] = 'na'
            return operands

        if '=' not in operands_text:
            raise ValueError(f"missing '=' in instruction '{base_op}: {operands_text}'")

        left_side, right_side = [part.strip() for part in operands_text.split('=', 1)]

        if base_op == 'load':
            if not (right_side.startswith('[') and right_side.endswith(']')):
                raise ValueError(f"invalid load source '{right_side}'")
            address = right_side[1:-1].strip()
            operands['rd'] = left_side
            operands['rh'] = 'r0'
            operands['op2'] = address
            operands['resolved_supp'] = 'na' if REGISTER_PATTERN.fullmatch(address) else 'i'
            return operands

        if base_op == 'store':
            if not (left_side.startswith('[') and left_side.endswith(']')):
                raise ValueError(f"invalid store target '{left_side}'")
            address = left_side[1:-1].strip()
            operands['rd'] = 'r0'
            operands['rh'] = right_side
            operands['op2'] = address
            operands['resolved_supp'] = 'na' if REGISTER_PATTERN.fullmatch(address) else 'i'
            return operands

        if base_op == 'mov':
            operands['rd'] = left_side
            operands['rh'] = 'r0'
            operands['op2'] = right_side
            operands['resolved_supp'] = 'na' if REGISTER_PATTERN.fullmatch(right_side) else 'i'
            return operands

        source_parts = [part.strip() for part in right_side.split(',')]
        operands['rd'] = left_side
        operands['rh'] = source_parts[0]
        operands['op2'] = source_parts[1] if len(source_parts) > 1 else 'r0'
        if operands['op2'] != 'r0' and not REGISTER_PATTERN.fullmatch(operands['op2']) and supp == 'na':
            operands['resolved_supp'] = 'i'
        else:
            operands['resolved_supp'] = supp
        return operands

    def _build_data_labels(self):
        current_address = 0
        for label, directive, value in self.data_entries:
            if label in self.data_labels:
                raise ValueError(f"duplicate data label '{label}'")
            self.data_labels[label] = current_address
            if directive == 'space':
                current_address += value
            else:
                current_address += 1

    def _stabilize_text_layout(self):
        instruction_index = 0
        for entry_type, _ in self.text_entries:
            if entry_type == 'instruction':
                self._instruction_sizes[instruction_index] = 1
                instruction_index += 1

        changed = True
        while changed:
            self._rebuild_text_labels()
            changed = False
            new_sizes = {}
            plans = {}
            instruction_index = 0
            current_address = 0

            for entry_type, payload in self.text_entries:
                if entry_type == 'label':
                    continue

                plan = self._plan_instruction(payload, current_address)
                plans[instruction_index] = plan
                new_sizes[instruction_index] = plan['size']
                if self._instruction_sizes.get(instruction_index) != plan['size']:
                    changed = True
                current_address += plan['size']
                instruction_index += 1

            self._instruction_sizes = new_sizes
            self._instruction_plans = plans

        self._rebuild_text_labels()

    def _rebuild_text_labels(self):
        self.text_labels = {}
        current_address = 0
        instruction_index = 0
        for entry_type, payload in self.text_entries:
            if entry_type == 'label':
                if payload in self.text_labels:
                    raise ValueError(f"duplicate text label '{payload}'")
                self.text_labels[payload] = current_address
            else:
                current_address += self._instruction_sizes.get(instruction_index, 1)
                instruction_index += 1

        self.symbol_table = {}
        self.symbol_table.update(self.text_labels)
        self.symbol_table.update(self.data_labels)

    def _resolve_symbol_or_int(self, token):
        if is_integer_literal(token):
            return int(token)
        if token in self.text_labels:
            return self.text_labels[token]
        if token in self.data_labels:
            return self.data_labels[token]
        raise ValueError(f"unknown symbol '{token}'")

    def _plan_instruction(self, instruction, current_address):
        if instruction.base_op == 'ret':
            return {'kind': 'ret', 'size': 1}

        if instruction.base_op == 'mov' and 'i' in instruction.supp:
            value = self._resolve_symbol_or_int(instruction.operands['op2'])
            if -512 <= value <= 511:
                return {'kind': 'single', 'size': 1}
            return {'kind': 'literal_move', 'size': 2, 'value': value}

        if instruction.base_op in ('b', 'bl') and not REGISTER_PATTERN.fullmatch(instruction.operands['target']):
            target = instruction.operands['target']
            if is_integer_literal(target):
                offset = int(target)
                if -512 <= offset <= 511:
                    return {'kind': 'single', 'size': 1}
                raise ValueError(f"numeric branch offset out of range in '{instruction.original}'")

            target_address = self._resolve_symbol_or_int(target)
            offset = target_address - (current_address + 1)
            if -512 <= offset <= 511:
                return {'kind': 'single', 'size': 1}
            move_size = 1 if -512 <= target_address <= 511 else 2
            return {
                'kind': 'long_branch',
                'size': move_size + 1,
                'target_address': target_address,
            }

        return {'kind': 'single', 'size': 1}

    def _assign_literal_addresses(self):
        literal_values = []
        for plan in self._instruction_plans.values():
            if plan['kind'] == 'literal_move':
                literal_values.append(plan['value'])
            elif plan['kind'] == 'long_branch' and not (-512 <= plan['target_address'] <= 511):
                literal_values.append(plan['target_address'])

        explicit_data_size = 0
        for _, directive, value in self.data_entries:
            explicit_data_size += value if directive == 'space' else 1

        next_address = explicit_data_size
        for value in literal_values:
            if value in self.literal_pool:
                continue
            label = f'.Lconst{len(self.literal_pool)}'
            self.literal_pool[value] = label
            self.literal_addresses[label] = next_address
            next_address += 1

        self.symbol_table.update(self.literal_addresses)

    def _encode(self):
        encoded_lines = []
        debug_lines = []

        instruction_index = 0
        current_address = 0
        for entry_type, payload in self.text_entries:
            if entry_type == 'label':
                continue

            plan = self._instruction_plans[instruction_index]
            concrete_instructions = self._expand_instruction(payload, plan, current_address)
            for concrete in concrete_instructions:
                binary = self._encode_concrete(concrete, current_address)
                encoded_lines.append(binary)
                debug_lines.append(f"{binary} -> {concrete['debug']}")
                current_address += 1
            instruction_index += 1

        for label, directive, value in self.data_entries:
            if directive == 'word':
                encoded_lines.append(format(value & WORD_MASK_32, '032b'))
                debug_lines.append(f"{encoded_lines[-1]} -> data {label} .word {value}")
            else:
                for index in range(value):
                    encoded_lines.append('0' * 32)
                    debug_lines.append(f"{encoded_lines[-1]} -> data {label}[{index}] .space")

        for value, label in self.literal_pool.items():
            encoded_lines.append(format(value & WORD_MASK_32, '032b'))
            debug_lines.append(f"{encoded_lines[-1]} -> literal {label} = {value}")

        self.full_code = '\n'.join(encoded_lines)
        self.debug_output = '\n'.join(debug_lines)

    def _expand_instruction(self, instruction, plan, current_address):
        if plan['kind'] == 'ret':
            pseudo_branch = ParsedInstruction('ret:', 'bi', 'b', 'do', 'i', {'target': '0'})
            return [{'instruction': pseudo_branch, 'debug': 'ret -> bi 0'}]

        if plan['kind'] == 'literal_move':
            literal_label = self.literal_pool[plan['value']]
            literal_address = self.literal_addresses[literal_label]
            if not (-512 <= literal_address <= 511):
                raise ValueError(f"literal address {literal_address} out of 10-bit range")
            scratch = 'r27'
            first = ParsedInstruction(
                f"movi: {scratch} = {literal_address}",
                'movi',
                'mov',
                instruction.cond,
                'i',
                {'rd': scratch, 'rh': 'r0', 'op2': str(literal_address)},
            )
            second = ParsedInstruction(
                f"load: {instruction.operands['rd']} = [{scratch}]",
                'load',
                'load',
                instruction.cond,
                'na',
                {'rd': instruction.operands['rd'], 'rh': 'r0', 'op2': scratch},
            )
            return [
                {'instruction': first, 'debug': f"{instruction.original} -> literal addr {literal_address}"},
                {'instruction': second, 'debug': f"{instruction.original} -> load literal"},
            ]

        if plan['kind'] == 'long_branch':
            scratch = 'r27'
            target_address = plan['target_address']
            first_phase = ParsedInstruction(
                f"movi: {scratch} = {target_address}",
                'movi',
                'mov',
                instruction.cond,
                'i',
                {'rd': scratch, 'rh': 'r0', 'op2': str(target_address)},
            )
            branch_to_reg = ParsedInstruction(
                f"{instruction.base_op}: {scratch}",
                instruction.base_op,
                instruction.base_op,
                instruction.cond,
                'na',
                {'target': scratch},
            )
            move_plan = {'kind': 'single', 'size': 1}
            if not (-512 <= target_address <= 511):
                move_plan = {'kind': 'literal_move', 'size': 2, 'value': target_address}
            move_sequence = self._expand_instruction(first_phase, move_plan, current_address)
            return move_sequence + [{'instruction': branch_to_reg, 'debug': f"{instruction.original} -> long branch"}]

        return [{'instruction': instruction, 'debug': instruction.original}]

    def _encode_concrete(self, concrete, current_address):
        instruction = concrete['instruction']
        info = INSTRUCTION_INFO[instruction.base_op]
        cond_bits = CONDITION_CODES[instruction.cond]
        type_bits, funct_bits = info
        supp_bits = SUPPORT_BITS[instruction.supp]

        binary = cond_bits + type_bits + supp_bits + funct_bits

        if instruction.base_op in ('b', 'bl'):
            target = instruction.operands['target']
            if REGISTER_PATTERN.fullmatch(target):
                binary += '0' * 10 + register_bits(target) + '0' * 5
            else:
                if is_integer_literal(target):
                    offset = int(target)
                else:
                    target_address = self.text_labels[target]
                    offset = target_address - (current_address + 1)
                binary += '0' * 10 + twos_complement(offset, 10)
            return binary

        rd_bits = register_bits(instruction.operands.get('rd', 'r0'))
        rh_bits = register_bits(instruction.operands.get('rh', 'r0'))
        op2_token = instruction.operands.get('op2', '0')

        if instruction.base_op == 'load':
            if 'i' in instruction.supp:
                immediate = self._resolve_symbol_or_int(op2_token)
                op2_bits = twos_complement(immediate, 10)
            else:
                op2_bits = register_bits(op2_token) + '0' * 5
            return binary + rd_bits + rh_bits + op2_bits

        if instruction.base_op == 'store':
            if 'i' in instruction.supp:
                immediate = self._resolve_symbol_or_int(op2_token)
                op2_bits = twos_complement(immediate, 10)
            else:
                op2_bits = register_bits(op2_token) + '0' * 5
            return binary + rd_bits + rh_bits + op2_bits

        if 'i' in instruction.supp:
            immediate = self._resolve_symbol_or_int(op2_token)
            op2_bits = twos_complement(immediate, 10)
        elif instruction.base_op == 'in':
            op2_bits = '0' * 10
        else:
            op2_bits = register_bits(op2_token) + '0' * 5

        return binary + rd_bits + rh_bits + op2_bits

    def decode_machine_code(self):
        decoded = []
        for line_number, line in enumerate(self.full_code.splitlines()):
            if len(line) != 32:
                decoded.append(f"Line {line_number}: invalid word")
                continue

            cond_bits = line[:4]
            type_bits = line[4:6]
            supp_bits = line[6:8]
            funct_bits = line[8:12]

            cond_name = next((name for name, bits in CONDITION_CODES.items() if bits == cond_bits), 'unknown')
            supp_name = next((name for name, bits in SUPPORT_BITS.items() if bits == supp_bits), 'unknown')
            opcode_name = next((name for name, info in INSTRUCTION_INFO.items() if info == (type_bits, funct_bits)), 'data')

            if type_bits == '11':
                target_payload = line[12:]
                if supp_name == 'na':
                    opcode_text = f"{opcode_name} {cond_name} r{int(target_payload[10:15], 2)}"
                else:
                    immediate = int(target_payload[-10:], 2)
                    if immediate >= 512:
                        immediate -= 1024
                    opcode_text = f"{opcode_name} {supp_name} {cond_name} {immediate}"
            else:
                rd = int(line[12:17], 2)
                rh = int(line[17:22], 2)
                if supp_name in ('i', 'is'):
                    immediate = int(line[22:], 2)
                    if immediate >= 512:
                        immediate -= 1024
                    opcode_text = f"{opcode_name} {supp_name} {cond_name} r{rd} = r{rh}, {immediate}"
                else:
                    ro = int(line[22:27], 2)
                    opcode_text = f"{opcode_name} {supp_name} {cond_name} r{rd} = r{rh}, r{ro}"

            decoded.append(f"Line {line_number}: {opcode_text}")

        return '\n'.join(decoded)
