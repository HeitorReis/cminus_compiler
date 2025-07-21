import sys
sys.path.append('codegen')
from codegen.assembler import FullCode

def assemble(lines):
    fc = FullCode(lines)
    assert fc.response == '-> Success'
    return fc

def test_space_addresses():
    asm = [
        '.data',
        'space: .space 2',
        'var1: .word 1',
        'var2: .word 2',
    ]
    fc = assemble(asm)
    assert fc.symbol_table['space'] == fc.data_section_start_address
    assert fc.symbol_table['var1'] == fc.symbol_table['space'] + 2
    assert fc.symbol_table['var2'] == fc.symbol_table['var1'] + 1

def test_space_output_count():
    asm = [
        '.data',
        'buf: .space 0x3',
        'val: .word 5',
    ]
    fc = assemble(asm)
    # number of binary words equals spaces + explicit words
    assert fc.full_code.count("\n") == 4