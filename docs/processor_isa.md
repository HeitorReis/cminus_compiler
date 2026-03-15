# Processor ISA Reference

This document reflects the instruction syntax and encoding rules implemented by `codegen/assembler.py`.

## Source Format Accepted by the Assembler

The assembler reads a simple textual assembly language with:

- `.text`
- `.global <symbol>`
- `.data`
- labels ending with `:`
- data directives:
  - `.word <value>`
  - `.space <count>`

Examples:

```text
addi: r4 = r31, 3
subi: r30 = r31, 1
load: r5 = [r30]
store: [r30] = r4
bi: main
b: r28
out: r1
in: r4
ret:
```

## Instruction Name Structure

The assembler splits an instruction mnemonic into:

- base opcode
- optional condition suffix
- optional support suffix

### Condition Suffixes

- `do`
  - unconditional default
- `eq`
- `neq`
- `gt`
- `gteq`
- `lt`
- `lteq`

### Support Suffixes

- `na`
  - register form
- `i`
  - immediate form
- `s`
  - flag-setting form
- `is`
  - immediate plus flag-setting form

Examples:

- `add`
- `addi`
- `subs`
- `movi`
- `bineq`

## Encoded Layout

The assembler encodes 32-bit words in this order:

```text
[31:28] condition
[27:26] type
[25:24] support bits
[23:20] function/opcode
[19:15] rd
[14:10] rh
[9:0]   immediate or register payload
```

Branches use the lower payload bits differently from data-processing instructions.

## Implemented Base Opcodes

Data processing:

- `add`
- `sub`
- `mul`
- `div`
- `and`
- `or`
- `xor`
- `not`
- `mov`
- `in`
- `out`

Memory:

- `load`
- `store`

Branch:

- `b`
- `bl`

## Branch Model

- Branch targets may be labels, signed numeric offsets, or registers.
- Label branches are encoded as PC-relative offsets when they fit in the 10-bit signed range.
- Out-of-range label branches are expanded into:
  - move target address into scratch register `r27`
  - branch via register

## Immediate Model

- Signed immediates are limited to 10 bits
- Large immediates are placed in a literal pool at the end of the data section
- The assembler emits:
  - a move of the literal address into `r27`
  - a load from `[r27]`

## Data Directives

The current backend emits:

- `stack_space: .space 256`
- one `.space` per global array
- `.word` entries when the backend symbol table contains scalar globals

## Pseudo-Instructions

- `ret:`
  - parsed specially by the assembler
  - lowered to `bi 0`

That matches the backend's use of `ret:` as the end-of-program halt path for `main`.
