# Usage Guide

## Build

```
make
```

## Run the compiler

```
make run TEST=1
```

Available test inputs live in `docs/test_files/` and are selected by the `TEST`
value in the `Makefile`. The run target produces:

- `docs/output/log_compiler.txt` (front-end output)
- `docs/output/generated_IR.txt`
- `docs/output/log_codegen.txt` (codegen output)
- `docs/output/generated_assembly.txt`
- `docs/output/generated_machine_code.txt`

## End-to-end pipeline

1) Front-end parses and type-checks source into the AST.
2) IR is generated into `docs/output/generated_IR.txt`.
3) Python codegen translates IR to assembly in `docs/output/generated_assembly.txt`.
4) The assembler emits machine code in `docs/output/generated_machine_code.txt`.

## Adding new tests

Place a `.txt` file in `docs/test_files/` and wire it into the `Makefile`
`TEST` selector to include it in `make run`.
