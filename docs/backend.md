# Backend Documentation

## Code Generation (`codegen/codegen.py`)
- Parses IR to build function contexts.
- Performs register allocation with spill handling.
- Builds stack layout for parameters, locals, temporaries, and local arrays.
- Generates assembly for arithmetic, pointer loads/stores, calls, returns, and branches.

## Stack Layout
- Stack grows down (negative offsets from `fp`).
- Each variable maps to a base offset in `stack_layout`.
- Local arrays reserve multiple words in the stack frame.

## Assembly Generation
- Produces `.text` and `.data` sections.
- Emits function prologue/epilogue:
  - Saves/restores `lr` and `fp` for non-`main`.
  - Initializes `sp`/`fp` for `main`.
- Globals declared with `.word` or `.space`.

## Assembler (`codegen/assembler.py`)
- Encodes custom 32-bit instruction format described in
  `ImportantAdditionalText-ProcessorInformation.txt`.
- Supports conditional execution, immediate operands, and branch encoding.
- Handles large immediates using a literal pool.

