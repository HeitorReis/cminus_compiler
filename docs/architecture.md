# C-minus Compiler Architecture

## High-Level Shape

The implementation is split into two phases owned by different runtimes:

1. Front-end in C
   - Lexing, parsing, AST construction, symbol tracking, semantic analysis, and IR emission.
2. Backend in Python
   - IR parsing, stack/data layout, assembly generation, and machine-code assembly.

The handoff between the two phases is the textual IR file `docs/output/generated_IR.txt`.

## Front-End Stages

### 1. Process Setup

`main.c` initializes:

- The global symbol table
- The scope stack
- Built-in functions:
  - `input(): int`
  - `output(int): void`

### 2. Lexing and Parsing

`parser/lexer.l` tokenizes the source and prints verbose token logs.

`parser/parser.y` builds:

- The AST rooted at `AST_PROGRAM`
- Symbol-table entries for declarations and uses
- Block-scope names such as `main#block1`

### 3. Semantic Analysis

`src/semantic.c` re-walks the AST and validates:

- Declaration-before-use
- Type correctness for expressions and calls
- Array indexing rules
- Assignment target validity
- Return statements for non-void functions
- Return-path coverage for non-void functions

If semantic analysis succeeds, it calls the IR generator.

### 4. IR Generation

`src/ir.c` emits a three-address-style IR:

- Function labels
- `param` declarations
- Arithmetic and comparison instructions
- `arg`, `call`, and `return`
- `if_false` and `goto`
- Array address, load, and store operations
- `.space` declarations for arrays

It also removes unreachable instructions that appear after `goto` or `return` until the next label.

## Backend Stages

### 1. IR File Read

`codegen/main.py` reads `docs/output/generated_IR.txt` and passes the line list to `codegen.generate_assembly`.

### 2. Static IR Analysis

`codegen/codegen.py` performs two setup passes:

- Collect function entry labels and create one `FunctionContext` per function.
- Build a backend symbol table for global data directives found in IR.

Important detail:

- The backend only allocates explicit global data it can see in IR.
- The front-end currently emits explicit `.space` declarations for arrays, but not `.word` declarations for scalar globals.

### 3. Function Lowering

For each function, the backend:

- Collects formal parameters from `param` lines
- Infers locals and temporaries from textual IR
- Builds a stack layout
- Translates each IR instruction into assembly
- Spills dirty registers before labels, calls, and returns

### 4. Assembly and Machine Code

`codegen/assembler.py` parses the emitted assembly and:

- Resolves labels
- Expands large immediates via a literal pool
- Expands long branches when the target is out of range
- Encodes the final 32-bit machine code

## Core Data Structures

### AST

The AST is an n-ary tree with `firstChild` and `nextSibling` links.

Important node kinds include:

- `AST_PROGRAM`
- `AST_FUN_DECL`
- `AST_BLOCK`
- `AST_VAR_DECL`
- `AST_PARAM` and `AST_PARAM_ARRAY`
- `AST_ASSIGN`
- `AST_BINOP`
- `AST_CALL`
- `AST_ARRAY_ACCESS`

### Front-End Symbol Table

The C symbol table stores:

- Name
- Scope string
- Symbol kind (`VAR` or `FUNC`)
- Type information
- Array metadata
- Declaration and use lines
- Function parameter count and parameter types

### Scope Stack

The scope stack in `src/utils.c` tracks active function and block scopes.

Resolution order is:

1. Innermost active scope
2. Outward active scopes
3. `global`

### Backend Function Context

Each backend function context stores:

- Collected instructions
- Pending call arguments
- Parameter names
- Local variable names
- Local array sizes
- Stack layout
- Temporary spill locations
- The last comparison operator used for conditional lowering

## Current Architectural Constraints

- The front-end and backend share no typed IR schema; they communicate through plain text.
- The backend reconstructs some meaning, such as locals and parameters, by scanning the IR text.
- Debug output is always enabled, so normal runs produce large logs.
- Semantic failure does not currently translate into a failing process exit status.
