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
  - Runs one of the wired sample inputs from `docs/test_files/`.
  - Accepts legacy numeric selectors such as `TEST=3` and canonical names such as `TEST=gcd`.
  - `TEST=1` now selects `docs/test_files/teste.txt`; the empty default still selects `docs/test_files/sort.txt`.
- `make run TEST=<id> trace`
- `make run TEST=<id> TRACE=1`
  - Runs the selected sample, then executes `python3 tools/run_machine_code.py --trace` against the generated machine code.
  - Writes the runner stdout to `docs/output/log_analysis.txt` and refreshes `docs/output/result_analysis.txt`.
  - GNU make treats dash-prefixed words as its own CLI options, so the dashed spelling only works behind `--`: `make -- run TEST=<id> --trace`.
- `make run_all`
  - Cleans, rebuilds, and runs the configured positive regression suite.
  - The suite uses canonical names for `sort`, `gcd`, `factorial`, and `fibonacci`, plus the remaining numbered fixtures.
- `make run_all complete`
- `make run_all c`
- `make run_all COMPLETE=1`
  - Runs the same positive regression suite, then also executes `python3 tools/run_machine_code.py` for each generated machine-code file.
  - Writes per-test runner summaries to `docs/output/all_machine_codes/logs/*_machine_run.log`.
  - The default runner arguments are `--max-cycles 500 --default-input 0`; override them with `RUN_MACHINE_ARGS="..."` when needed.
  - GNU make treats dash-prefixed words as its own CLI options, so the dashed spellings only work behind `--`: `make -- run_all --complete` or `make -- run_all -c`.
- `make test_analysis`
  - Builds the front-end and runs the analysis-phase regression suite in temporary working directories.
  - Covers lexical, syntactic, semantic, undeclared-identifier, missing-`main`, and VPP-generation checks.
- `make generate_analysis_vpp`
  - Regenerates the canonical Visual Paradigm analysis diagram inside `vpp/cminus-compiler-expanded.vpp`.

If your environment only provides `python3`, the most reliable manual flow is:

```sh
make bin/c-c
bin/c-c docs/test_files/gcd.txt > docs/output/log_compiler.txt
python3 -u codegen/main.py > docs/output/log_codegen.txt
```

## Pipeline

1. `bin/c-c <input_file>`
   - Opens the source file and resets the shared lexical/syntactic diagnostic state.
   - Initializes built-in symbols `input()` and `output(int)`.
   - Runs Flex/Bison to tokenize and parse the source into an AST.
   - Aborts immediately on lexical or syntactic failure and returns a non-zero exit code.
   - Prints the AST after a successful parse.
   - Runs semantic analysis, checks for a global `main`, and then prints the symbol table.
   - Emits `docs/output/generated_IR.txt` only when semantic analysis succeeds and `main` exists.
2. `python3 codegen/main.py`
   - Reads `docs/output/generated_IR.txt`.
   - Generates `docs/output/generated_assembly.txt`.
   - Assembles into `docs/output/generated_machine_code.txt`.
   - Writes the machine-word to assembly listing to `docs/output/debug_assembly.txt`.
   - Writes a decoded machine-code log to `docs/output/debug_machine_code.txt`.

The C and Python halves communicate through the IR text file rather than through a shared in-memory representation.

## Analysis Regression Suite

The dedicated front-end regression runner captures stdout/stderr in memory and avoids redirecting logs into tracked files:

```sh
make test_analysis
python3 tools/run_analysis_regressions.py
```

The suite uses temporary working directories so that negative cases can assert the absence of `generated_IR.txt` without depending on repository state.

## Visual Paradigm Diagram

`vpp/cminus-compiler-expanded.vpp` is the canonical Visual Paradigm artifact for the project.
The analysis-phase activity diagram is generated, not edited manually:

```sh
make generate_analysis_vpp
python3 tools/generate_vpp_analysis_diagram.py
python3 tools/generate_vpp_analysis_diagram.py /tmp/cminus-analysis.vpp
```

The generator creates or replaces the single diagram named `Compilador - Fase de Análise` and leaves legacy diagrams intact.

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

Main pipeline outputs are written under `docs/output/`:

- `generated_IR.txt`
- `generated_assembly.txt`
- `generated_machine_code.txt`
- `debug_assembly.txt`
- `debug_machine_code.txt`
- `result_analysis.txt`
- `log_analysis.txt`
- `log_compiler.txt`
- `log_codegen.txt`

`make clean` removes `build/`, `bin/`, `parser.gv`, and `parser.output`, but it does not remove files under `docs/output/`.

## RTL Machine-Code Runner

The repository also contains a Python runner that simulates the current `Processor(v2026-1)` RTL behavior at the machine-code level:

```sh
python3 tools/run_machine_code.py --max-cycles 50
python3 tools/run_machine_code.py docs/output/generated_machine_code.txt --max-cycles 50
python3 tools/run_machine_code.py docs/output/generated_machine_code.txt --max-cycles 50 --default-input 0
python3 tools/run_machine_code.py docs/output/generated_machine_code.txt --max-cycles 50 --trace
```

If no machine-code file is passed, the runner automatically loads `docs/output/generated_machine_code.txt` when that file exists.
When the default generated machine-code file is used, the runner also writes the text report to `docs/output/result_analysis.txt`.
If `docs/output/debug_assembly.txt` is available, `--trace` also prints the matching assembly instruction for each executed machine word.

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
- `docs/test_files/`
  - Sample input programs.
- `docs/output/`
  - Generated artifacts and logs.

## Current Caveats

- Debug logging is always enabled across the front-end and backend.
- Global arrays are materialized in the backend data section. Global scalar storage is a weaker path today and is not covered by the checked-in regression set.
