# C-minus Compiler Architecture

## Pipeline Overview
1. Frontend (Flex/Bison + C)
   - Lexing and parsing build the AST and a symbol table.
2. Semantic Analysis (C)
   - Type checks, declaration/use validation, and return checks.
3. IR Generation (C)
   - Emits a three-address-code-like IR to `docs/output/generated_IR.txt`.
4. Code Generation (Python)
   - Translates IR to custom assembly.
5. Assembly (Python)
   - Encodes assembly into 32-bit machine code.

## Major Data Structures
- AST (`AstNode`): n-ary tree describing program structure and expressions.
- Symbol table (`SymbolTable`): linked list of identifiers with scope/type metadata.
- IR (`IRList`, `IRInstruction`): linear list of three-address instructions.

## Key Interfaces
- Frontend:
  - `yyparse()` builds the AST and populates the symbol table.
  - `semanticAnalyze(root, symtab)` validates semantics and triggers IR generation.
- Backend:
  - `generate_ir(root, symtab)` produces IR.
  - `generate_assembly(ir_lines)` produces assembly.
  - `FullCode(assembly_lines)` assembles to machine code.

## Scope Model
- Functions introduce new scopes.
- The current scope is tracked by `currentScope`.
- Variables are resolved within the current scope, then `global`.

