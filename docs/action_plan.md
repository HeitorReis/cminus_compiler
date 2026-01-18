# Action Plan

This plan is based on the identified issues and focuses on correctness,
maintainability, and predictable behavior. Each item includes its motivation.

## Phase 1: Correctness and Semantics
- **Fix control-flow lowering for `if (x)` conditions.**
  - Motivation: current backend requires a prior comparison and fails when the
    condition is a plain expression; this can silently generate incorrect code.
  - Action: emit an explicit compare-to-zero in IR or handle it in codegen when
    `if_false` sees no prior comparison.
- **Formalize IR semantics in code and docs.**
  - Motivation: mismatched comments/behavior caused confusion and bugs.
  - Action: align comments, IR dump format, and codegen assumptions; add an IR
    reference in `docs/ir.md`.
- **Complete array semantics across all stages.**
  - Motivation: arrays are used in tests and require consistent behavior for
    declarations, indexing, passing to functions, and local storage.
  - Action: ensure array parameters are treated as pointers in IR, and array
    locals are allocated in stack frames with proper offsets.
- **Address return semantics for `main`.**
  - Motivation: returning from `main` is unreliable on the current ISA model;
    users reported returns not working correctly.
  - Action: define a termination strategy (e.g., `ret` as halt, or `b` to a
    fixed exit label) and document it; adjust codegen accordingly.

## Phase 2: Symbol and Scope Robustness
- **Introduce block scopes and shadowing rules.**
  - Motivation: current scope model only distinguishes global and function
    scope; nested blocks cannot safely declare variables.
  - Action: push/pop scopes for compound statements and adjust symbol lookup
    accordingly.
- **Harden function parameter type tracking.**
  - Motivation: parameter type mismatches lead to incorrect call checking.
  - Action: store exact parameter types (int/array) in the symbol table and
    validate against call sites.

## Phase 3: Memory and Resource Hygiene
- **Free symbol table and scope-stack allocations.**
  - Motivation: long or repeated runs leak memory.
  - Action: add destructor functions for symbols/lines and call them on exit.
- **Clarify ownership of identifier strings.**
  - Motivation: `strdup` is used in multiple layers without a single owner.
  - Action: centralize ownership in AST or symbol table to avoid leaks/double-free.

## Phase 4: Build and Testing Improvements
- **Separate `build` and `run` in the Makefile.**
  - Motivation: `make all` currently runs `clean` and `run`, preventing
    incremental builds and slowing iteration.
  - Action: provide explicit `build`, `run`, and `clean` targets.
- **Add an automated test runner.**
  - Motivation: no regression coverage for parser/semantic/IR/codegen.
  - Action: add a simple shell or Python test harness to run test files and
    compare expected outputs.

## Phase 5: Logging and Configuration
- **Add logging levels.**
  - Motivation: current verbose logs obscure errors and slow execution.
  - Action: gate debug output behind a macro/flag and provide a quiet mode.
- **Externalize output paths.**
  - Motivation: hard-coded `docs/output/*` makes integration harder.
  - Action: allow output directory overrides via CLI or environment variables.

