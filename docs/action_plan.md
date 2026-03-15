# Action Plan

This plan reflects the codebase as it stands today.

## Phase 1: Fix Everyday Workflow Friction

- Add a real `build` target.
  - Motivation: `make` should not implicitly clean and run a sample program.
- Standardize on `python3` in all Make targets.
  - Motivation: the current split between `python` and `python3` causes avoidable failures.
- Add a short `help` target.
  - Motivation: the repository currently requires reading the `Makefile` to discover the safe commands.

## Phase 2: Tighten Correctness Boundaries

- Return a failing exit status when semantic analysis reports errors.
  - Motivation: shell scripts and test harnesses currently cannot trust process success.
- Preserve scalar global storage explicitly in IR and backend data allocation.
  - Motivation: global arrays are materialized clearly, but scalar globals are not represented as strongly.
- Replace backend text-pattern inference with a more explicit IR contract where practical.
  - Motivation: locals, parameters, and data ownership should not depend on ad hoc string scanning.

## Phase 3: Make Diagnostics Usable

- Add logging levels or compile-time debug flags.
  - Motivation: current debug output is useful for bring-up but too noisy for everyday use.
- Separate human-readable logs from machine-readable artifacts.
  - Motivation: output files under `docs/output/` currently mix products and diagnostics.

## Phase 4: Improve Resource Hygiene

- Add destruction paths for symbol-table allocations and scope-stack strings.
  - Motivation: the compiler currently assumes short-lived process lifetime.
- Clarify ownership of duplicated strings across AST, symbol table, and IR layers.
  - Motivation: the codebase still spreads allocation responsibility across several subsystems.

## Phase 5: Add Real Regression Checking

- Turn `run_all` into a pass/fail regression harness.
  - Motivation: it currently produces artifacts but does not verify behavior.
- Add expected-output fixtures for:
  - semantic failures
  - recursion
  - arrays
  - four-argument calls
  - literal-pool assembly
- Add CI for build plus regression runs.
  - Motivation: most current validation is still manual.
