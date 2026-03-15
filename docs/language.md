# Language Notes

## Supported Source Features

The current grammar and semantic pass support this subset of C-minus.

### Types

- `int`
- `void`
- Fixed-size integer arrays
- Array parameters written as `int a[]`

### Declarations

- Global variables
- Local variables
- Global arrays
- Local arrays
- Functions

There are no initializers in declarations.

### Statements

- Expression statements
- Compound statements
- `if`
- `if/else`
- `while`
- `return`
- Nested blocks with shadowing

### Expressions

- Assignment
- Function call
- Identifier reference
- Array indexing
- Integer literal
- Parenthesized expressions
- Binary arithmetic:
  - `+`
  - `-`
  - `*`
  - `/`
  - `%`
- Binary comparisons:
  - `==`
  - `!=`
  - `<`
  - `<=`
  - `>`
  - `>=`

Notable current omission:

- No unary minus operator in the grammar.

## Built-In Functions

These are injected before parsing:

- `input(): int`
- `output(int): void`

## Arrays

Current array model:

- Array elements are one word each
- Index expressions must be `int`
- Array parameters behave like base addresses
- Non-parameter arrays use explicit address-of IR before load/store

Example forms accepted by the parser:

```c
int data[10];

int sum(int a[], int n) {
    int i;
    int total;
    i = 0;
    total = 0;
    while (i < n) {
        total = total + a[i];
        i = i + 1;
    }
    return total;
}
```

## Return Rules

The semantic pass enforces:

- `void` functions may use `return;`
- Non-void functions must return an `int`
- Non-void functions must return on all paths according to the current AST walk

`main` is not treated specially by the parser or semantic pass, so both `int main(void)` and `void main(void)` parse today. The backend, however, treats `main` specially as the entry point and final halt path.

## Current Implementation Caveats

- `%` is lowered into `/`, `*`, and `-` during IR generation.
- Semantic errors stop IR generation, but the front-end currently still exits with parse success status.
- Global arrays are explicitly materialized in backend data.
- Global scalar storage across functions is not as strong a path as the array path and is not covered by the checked-in regression set.
