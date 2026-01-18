# Language Notes

## Core features

- Integer variables and arithmetic.
- Conditionals (`if/else`) and loops (`while`).
- Functions with `int` and `void` return types.
- Built-in `input()` and `output(x)` helpers.

## Vectors (arrays)

Arrays are declared with a fixed size and accessed with `[]`.

```
int data[10];
int sum(int v[], int n) { ... }
```

Semantics:

- Array indexing uses word offsets (one word per element).
- Array parameters are passed by address.
- Array accesses inside a function using array parameters load from the
  parameter value itself (the passed-in address).

## Recursion

Functions can call themselves. This is supported for both `int` and `void`
functions.

```
int fact(int n) {
  if (n < 2) return 1;
  return n * fact(n - 1);
}
```
