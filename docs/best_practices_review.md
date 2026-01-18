# Best-Practices Review

This is a lightweight audit of the repository as it stands. It focuses on
engineering practices rather than language semantics.

## Gaps and risks

1) No automated test runner or CI workflow (including coverage for recursion and returns).
2) No LICENSE file or contribution guidelines.
3) Debug logging is always enabled in the compiler and codegen paths.
4) Generated outputs are checked in under `docs/output/`, which can drift
   and become stale.
5) No static analysis or sanitizers are configured (e.g., `-Wall`,
   `-Wextra`, `-fsanitize=address`).
6) Build scripts do not expose a release/debug mode separation.
7) No documented versioning or change log.

## Notes

- The current `Makefile` always cleans before building, which is convenient
  for local runs but makes incremental builds slower.
