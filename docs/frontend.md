# Front-End Documentation

## Overview

The front-end owns the source-language side of the compiler:

- Lexing
- Parsing
- AST construction
- Symbol tracking
- Scope management
- Semantic validation
- IR emission

All of that logic lives in `main.c`, `parser/`, and `src/`.

## Lexer

`parser/lexer.l` recognizes:

- Keywords: `if`, `else`, `while`, `return`, `int`, `void`
- Comparison operators: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Arithmetic operators: `+`, `-`, `*`, `/`, `%`
- Assignment: `=`
- Delimiters: `; , ( ) { } [ ]`
- Integer literals
- Identifiers
- Block comments `/* ... */`

Implementation notes:

- Numeric literals are stored in `yylval.ival`.
- Identifiers are duplicated into `yylval.sval`.
- The lexer prints every token as a debug trace.
- Unexpected characters are reported immediately.

## Parser

`parser/parser.y` builds the AST directly in grammar actions.

### Top-Level Structure

- `program` becomes `AST_PROGRAM`
- Top-level declarations are chained as siblings and then attached as children of the program node

### Declarations

- Scalar variable declaration:
  - `int x;`
  - `void x;` is syntactically allowed, but semantic analysis rejects variable declarations of type `void`
- Array declaration:
  - `int a[10];`
- Function declaration:
  - `int f(...) { ... }`
  - `void f(...) { ... }`

### Parameters

- Scalar parameter:
  - `int x`
  - AST node kind: `AST_PARAM`
- Array parameter:
  - `int a[]`
  - AST node kind: `AST_PARAM_ARRAY`
  - Stored in the symbol table as `TYPE_ARRAY` with `array_size = -1`

### Statements

The grammar currently supports:

- Expression statements
- Compound statements
- `if`
- `if/else`
- `while`
- `return`

Nested blocks create fresh block scopes.

### Expressions

Supported expression forms are:

- Assignment
- Function call
- Variable reference
- Array access
- Integer literal
- Parenthesized expression
- Binary arithmetic and comparison

Important current limitation:

- There is no unary minus node in the grammar.

## AST Shape

The AST uses `firstChild` and `nextSibling` links instead of fixed child arrays.

Important shapes:

- `AST_FUN_DECL`
  - First child is either `AST_PARAM_LIST` or the function body block
- `AST_BLOCK`
  - Children are local declarations first, followed by statements
- `AST_ASSIGN`
  - Child 1 is the lvalue
  - Child 2 is the rhs expression
- `AST_BINOP`
  - Child 1 is the left operand
  - Child 2 is an operator node created by `newOpNode`
  - Child 3 is the right operand
- `AST_CALL`
  - Child is `AST_ARG_LIST`
- `AST_ARRAY_ACCESS`
  - Node name is the array identifier
  - First child is the index expression

## Scope Management

The current scope implementation is in `src/utils.c`.

Rules:

- The parser pushes a function scope when entering a function declaration.
- Each compound statement pushes a unique block scope such as `main#block1`.
- Scope names are stored on a stack.
- Symbol lookup uses the active scope stack from innermost to outermost, then falls back to `global`.

This means nested block shadowing is implemented today.

## Symbol Table

The symbol table in `src/symbol_table.c` records:

- Identifier name
- Scope string
- Symbol kind
- Data type
- Array size and base type
- Declaration lines
- Use lines
- Function parameter metadata

Behavior notes:

- Redeclaration inside the same scope reports an error through `yyerror`.
- Uses resolve through the active scope stack, not just the current scope string.
- Function parameter types are copied into the function symbol after parsing the full parameter list.

## Semantic Analysis

`src/semantic.c` performs a second AST walk after parsing.

Checks currently implemented:

- Variables cannot be declared as `void`
- Identifiers must resolve through the active scope stack
- Binary operators require integer operands
- Assignment lhs must be a scalar variable or an indexed array element
- Assignment rhs must be `int`
- Bare array names cannot be assigned to
- Function calls must target declared functions
- Function call argument count must match
- Function call argument types must match, including array parameters
- Array access requires an array symbol and an integer index
- `if` and `while` conditions must be `int`
- `return;` is only valid in `void` functions
- `return expr;` must match the enclosing function return type
- Non-void functions must return on all paths according to the current block analysis

When semantic analysis succeeds:

- IR is generated
- IR is printed to the terminal
- IR is written to `docs/output/generated_IR.txt`

When semantic analysis fails:

- IR is not generated
- Errors are printed to stderr

Current caveat:

- `main.c` still exits based on parse success, so semantic failure does not currently produce a failing shell exit status.
