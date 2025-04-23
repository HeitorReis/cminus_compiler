# C-minus Compiler

This project implements a compiler for the **C-minus** language using **Flex**, **Bison**, and **C**.

## 📁 Project Structure

- `src/` - C source files
- `parser/` - Flex (lexer.l) and Bison (parser.y)
- `build/` - Intermediate object and generated files
- `bin/` - Compiled executable
- `docs/test_files/` - Test input files

## 🔧 Build Instructions

To build the project:

    make

## ▶️ Run with Test Files

To run the program with a specific test file:

    make run TEST=1   # Runs with docs/test_files/teste.txt
    make run TEST=2   # Runs with docs/test_files/teste2.txt
    make run TEST=3   # Runs with docs/test_files/teste3.txt

To run without an input file:

    make run

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
