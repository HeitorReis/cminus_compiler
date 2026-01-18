# IR Documentation

## IR Concepts
- Three-address code with explicit temporaries (`t0`, `t1`, ...).
- Operands can be temporaries, constants, names, or labels.
- Control flow uses labels and conditional branches.

## Instruction Forms
- Assignment: `x := y`
- Binary op: `t := a + b`
- Relational op: `t := a < b`
- Address-of: `t := &x`
- Load: `t := *addr`
- Store: `*addr := v`
- Argument: `arg v`
- Call:
  - With return: `t := call f, N`
  - Without return: `call f, N`
- Return:
  - `return _` for void
  - `return v` for value
- Conditional branch (if-false): `if_false t goto L1`
- Unconditional branch: `goto L1`
- Label: `L1:`
- Array declaration: `arr := .space, N`

## Array Semantics
- Array access expands to:
  - `t0 := &arr`
  - `t1 := t0 + index`
  - `t2 := *t1`
- Array assignment expands to:
  - `t0 := &arr`
  - `t1 := t0 + index`
  - `*t1 := value`
- Passing arrays to functions:
  - Argument is the array base address: `t := &arr`, then `arg t`.

## Notes
- `.space` declarations within a function are treated as local array storage.
- `.space` declarations at global scope are translated into `.data` directives.

