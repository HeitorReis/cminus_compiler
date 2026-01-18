# Frontend Documentation

## Lexer (`parser/lexer.l`)
- Produces tokens for keywords, operators, punctuation, numbers, and identifiers.
- Supports block comments `/* ... */`.
- Returns numeric literals in `yylval.ival` and identifiers in `yylval.sval`.

## Parser (`parser/parser.y`)
- Grammar builds the AST and symbol table in semantic actions.
- Function scopes are pushed/popped on entry/exit.
- AST nodes:
  - `AST_PROGRAM` contains all top-level declarations.
  - `AST_FUN_DECL` holds parameters and body block.
  - `AST_BLOCK` contains local declarations and statements.
  - Expressions are represented with `AST_BINOP`, `AST_ASSIGN`, `AST_CALL`, etc.
- Arrays:
  - Declarations record `array_size` in the AST.
  - Array access is `AST_ARRAY_ACCESS` with index expression as child.

## Symbol Table (`src/symbol_table.*`)
- Stores name, scope, kind (variable/function), type, and decl/use lines.
- Functions store parameter counts and parameter types.
- Array declarations are recorded with `dataType = TYPE_ARRAY`.

## AST (`src/syntax_tree.*`)
- `AstNode` contains:
  - `kind`, `name`, `value`, `array_size`, `data_type`, `lineno`.
  - `firstChild` and `nextSibling` for tree structure.
- Constructors:
  - `newNode(kind)`
  - `newIdNode(name, lineno)`
  - `newNumNode(value, lineno)`
  - `newOpNode(op, lineno)`

## Semantic Analysis (`src/semantic.*`)
- Validates:
  - Declarations exist before use.
  - Non-void variables.
  - `if/while` conditions are `int`.
  - Binary op operands are `int`.
  - Function call argument counts/types.
  - Array access uses an array with `int` index.
  - Assignments do not target array names directly.
- On success: generates IR.

