# C-minus Compiler

This repository implements a C-minus compiler with a split pipeline:

- A C front-end built with Flex and Bison.
- A Python backend that lowers textual IR into assembly and then into machine code.

## Current Workflow

The project does not currently have a dedicated `build` target. The practical entry points are:

- `make`
  - Runs `clean` and then `run` on the default sample program.
  - This is a full pipeline command, not a build-only command.
- `make bin/c-c`
  - Builds only the front-end executable.
- `make run TEST=<id>`
  - Runs one of the wired sample inputs from `docs/input/cminus/`.
  - Accepts legacy numeric selectors such as `TEST=3` and canonical names such as `TEST=gcd`.
  - `TEST=1` now selects `docs/input/cminus/teste.txt`; the empty default still selects `docs/input/cminus/sort.txt`.
- `make run TEST=<id> trace`
- `make run TEST=<id> TRACE=1`
  - Runs the selected sample, then executes `python3 tools/run_machine_code.py --trace` against the generated machine code.
  - Writes the runner stdout to `docs/generated/diagnostics/machine_runner/analysis_trace.log` and refreshes `docs/generated/diagnostics/machine_runner/result_analysis.txt`.
  - GNU make treats dash-prefixed words as its own CLI options, so the dashed spelling only works behind `--`: `make -- run TEST=<id> --trace`.
- `make run_all`
  - Cleans, rebuilds, and runs the configured positive regression suite.
  - The suite uses canonical names for `sort`, `gcd`, `factorial`, and `fibonacci`, plus the remaining numbered fixtures.
- `make run_all complete`
- `make run_all c`
- `make run_all COMPLETE=1`
  - Runs the same positive regression suite, then also executes `python3 tools/run_machine_code.py` for each generated machine-code file.
  - Writes per-test runner summaries to `docs/generated/batch/diagnostics/*_machine_run.log`.
  - The default runner arguments are `--max-cycles 500 --default-input 0`; override them with `RUN_MACHINE_ARGS="..."` when needed.
  - GNU make treats dash-prefixed words as its own CLI options, so the dashed spellings only work behind `--`: `make -- run_all --complete` or `make -- run_all -c`.
- `make test_analysis`
  - Builds the front-end and runs the analysis-phase regression suite in temporary working directories.
  - Covers lexical, syntactic, semantic, undeclared-identifier, missing-`main`, and VPP-generation checks.
- `make generate_analysis_vpp`
  - Regenerates the canonical Visual Paradigm SysML diagrams inside `vpp/cminus-compiler-expanded.vpp`.
- `make generate_sysml_vpp`
  - Alias for the same SysML diagram generator.

If your environment only provides `python3`, the most reliable manual flow is:

```sh
make bin/c-c
bin/c-c docs/input/cminus/gcd.txt > docs/generated/diagnostics/frontend/compiler.log
python3 -u codegen/main.py > docs/generated/diagnostics/codegen/codegen.log
```

## Pipeline

1. `bin/c-c <input_file>`
   - Opens the source file and resets the shared lexical/syntactic diagnostic state.
   - Initializes built-in symbols `input()` and `output(int)`.
   - Runs Flex/Bison to tokenize and parse the source into an AST.
   - Aborts immediately on lexical or syntactic failure and returns a non-zero exit code.
   - Prints the AST after a successful parse.
   - Runs semantic analysis, checks for a global `main`, and then prints the symbol table.
   - Emits `docs/generated/intermediate/semantic/ir/generated_IR.txt` only when semantic analysis succeeds and `main` exists.
2. `python3 codegen/main.py`
   - Reads `docs/generated/intermediate/semantic/ir/generated_IR.txt`.
   - Generates `docs/generated/intermediate/codegen/assembly/generated_assembly.txt`.
   - Assembles into `docs/generated/final/assembler/machine_code/generated_machine_code.txt`.
   - Writes the machine-word to assembly listing to `docs/generated/diagnostics/assembler/assembly_to_machine.txt`.
   - Writes a decoded machine-code log to `docs/generated/diagnostics/assembler/machine_code_decoded.txt`.

The C and Python halves communicate through the IR text file rather than through a shared in-memory representation.

## Technical Documentation By Module

The detailed implementation documentation is in
`docs/documentation/compiler_modules.md`. It groups the project by functional
module and documents the role of the main functions, classes, generated
artifacts, processor interface, and verification tools.

Current module groups:

- Front-end orchestration: `main.c` and `Makefile`.
- Lexical and syntactic analysis: `parser/lexer.l` and `parser/parser.y`.
- Front-end data structures: AST, scope stack, symbol table, and diagnostic state under `src/`.
- Semantic analysis and IR generation: `src/semantic.c` and `src/ir.c`.
- Python backend: `codegen/codegen.py`, `codegen/symbol_table.py`, and `codegen/constants.py`.
- Assembler and encoder: `codegen/assembler.py`.
- Regression and execution tools: `tools/run_analysis_regressions.py`, `codegen/assembler_regressions.py`, and `tools/run_machine_code.py`.
- Hardware target: `Processor(v2026-1)` and its Verilog modules.

## Analysis Regression Suite

The dedicated front-end regression runner captures stdout/stderr in memory and avoids redirecting logs into tracked files:

```sh
make test_analysis
python3 tools/run_analysis_regressions.py
```

The suite uses temporary working directories so that negative cases can assert the absence of `generated_IR.txt` without depending on repository state.

## Visual Paradigm SysML Diagrams

`vpp/cminus-compiler-expanded.vpp` is the canonical Visual Paradigm artifact for the project.
The compiler SysML diagrams are generated, not edited manually:

```sh
make generate_analysis_vpp
make generate_sysml_vpp
python3 tools/generate_vpp_analysis_diagram.py
python3 tools/generate_vpp_analysis_diagram.py /tmp/cminus-sysml.vpp
```

The generator creates or replaces the current compiler-only diagram set and removes old Visual Paradigm diagrams that are outside this scope:

- `Diagrama de Atividades - Fluxo de Compilação C- para Código Binário ARM Simplificado`
- `Diagrama de Blocos - Arquitetura Interna do Compilador`
- `Diagrama Interno - Codificador Binário`
- `Diagrama de Blocos — Hierarquia dos Módulos do Compilador`
- `Diagrama de Rastreabilidade - C- para IR, Assembly e Binário`

The activity diagram uses columns of responsibility for the compiler modules, from the C- input through lexical, syntactic and semantic analysis, IR, register allocation, assembly generation, label resolution, binary encoding, validation and final `.txt` output.
The block diagrams keep the processor only as the target instruction format: the compiler block contains the lexer, parser, semantic analyzer, symbol table, IR generator, register allocator, simplified ARM assembly generator, label resolver, binary encoder, binary validator, and output file generator.
The module hierarchy block diagram is the code-organization view. It uses the real project names such as `main.c`, `parser/lexer.l`, `parser/parser.y`, `src/syntax_tree.c/h`, `src/semantic.c/h`, `src/ir.c/h`, `codegen/codegen.py`, and `codegen/assembler.py`, then shows the main structs, classes, functions, outputs, tests, and dependencies between those files.
The encoder view shows the 32-bit fields `Cond[31:28]`, `Type[27:26]`, `Supp[25:24]`, `Funct[23:20]`, `Rd[19:15]`, `Rh[14:10]`, and `Operand2[9:0]`.
The traceability diagram maps one C- example into intermediate code, assembly, and conceptual binary output.

## Current Language Coverage

The checked-in tests exercise the following features:

- `int` and `void` functions
- Local and global declarations
- Fixed-size integer arrays
- Array parameters (`int a[]`)
- Nested block scopes with shadowing
- `if`, `if/else`, and `while`
- Recursion
- Built-ins `input()` and `output(x)`
- Arithmetic `+`, `-`, `*`, `/`, `%`
- Comparisons `==`, `!=`, `<`, `<=`, `>`, `>=`

## Outputs

`docs/` is split by purpose:

- `docs/input/cminus/`
  - C-minus sample and regression programs.
- `docs/documentation/`
  - Project documentation and reports.
- `docs/generated/frontend/syntax_tree/ast.txt`
  - AST emitted by the C front-end after parsing.
- `docs/generated/frontend/symbol_table/symbol_table.txt`
  - Symbol table emitted after semantic analysis.
- `docs/generated/intermediate/semantic/ir/generated_IR.txt`
  - Intermediate representation emitted by `src/semantic.c` and `src/ir.c`.
- `docs/generated/intermediate/codegen/assembly/generated_assembly.txt`
  - Backend assembly used as input to the assembler.
- `docs/generated/final/assembler/machine_code/generated_machine_code.txt`
  - Final machine-code output.
- `docs/generated/diagnostics/`
  - Logs, decoded machine-code reports, assembly-to-machine mapping, and machine-runner analysis.
- `docs/generated/batch/`
  - `run_all` outputs, split between final machine-code files and diagnostic logs.

`make clean` removes `build/`, `bin/`, `parser.gv`, and `parser.output`, but it does not remove files under `docs/generated/`.

## RTL Machine-Code Runner

The repository also contains a Python runner that simulates the current `Processor(v2026-1)` RTL behavior at the machine-code level:

```sh
python3 tools/run_machine_code.py --max-cycles 50
python3 tools/run_machine_code.py docs/generated/final/assembler/machine_code/generated_machine_code.txt --max-cycles 50
python3 tools/run_machine_code.py docs/generated/final/assembler/machine_code/generated_machine_code.txt --max-cycles 50 --default-input 0
python3 tools/run_machine_code.py docs/generated/final/assembler/machine_code/generated_machine_code.txt --max-cycles 50 --trace
```

If no machine-code file is passed, the runner automatically loads `docs/generated/final/assembler/machine_code/generated_machine_code.txt` when that file exists.
When the default generated machine-code file is used, the runner also writes the text report to `docs/generated/diagnostics/machine_runner/result_analysis.txt`.
If `docs/generated/diagnostics/assembler/assembly_to_machine.txt` is available, `--trace` also prints the matching assembly instruction for each executed machine word.

Useful options:

- `--json`
  - emit the final state as JSON
- `--trace`
  - include a per-cycle execution trace
- `--input <value>`
  - provide peripheral input values for `in` instructions
- `--prompt-inputs`
  - force stdin prompts when an `in` instruction needs a value and no `--input` values remain
- `--default-input <value>`
  - inject a fallback input value when an `in` instruction blocks and no explicit `--input` values remain
- `--analysis-output <path>`
  - write the rendered analysis report to a specific file
- `--assembly-listing <path>`
  - load a `<binary> -> <assembly>` listing so trace lines can include the originating assembly instruction

The runner models:

- 32 general-purpose registers
- the dedicated hardware link register
- CPSR zero/negative flags
- 64-word data memory
- the current branch/link semantics implemented in `Processor(v2026-1)`

For deterministic testing, the Python model starts registers, link state, flags, and data memory at zero.
Each executed `out` appends the emitted value to `output_value`, so the final state keeps the full output sequence.
When the runner is attached to an interactive terminal, it also prompts for missing `in` values automatically.

In the FPGA processor path, `SW[15]` now resumes a halted `in` instruction only on a falling edge (`1 -> 0`). The top-level still forwards the raw switch value, and the edge detection happens inside the control logic so the interaction behaves like an `enter` key: raise `SW[15]` to arm it, then move it to `0` to release the waiting `in`. `SW[16]` resets the detector state and clears the temporary halt latch.

## Repository Layout

- `main.c`
  - Front-end entry point.
- `parser/`
  - Flex lexer and Bison grammar.
- `src/`
  - AST, symbol table, scope stack, semantic analysis, and IR generation.
- `codegen/`
  - Python code generator, assembler, and backend symbol helpers.
- `docs/input/cminus/`
  - Sample input programs.
- `docs/generated/`
  - Generated artifacts and logs.

## Current Caveats

- Debug logging is always enabled across the front-end and backend.
- Global arrays are materialized in the backend data section. Global scalar storage is a weaker path today and is not covered by the checked-in regression set.
