# Updated Audit of `Processor(v2026-1)` Branch, Branch-to-Register, and Branch-and-Link Logic

## Summary

This document describes the **current** branch implementation in `Processor(v2026-1)` after the RTL adjustment that:

- keeps immediate-form branch as **PC-relative**
- changes register-form branch to **direct branch to register**
- changes branch-and-link to save **PC+1**
- keeps a dedicated link register and a dedicated return instruction that branches to that saved link value

The source of truth for this explanation is the Verilog in:

- `Processor(v2026-1)/integrated.v`
- `Processor(v2026-1)/Processor.v`
- `Processor(v2026-1)/modules/ControlUnit.v`
- `Processor(v2026-1)/modules/PC_main.v`
- `Processor(v2026-1)/modules/registerBank.v`
- `Processor(v2026-1)/modules/ALUControl.v`
- `Processor(v2026-1)/modules/alu.v`

Project-level Quartus details:

- top-level entity: `Processor`
- family/device: Cyclone IV E / `EP4CE115F29C7`
- instruction memory initialization file: `Processor(v2026-1)/modules/single_port_rom_init.txt`
- instruction memory depth: 1024 words
- data memory depth: 64 words

---

## 1. Branch datapath

The active control-flow datapath is:

```text
InstructionMemory
  -> current instruction
  -> ControlUnit
       - TypeCode
       - CondField
       - is_immediate
       - should_branch
       - should_store_link
       - should_branch_to_link
       - Ro / Rh / Rd
  -> registerBank
       - RoValue
       - LinkValue
  -> ALUControl
       - operand2 = immediate or RoValue
  -> ALU
       - for Type=11, result = operand2
  -> registerBank write path
       - if should_store_link and condition passes:
           LinkRegister <= current_instr_addr + 1
  -> PC_main
       - if condition passes and branch is active:
           - if should_branch_to_link: PC <= link_value
           - else if is_immediate:     PC <= PC + branch_value
           - else:                     PC <= branch_value
       - else:
           PC <= PC + 1
```

### Practical meaning

The processor now supports three distinct branch target forms:

1. **Immediate branch**
   - `PC := PC + offset`
2. **Register branch**
   - `PC := register_value`
3. **Return branch**
   - `PC := saved_link_value`

---

## 2. Bit-level control decode

The branch control logic still comes from `ControlUnit.v`:

- `TypeCode = instruction[27:26]`
- `should_branch = instruction[27] & instruction[26]`
- `should_store_link = instruction[27] & instruction[26] & instruction[23]`
- `should_branch_to_link = instruction[27] & instruction[26] & instruction[22]`
- `is_immediate = instruction[25]`

So branch behavior is decided by:

- `Type[27:26]`
- `Supp[25]`
- `Funct[23]`
- `Funct[22]`

The lower function bits remain unused by the branch datapath.

### Effective branch classes

| Type | `i` bit | Funct[23] | Funct[22] | Link write | PC behavior |
| --- | --- | --- | --- | --- | --- |
| `11` | `1` | `0` | `0` | no | `PC := PC + immediate` |
| `11` | `0` | `0` | `0` | no | `PC := RoValue` |
| `11` | `1` | `1` | `0` | yes | `Link := PC+1`, then `PC := PC + immediate` |
| `11` | `0` | `1` | `0` | yes | `Link := PC+1`, then `PC := RoValue` |
| `11` | `x` | `0` | `1` | no | `PC := LinkValue` |
| `11` | `x` | `1` | `1` | yes | `Link := PC+1`, then `PC := LinkValue` |

### Important note

The return path is still a **dedicated branch-to-link-register instruction**. The processor does not use a general-purpose register as the hardware link register.

---

## 3. Timing and update order

The relevant timing points are:

- `InstructionMemory` updates instruction on `posedge fast_clock`
- `registerBank` updates read outputs on `posedge fast_clock`
- `registerBank` writes registers and link register on `posedge clock`
- `PC_main` updates PC on `negedge clock`
- `CPSRegister` updates flags on `negedge clock`

### Branch timing

```text
Before posedge clock:
  - instruction is already visible
  - RoValue and LinkValue are already visible
  - write_condition is already resolved from CondField and CPSR flags

At posedge clock:
  - if write_condition & should_store_link:
      LinkRegister <= current_instr_addr + 1

At negedge clock:
  - if write_condition & should_branch:
      - if should_branch_to_link:
          PC <= link_value
      - else if is_immediate:
          PC <= current_PC + branch_value
      - else:
          PC <= branch_value
  - else:
      PC <= current_PC + 1
```

### Consequences

#### 3.1 Saved link is now `PC+1`

The saved link value comes from:

```text
new_LinkValue(current_instr_addr + 1)
```

So the branch-and-link instruction now saves the address of the next sequential instruction in processor word-address space.

#### 3.2 Immediate branch is still PC-relative

If `is_immediate = 1`, the processor still uses:

```text
PC := current_PC + immediate
```

#### 3.3 Register branch is now absolute

If `is_immediate = 0` and the instruction is not the dedicated branch-to-link-register form, the processor now uses:

```text
PC := RoValue
```

This is the key logic change in the processor.

---

## 4. Concrete control-flow cases

### 4.1 Immediate branch

Conditions:

- `Type = 11`
- `is_immediate = 1`
- `Funct[22] = 0`
- condition passes

Behavior:

1. `ALUControl` selects the sign-extended immediate
2. `ALU` forwards it as `branch_value`
3. `PC_main` performs `PC := PC + branch_value`

Semantics:

```text
branch by offset
```

---

### 4.2 Branch to general register

Conditions:

- `Type = 11`
- `is_immediate = 0`
- `Funct[22] = 0`
- condition passes

Behavior:

1. `ALUControl` selects `RoValue`
2. `ALU` forwards it as `branch_value`
3. `PC_main` performs `PC := branch_value`

Semantics:

```text
branch to register
```

This is no longer a PC-relative branch.

---

### 4.3 Branch-and-link with immediate target

Conditions:

- `Type = 11`
- `is_immediate = 1`
- `Funct[23] = 1`
- `Funct[22] = 0`
- condition passes

Behavior:

1. `registerBank` stores `LinkRegister := current_instr_addr + 1`
2. `PC_main` performs `PC := PC + immediate`

Semantics:

```text
save return point and branch by offset
```

---

### 4.4 Branch-and-link with register target

Conditions:

- `Type = 11`
- `is_immediate = 0`
- `Funct[23] = 1`
- `Funct[22] = 0`
- condition passes

Behavior:

1. `registerBank` stores `LinkRegister := current_instr_addr + 1`
2. `PC_main` performs `PC := RoValue`

Semantics:

```text
save return point and branch to register
```

---

### 4.5 Return to saved link point

Conditions:

- `Type = 11`
- `Funct[22] = 1`
- condition passes

Behavior:

1. `PC_main` ignores the general branch operand
2. `PC_main` performs `PC := LinkValue`

Semantics:

```text
return / branch to saved link register
```

This is the instruction that returns to the point previously saved by branch-and-link.

---

## 5. Link register model

The processor still uses a **dedicated link register** inside `registerBank.v`:

- it is not one of the 32 general-purpose registers
- it is written through `store_link_signal`
- it is read through `LinkValue`

### What branch-and-link saves

The saved value is:

```text
current_instr_addr + 1
```

### What return uses

The return path reads:

```text
LinkValue
```

So the call/return pair is:

```text
branch-and-link -> save PC+1 in dedicated link register
branch-to-link  -> load PC from dedicated link register
```

---

## 6. Compiler and simulator interface

The compiler emits one 32-bit binary word per line in:

```text
docs/generated/final/assembler/machine_code/generated_machine_code.txt
```

For the Quartus processor path, these words must be copied or transformed into the ROM initialization file used by `InstructionMemory.v`:

```text
Processor(v2026-1)/modules/single_port_rom_init.txt
```

The Python runner in `tools/run_machine_code.py` models the same branch/link behavior described above. It is intentionally useful as a fast software check before loading the machine code into the Verilog ROM.

### Top-level interaction signals

| Signal | Current meaning |
| --- | --- |
| `SW[16]` | reset |
| `SW[15]` | peripheral input release signal for `in`; release occurs on falling edge while halted |
| `SW[17]` | clock pause gate in `Processor.v` |
| `SW[7:0]` | input value for `in` |
| `LEDR[0]` | `write_condition` from the CPSR condition verifier |
| `output_value` / `HEX6-HEX7` | last value written by `out` |
| `pc` / `HEX0-HEX3` | current instruction address |

### Register convention used by the compiler

The assembly backend uses `r28` as a logical link register name in generated assembly. In the RTL, however, `bl` writes a dedicated hardware `LinkRegister` inside `registerBank.v`, and `PC_main.v` can return through that dedicated link path when `should_branch_to_link` is active. This distinction matters when reading generated assembly versus hardware control signals:

- `b: r28` is a register-form branch to the value stored in general register `r28`;
- branch-to-link is a separate hardware branch class controlled by `Funct[22]`;
- `bl` stores `PC+1` in the dedicated link register when the branch condition passes.

---

## 7. Effect on previous audit findings

The following earlier findings are no longer true after the RTL fix:

- register-form branch is **not** `PC + register` anymore
- saved link is **not** the current PC anymore

The following hardware properties remain true:

- the processor still has a dedicated link register
- the lower two branch function bits are still not used by the control datapath
- condition gating still blocks both branch execution and link write when the condition fails

---

## 8. Remaining processor-side caveat

The branch class with:

- `Funct[23] = 1`
- `Funct[22] = 1`

still means:

```text
save link and branch to LinkValue
```

Because `LinkRegister` is written on `posedge clock` and `LinkValue` is refreshed separately on `posedge fast_clock`, this combined form is still less clear than the standard pair:

1. branch-and-link
2. later branch-to-link

For normal call/return behavior, the clean processor path remains:

- use `bl`-style encoding to save `PC+1`
- use the branch-to-link-register instruction to return

---

## Final processor behavior

The processor branch subsystem now behaves as follows:

- **Immediate bit on**
  - branch target is relative: `PC + immediate`
- **Immediate bit off**
  - branch target is direct: `register value`
- **Link bit on**
  - the dedicated link register stores `PC + 1`
- **Branch-to-link bit on**
  - the PC loads the dedicated saved link value

That gives the processor a coherent hardware model for:

- branch by immediate offset
- branch to general register
- branch-and-link with saved return point
- return to the saved point
