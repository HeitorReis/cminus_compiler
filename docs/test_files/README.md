# Test Files

This folder contains sample C-minus inputs used to exercise the current compiler pipeline.

## Samples Wired Into `make run`

- `teste.txt`
  - Selection sort using a global array and an array parameter
- `teste2.txt`
  - Global array reads, writes, and arithmetic
- `teste3.txt`
  - Recursive GCD
- `teste4.txt`
  - Recursive halving with intermediate outputs
- `teste5.txt`
  - Void recursion with countdown behavior
- `teste6.txt`
  - Recursive factorial
- `teste7.txt`
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

- `invalid_missing_return.txt`
  - Semantic-error sample for non-void return-path checking
- `testing.txt`
  - Human checklist, not compiler input

## Commands

Run one mapped sample:

```sh
make run TEST=2
```

Run all mapped regression samples:

```sh
make run_all
```

Important current behavior:

- `make run_all` only matches `teste*.txt`
- It does not include `invalid_missing_return.txt`
- `make run` currently uses `python`, so on `python3`-only systems the manual flow is more reliable

Manual invalid-case run:

```sh
make bin/c-c
bin/c-c docs/test_files/invalid_missing_return.txt
```
