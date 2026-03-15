# Backend Documentation

## Overview

The backend is implemented in Python and consists of two layers:

- `codegen/codegen.py`
  - Translates IR text into assembly
- `codegen/assembler.py`
  - Encodes assembly into 32-bit machine code

`codegen/main.py` is the bridge script that reads the IR file, writes assembly, and writes machine code.

## Code Generation Flow

### Pass 1A: Collect Functions

The backend scans the IR for top-level labels that do not start with `L`.

Each such label creates a `FunctionContext`.

### Pass 1B: Collect Global Data

The backend scans IR assignments looking for:

- `.space`
- `.word`

and builds a Python-side symbol table for global data.

Current implementation detail:

- Global arrays are supported because the front-end emits `.space` for them.
- Global scalar variables are weaker because the front-end does not currently emit explicit `.word` directives for them.

### Pass 2: Lower Each Function

For each function, the backend:

- Isolates the function's IR slice
- Collects parameter names from `param` lines
- Infers locals and temporaries by scanning identifiers
- Builds a stack layout
- Translates IR line by line into assembly

## Register Model

Named special registers in the backend are:

- `r0`
  - Return-value register
- `r1` to `r3`
  - Fast argument registers
- `r27`
  - Literal-pool scratch register
- `r28`
  - Link register
- `r29`
  - Stack pointer
- `r30`
  - Spill and frame-address scratch register
- `r31`
  - Frame pointer

General allocation pool:

- `r4` to `r11`
- `r12` to `r26`

The allocator tracks:

- Variable-to-register mappings
- Dirty registers
- Least-recently-used order
- Spilled temporaries

## Stack Layout

The backend uses frame-pointer-relative addressing.

Current layout rules:

- Up to three parameters arrive in `r1` to `r3`
- Those fast parameters are immediately spilled into negative offsets from `fp`
- Additional parameters are left at positive offsets from `fp`
- Local scalars consume one word each
- Local arrays reserve `N` words
- Spilled temporaries also get stack slots as needed

Frame-address code is emitted with:

- `addi` when offset is positive
- `subi` when offset is negative
- `mov` when offset is zero

## Calls and Returns

### Calls

Before a call, the backend:

- Spills dirty non-temporary values
- Spills live temporaries to stack slots
- Moves up to three arguments into `r1` to `r3`
- Pushes remaining arguments onto the stack

Built-ins:

- `input`
  - Lowers to `in`
- `output`
  - Lowers to `out` using `r1`

User-defined calls:

- The caller materializes a synthetic return label
- Moves it into `lr`
- Branches with link using `bl`
- Copies `r0` into the requested destination temporary after return

### Returns

For `return value`:

- The value is moved into `r0`
- Control branches to `<function>_epilogue`

For `return _`:

- Control branches straight to the epilogue

`main` is special:

- It initializes `sp` and `fp`
- Its epilogue ends with `ret:`

Non-`main` functions:

- Save `lr` and `fp`
- Restore them in the epilogue
- Return via `b: r28`

## Data Section

The final assembly always contains:

- `.data`
- `stack_space: .space 256`

Additional directives are emitted for backend-known globals:

- Global arrays become `.space N`
- Global integers would become `.word 0` if they are present in the backend symbol table

## Assembler Behavior

`codegen/assembler.py` supports:

- `.text`, `.global`, `.data`
- Labels
- Arithmetic/data-processing instructions
- `load` and `store`
- Branches to labels or registers
- `ret:` as a pseudo-instruction
- `.word` and `.space`

Important implementation details:

- Immediate fields are 10-bit signed
- Large immediates are lowered through a literal pool
- Out-of-range label branches are expanded into a move-to-scratch plus branch-by-register sequence
- A decoded debug view of the machine code is written after assembly

## Current Caveats

- The backend infers some semantics from text rather than from a typed IR object model.
- Scalar global handling is less robust than array-global handling.
- Debug logging is always enabled, so generated logs are intentionally noisy.
