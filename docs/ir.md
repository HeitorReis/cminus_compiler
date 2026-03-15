# IR Documentation

## Role of the IR

The IR is the contract between the C front-end and the Python backend.

It is:

- Three-address style
- Textual rather than binary
- Written to `docs/output/generated_IR.txt`
- Re-parsed by `codegen/codegen.py`

The backend relies on both the syntax of the IR and some positional conventions, so keeping the IR format stable matters.

## Operand Kinds

The front-end IR generator models operands as:

- Empty
- Temporary
- Constant
- Name
- Label

In the printed IR, these appear as:

- `_`
- `t0`, `t1`, ...
- `0`, `1`, `42`, ...
- `x`, `main`, `output`
- `L0`, `L1`, ...

## Instruction Forms

Current printed forms include:

- Label
  - `main:`
  - `L0:`
- Formal parameter
  - `param x`
- Simple assignment
  - `x := y`
  - `x := 7`
- Arithmetic
  - `t0 := a + b`
  - `t1 := x / 2`
- Comparison
  - `t2 := a < b`
  - `t3 := x == 0`
- Address-of
  - `t4 := &arr`
- Load through address
  - `t5 := *t4`
- Store through address
  - `*t4 := value`
- Argument
  - `arg x`
- Function call with return value
  - `t6 := call gcd, 2`
- Procedure call without return value
  - `call output, 1`
- Return
  - `return _`
  - `return x`
- Conditional branch
  - `if_false t0 goto L1`
- Unconditional branch
  - `goto L2`
- Array declaration
  - `arr := .space , 10`

Spacing in the `.space` form comes from the generic printer path and is expected by the current backend parser.

## Generation Rules

### Functions

Each function is emitted as:

1. A function label
2. Zero or more `param` lines
3. Body instructions
4. A trailing `return _` inserted by the IR generator

Unreachable instructions after `goto` or `return` are stripped until the next label.

### Conditionals and Loops

- `if` and `while` conditions are emitted as expressions that produce a temporary
- The actual branch instruction is `if_false`
- The backend uses the most recent comparison operator when available
- If no comparison metadata is available, the backend falls back to comparing the condition result against zero

### Arrays

Array behavior depends on whether the symbol is a real array object or an array parameter.

For a non-parameter array access:

1. Compute the index expression
2. Get the base address with `&arr`
3. Add index to base
4. Load or store through the resulting address

For an array parameter access:

- The parameter value is already treated as the base address
- No extra `&arr` is emitted

### Modulo

`%` is lowered in IR generation rather than handled as a native backend operation:

```text
t_div := a / b
t_mul := t_div * b
t_res := a - t_mul
```

## Global and Local Data

Current data emission behavior:

- Arrays emit explicit `.space` declarations
- Local array declarations stay inside the function IR
- Global array declarations appear before function bodies
- Scalar globals do not currently emit an explicit `.word` from the front-end

That last detail matters because the backend only allocates explicit global data directives that it can observe in the IR text.

## Current Caveats

- The backend still reconstructs some semantic meaning by scanning IR text.
- The IR does not carry a fully explicit typed symbol table.
- The printed form is stable enough for the current backend, but it is not yet a formally versioned interface.
