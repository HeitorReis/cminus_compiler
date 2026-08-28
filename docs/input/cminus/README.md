# Test Files

This folder contains sample C-minus inputs used to exercise the current compiler pipeline.

## Canonical Samples Wired Into `make run`

- `sort.txt`
  - Selection sort using a global array and an array parameter
- `teste.txt`
  - Simple loop/output fixture used by `TEST=1` and `TEST=teste`
- `teste2.txt`
  - Global array reads, writes, and arithmetic
- `gcd.txt`
  - Recursive GCD
- `teste4.txt`
  - Recursive halving with intermediate outputs
- `teste5.txt`
  - Void recursion with countdown behavior
- `factorial.txt`
  - Recursive factorial
- `fibonacci.txt`
  - Recursive Fibonacci
- `teste8.txt`
  - Modulo lowering regression
- `teste9.txt`
  - Four-argument call with stack-passed extra parameters
- `teste10.txt`
  - Large immediate that exercises literal-pool assembly
- `teste11.txt`
  - Nested block scope with shadowing

## Files Not Wired Into `make run`

- `invalid_lexical_error.txt`
  - Negative lexical sample; the lexer must report an unexpected character and the pipeline must stop before AST/IR generation
- `invalid_syntax_error.txt`
  - Negative syntax sample; Bison must report a syntax error and semantic analysis must not run
- `invalid_undeclared_identifier.txt`
  - Semantic-error sample for use of an identifier that cannot be resolved in the active scope chain
- `invalid_missing_return.txt`
  - Semantic-error sample for non-void return-path checking
- `invalid_missing_main.txt`
  - Semantic-error sample for programs without a global `main` function

These invalid files are exercised by `make test_analysis` through `tools/run_analysis_regressions.py`, not by the positive `make run_all` suite.

## Legacy Numeric Aliases

- `teste3.txt`
  - Legacy alias for `gcd.txt`
- `teste6.txt`
  - Legacy alias for `factorial.txt`
- `teste7.txt`
  - Legacy alias for `fibonacci.txt`

## Commands

Run the focused ten-test suite added in the numbered files:

```sh
make run_selected_10
```

This runs only `01_soma_1_ate_n.txt` through `10_carga_preempcao.txt` and saves their machine-code files in:

```text
docs/generated/batch/selected_10_machine_code/
```

Use `make run_numbered_tests` or `make run_10` as aliases. Per-test compiler and code-generator logs are saved in `docs/generated/batch/selected_10_diagnostics/`.

Run the fixed FPGA diagnostic vectors and compare the expected output with the Python processor model:

```sh
make run_selected_10_diagnostics
```

The reports are written to `docs/generated/batch/selected_10_fpga_diagnostics/`. For each input value, set `SW[7:0]` and release the blocked `input()` with the `SW[15]` transition from `1` to `0`. `HEX6`/`HEX7` show only the last output's two least-significant decimal digits, so record every `output()` for tests with multiple values.

Generate a Quartus ROM image for each of the ten selected tests:

```sh
make generate_mif
```

This creates `program1.mif` through `program10.mif` inside `processor/Processor/modules/`. First refresh the selected suite if needed, then choose which one will be used by the FPGA:

```sh
make run_selected_10
make generate_mif
make select_mif ROM_PROGRAM=1
```

`ROM_PROGRAM=1` maps to `01_soma_1_ate_n`, and so on through `ROM_PROGRAM=10` for `10_carga_preempcao`. The selected file is copied to `program.mif`, which has exactly 1024 32-bit words and pads unused addresses with zero.

Run one mapped sample:

```sh
make run TEST=2
```

Run one named sample:

```sh
make run TEST=sort
make run TEST=gcd
make run TEST=factorial
make run TEST=fibonacci
```

Run all mapped regression samples:

```sh
make run_all
```

Current behavior:

- `make run` accepts both numeric selectors and the canonical names above
- `TEST=1` selects `teste.txt`, while the default empty selector still runs `sort.txt`
- `make run_all` runs an explicit positive regression suite, including the named files above

Manual invalid-case run:

```sh
make bin/c-c
bin/c-c docs/input/cminus/invalid_missing_return.txt
```

The compiler should leave `docs/generated/intermediate/semantic/ir/generated_IR.txt` absent for lexical, syntactic, and semantic failures.
