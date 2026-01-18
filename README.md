# C-minus Compiler

This project implements a compiler for the **C-minus** language using **Flex**, **Bison**, and **C**.

## 📚 Documentation

- `docs/architecture.md` - High-level structure and pipeline
- `docs/frontend.md` - Lexer/parser/AST/symbol table/semantic analysis
- `docs/ir.md` - IR format and semantics
- `docs/backend.md` - Codegen and assembler details
- `docs/best_practices.md` - Best-practices audit
- `docs/action_plan.md` - Remediation plan and motivations

## 📁 Project Structure

- `src/` - C source files
- `parser/` - Flex (lexer.l) and Bison (parser.y)
- `build/` - Intermediate object and generated files
- `bin/` - Compiled executable
- `docs/test_files/` - Test input files

## ✅ Language Support

- Integers, arithmetic, comparisons, and assignments
- `if/else` and `while`
- Functions with `int`/`void` returns
- Vectors (arrays), including array parameters
- Recursion (self-calling functions)
- Built-ins: `input()` and `output(x)`

## 🔧 Build Instructions

To build the project:

    make

## ▶️ Run with Test Files

To run the program with a specific test file:

    make run TEST=1   # Runs with docs/test_files/teste.txt
    make run TEST=2   # Runs with docs/test_files/teste2.txt
    make run TEST=3   # Runs with docs/test_files/teste3.txt
    make run TEST=4   # Runs with docs/test_files/teste4.txt
    make run TEST=5   # Runs with docs/test_files/teste5.txt

To run without an input file:

    make run

## 📦 Outputs

The pipeline writes compiler and codegen artifacts to `docs/output/`:

- `docs/output/generated_IR.txt`
- `docs/output/generated_assembly.txt`
- `docs/output/generated_machine_code.txt`

## 🧹 Clean Build Files

To clean all generated files:

    make clean

## 🛠 Requirements

Make sure you have the following installed:

- gcc and g++
- flex
- bison
- make

On Ubuntu/Debian:

    sudo apt update
    sudo apt install build-essential flex bison
