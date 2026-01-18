# Best-Practices Audit

This file lists areas where the project does not currently follow common
compiler and software-engineering best practices.

## Architecture and Correctness
- IR semantics are not formally specified in code; `IR_IF_GOTO` behavior is
  encoded in multiple places and historically differed from comments.
- Control-flow lowering relies on implicit state (`last_comparison`) in the
  backend, which is brittle and fails for `if (x)`-style conditions.
- Function parameter handling is inferred from IR text patterns instead of a
  formal symbol table pass.
- Program termination semantics for `main` are not explicitly defined, leading
  to uncertainty about correct return behavior.

## Memory and Resource Management
- Symbol table allocations and scope-stack storage are never freed.
- Lexer-allocated identifier strings are owned by AST/symbol table without a
  centralized ownership strategy.

## Error Handling and Reporting
- Parsing/semantic errors are printed but not summarized consistently.
- Some errors still allow later phases to run if not guarded.

## Build and Configuration
- `make all` runs `clean` and `run`, which prevents incremental builds.
- Output paths are hard-coded (`docs/output/*`).

## Logging and Debugging
- Verbose debug output is always enabled in many components.
- No structured logging levels (error/warn/info/debug).

## Testing and Validation
- No automated test harness or CI for parser/semantic/IR/codegen/assembler.
- Test inputs exist but are not executed as part of a test suite.

## Portability and Hygiene
- Generated binaries and intermediate files are mixed with source outputs.
- Some behavior relies on specific tool versions (`python3.10`).
