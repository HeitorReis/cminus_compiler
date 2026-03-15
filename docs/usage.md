# Usage Guide

## Fastest Commands

### Run the default sample end to end

```sh
make
```

Current behavior:

- `make` runs `clean` and then `run`
- The default input is `docs/test_files/teste.txt`
- This is not a build-only command

### Build only the front-end executable

```sh
make bin/c-c
```

### Run one wired sample

```sh
make run TEST=3
```

Useful sample selectors:

- `TEST=1`
  - selection-sort sample using a global array
- `TEST=8`
  - modulo lowering
- `TEST=9`
  - four-argument call and stack arguments
- `TEST=10`
  - large immediate and literal-pool behavior
- `TEST=11`
  - nested block scope and shadowing

Important caveat:

- The current `run` target invokes `python`, not `python3`
- If your machine only has `python3`, run the frontend and backend manually instead

### Run every checked-in regression sample

```sh
make run_all
```

`run_all` currently executes every `docs/test_files/teste*.txt` and stores per-test logs and machine-code outputs under `docs/output/all_machine_codes/`.

## Manual Workflow

For the most reliable environment-independent flow:

```sh
make bin/c-c
bin/c-c docs/test_files/teste3.txt > docs/output/log_compiler.txt
python3 -u codegen/main.py > docs/output/log_codegen.txt
```

Replace `docs/test_files/teste3.txt` with any source file path.

## What Each Step Produces

Frontend run:

- prints parser, AST, symbol-table, semantic, and IR debug output
- writes `docs/output/generated_IR.txt` when semantic analysis succeeds

Backend run:

- writes `docs/output/generated_assembly.txt`
- writes `docs/output/generated_machine_code.txt`
- writes `docs/output/debug_machine_code.txt`

Common log files:

- `docs/output/log_compiler.txt`
- `docs/output/log_codegen.txt`

## Invalid-Test Workflow

`invalid_missing_return.txt` is not wired into `make run` or `make run_all`.

Run it manually with:

```sh
bin/c-c docs/test_files/invalid_missing_return.txt
```

Current behavior to be aware of:

- The semantic error is reported
- IR generation is skipped
- The process still exits as if parsing succeeded

## Cleaning

```sh
make clean
```

This removes:

- `build/`
- `bin/`
- `parser.gv`
- `parser.output`

It does not remove files under `docs/output/`.
