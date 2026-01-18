# Processor ISA Reference

This table summarizes the instruction encoding and operation semantics as implemented in the Verilog sources under `processor_archive/modules/`.

## Encoding (32-bit)

```
[31:28] Cond    [27:26] Type  [25] I  [24] S  [23:20] Op  [20] L
[19:15] Rd      [14:10] Rh    [9:5] Ro      [9:0] imm10 (sign-extended)
```

- `Type`: `00` = Data Processing (DP), `01` = Data Transfer (MEM), `11` = Branch (BR)
- `I`: operand2 source (`0` = `Ro`, `1` = sign-extended `imm10`)
- `S`: update CPSR flags (Z, N) when condition passes
- `L`: load bit (only used for MEM)

## Condition Codes (Cond)

| Cond | Name | Meaning (uses CPSR flags) |
| --- | --- | --- |
| 0000 | AL | always |
| 0001 | EQ | Z = 1 |
| 0010 | NE | Z = 0 |
| 0011 | GT | Z = 0 and N = 0 |
| 0100 | GE | Z = 1 or N = 0 |
| 0101 | LT | N = 1 |
| 0110 | LE | Z = 1 or N = 1 |
| other | - | never |

## Data Processing (Type = 00)

`operand2 = (I == 1) ? signext(imm10) : Ro`

| Op | Mnemonic | Semantics (when Cond passes) |
| --- | --- | --- |
| 0000 | ADD | Rd = Rh + operand2 |
| 0001 | SUB | Rd = Rh - operand2 |
| 0010 | MUL | Rd = Rh * operand2 |
| 0011 | DIV | Rd = Rh / operand2 |
| 0100 | AND | Rd = Rh & operand2 |
| 0101 | OR  | Rd = Rh | operand2 |
| 0110 | XOR | Rd = Rh ^ operand2 |
| 0111 | NEG | Rd = -Rh |
| 1000 | MOV | Rd = operand2 |
| 1001 | IN  | Rd = peripheral_value; core halts until peripheral_signal |
| 1010 | OUT | output_reg = operand2 (Rd write still enabled) |

## Data Transfer (Type = 01)

`Ro` is always the memory address. `Rh` is the store data.

| L | Mnemonic | Semantics (when Cond passes) |
| --- | --- | --- |
| 1 | LDR | Rd = mem[Ro] |
| 0 | STR | mem[Ro] = Rh |

## Branch (Type = 11)

`branch_offset = (I == 1) ? signext(imm10) : Ro`

| Control bit | Meaning |
| --- | --- |
| bit23 = 1 | store link register (Link = current PC) |
| bit22 = 1 | branch to link register (PC = Link) |

Branch update (when Cond passes):
- If bit22 = 1: `PC = Link`
- Else: `PC = PC + branch_offset`

