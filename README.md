# C-minus Compiler

This repository implements a C-minus compiler with a split pipeline:

- A C front-end built with Flex and Bison.
- A Python backend that lowers textual IR into assembly and then into machine code.

## Current Workflow

The project does not currently have a dedicated `build` target. The practical entry points are:

- `make`
  - Runs `clean` and then `run` on the default sample program.
  - This is a full pipeline command, not a build-only command.
- `make bin/c-c`
  - Builds only the front-end executable.
- `make run TEST=N`
  - Runs one of the wired sample inputs from `docs/test_files/`.
  - The current `run` target invokes `python`, so it assumes a `python` executable is available.
- `make run_all`
  - Cleans, rebuilds, and runs every `docs/test_files/teste*.txt`.
  - This target already uses `python3`.

If your environment only provides `python3`, the most reliable manual flow is:

```sh
make bin/c-c
bin/c-c docs/test_files/teste3.txt > docs/output/log_compiler.txt
python3 -u codegen/main.py > docs/output/log_codegen.txt
```

## Pipeline

1. `bin/c-c <input_file>`
   - Initializes built-in symbols `input()` and `output(int)`.
   - Parses the source into an AST.
   - Prints the symbol table and AST for debugging.
   - Runs semantic analysis.
   - Emits `docs/output/generated_IR.txt` only when semantic analysis succeeds.
2. `python3 codegen/main.py`
   - Reads `docs/output/generated_IR.txt`.
   - Generates `docs/output/generated_assembly.txt`.
   - Assembles into `docs/output/generated_machine_code.txt`.
   - Writes a decoded machine-code log to `docs/output/debug_machine_code.txt`.

The C and Python halves communicate through the IR text file rather than through a shared in-memory representation.

## Current Language Coverage

The checked-in tests exercise the following features:

- `int` and `void` functions
- Local and global declarations
- Fixed-size integer arrays
- Array parameters (`int a[]`)
- Nested block scopes with shadowing
- `if`, `if/else`, and `while`
- Recursion
- Built-ins `input()` and `output(x)`
- Arithmetic `+`, `-`, `*`, `/`, `%`
- Comparisons `==`, `!=`, `<`, `<=`, `>`, `>=`

## Outputs

Main pipeline outputs are written under `docs/output/`:

- `generated_IR.txt`
- `generated_assembly.txt`
- `generated_machine_code.txt`
- `debug_machine_code.txt`
- `log_compiler.txt`
- `log_codegen.txt`

`make clean` removes `build/`, `bin/`, `parser.gv`, and `parser.output`, but it does not remove files under `docs/output/`.

## Repository Layout

- `main.c`
  - Front-end entry point.
- `parser/`
  - Flex lexer and Bison grammar.
- `src/`
  - AST, symbol table, scope stack, semantic analysis, and IR generation.
- `codegen/`
  - Python code generator, assembler, and backend symbol helpers.
- `docs/test_files/`
  - Sample input programs.
- `docs/output/`
  - Generated artifacts and logs.

## Current Caveats

- Debug logging is always enabled across the front-end and backend.
- `make run` uses `python`, while `make run_all` uses `python3`.
- Semantic errors prevent IR generation, but the front-end process still exits based on parse success, not semantic success.
- Global arrays are materialized in the backend data section. Global scalar storage is a weaker path today and is not covered by the checked-in regression set.
