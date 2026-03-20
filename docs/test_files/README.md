# Test Files

This folder contains sample C-minus inputs used to exercise the current compiler pipeline.

## Canonical Samples Wired Into `make run`

- `sort.txt`
  - Selection sort using a global array and an array parameter
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

- `invalid_missing_return.txt`
  - Semantic-error sample for non-void return-path checking
- `testing.txt`
  - Human checklist, not compiler input

## Legacy Numeric Aliases

- `teste.txt`
  - Legacy alias for `sort.txt`
- `teste3.txt`
  - Legacy alias for `gcd.txt`
- `teste6.txt`
  - Legacy alias for `factorial.txt`
- `teste7.txt`
  - Legacy alias for `fibonacci.txt`

## Commands

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
- `make run_all` runs an explicit positive regression suite, including the named files above
- It does not include `invalid_missing_return.txt`

Manual invalid-case run:

```sh
make bin/c-c
bin/c-c docs/test_files/invalid_missing_return.txt
```
