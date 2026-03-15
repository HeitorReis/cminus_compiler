# Best-Practices Audit

This audit reflects the repository as it behaves today, not the earlier intended design.

## What Is Already in Better Shape

- Nested block scopes and shadowing are implemented through the shared scope stack.
- Non-void return-path checking exists in semantic analysis.
- The backend handles more than three arguments by mixing register and stack passing.
- The assembler has support for large immediates and long branches through a literal pool.
- `make run_all` provides a lightweight batch regression pass.

## Current Gaps

### Build and Developer Ergonomics

- `make` is not a pure build. It runs `clean` and then the default program.
- There is no dedicated `build` target.
- `make run` uses `python`, while `make run_all` uses `python3`.
- `make clean` leaves `docs/output/` artifacts behind.

### Compiler Correctness and Contracts

- Semantic failures do not currently produce a failing process exit status.
- The front-end/backend contract is textual IR with no versioned schema.
- The backend reconstructs some semantic information by scanning IR text.
- Global scalar storage is weaker than global array storage because only explicit IR data directives are materialized in backend global data.

### Logging and Observability

- Debug tracing is always enabled in lexer, parser, AST, semantic analysis, IR generation, and backend codegen.
- Normal successful runs produce very large logs.
- There is no logging level control.

### Memory and Resource Hygiene

- The symbol table and scope-stack storage are not fully torn down at the end of a run.
- Ownership of duplicated strings remains spread across parser, AST, symbol table, and IR objects.

### Testing

- There is no pass/fail harness that compares expected outputs.
- `run_all` only executes inputs and captures artifacts; it does not assert correctness.
- There is no CI configuration.

### Repository Hygiene

- Generated outputs are kept under `docs/output/`, which makes drift easy.
- Documentation had previously drifted from implementation details, especially around build/run behavior and remaining limitations.
