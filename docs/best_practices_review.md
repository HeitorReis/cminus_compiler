# Best-Practices Review

This is the current short-form review of the repository after the recent scope, IR, and backend changes.

## Primary Findings

1. The default `make` target is surprising.
   - It cleans and runs the default test instead of providing an incremental build.
2. Python invocation is inconsistent.
   - `make run` depends on `python`.
   - `make run_all` depends on `python3`.
3. Semantic failure is not reflected in the process exit code.
   - The compiler skips IR generation on semantic errors, but `main.c` still returns based on parse success.
4. The backend still infers too much from IR text.
   - Parameters, locals, and some storage decisions are reconstructed by scanning strings.
5. Global scalar handling is weaker than it looks from the source language.
   - The backend only allocates explicit global data directives it sees in IR.
6. Verbose debugging is permanently on.
   - This is useful during development but weak for repeatable tests and normal usage.

## Positive Notes

- Nested block-scope resolution is implemented and exercised by `teste11.txt`.
- Return-path analysis for non-void functions is implemented and exercised by `invalid_missing_return.txt`.
- Four-argument calls and large immediates now have dedicated regression inputs.
