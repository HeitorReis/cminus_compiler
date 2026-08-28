# === Directories ===
SRC_DIR := src
PARSER_DIR := parser
BUILD_DIR := build
BIN_DIR := bin
DOCS_DIR := docs/input/cminus
GENERATED_DIR := docs/generated
FRONTEND_LOG_DIR := $(GENERATED_DIR)/diagnostics/frontend
CODEGEN_LOG_DIR := $(GENERATED_DIR)/diagnostics/codegen
MACHINE_RUNNER_DIR := $(GENERATED_DIR)/diagnostics/machine_runner
FINAL_MACHINE_CODE := $(GENERATED_DIR)/final/assembler/machine_code/generated_machine_code.txt
ASSEMBLY_LISTING := $(GENERATED_DIR)/diagnostics/assembler/assembly_to_machine.txt
ALL_OUTPUT_DIR := $(GENERATED_DIR)/batch/final_machine_code
ALL_LOG_DIR := $(GENERATED_DIR)/batch/diagnostics
SELECTED_TEN_OUTPUT_DIR := $(GENERATED_DIR)/batch/selected_10_machine_code
SELECTED_TEN_LOG_DIR := $(GENERATED_DIR)/batch/selected_10_diagnostics
SELECTED_TEN_ASSEMBLY_DIR := $(GENERATED_DIR)/batch/selected_10_assembly
SELECTED_TEN_FPGA_DIAGNOSTIC_DIR := $(GENERATED_DIR)/batch/selected_10_fpga_diagnostics
ROM_MIF_DIR := processor/Processor/modules
ROM_ACTIVE_MIF := $(ROM_MIF_DIR)/program.mif
ROM_PROGRAM ?= 1
RUN_ALL_COMPLETE := $(strip $(filter 1 true yes on,$(COMPLETE)) $(filter complete c --complete -c,$(MAKECMDGOALS)))
RUN_TRACE := $(strip $(filter 1 true yes on,$(TRACE)) $(filter trace --trace,$(MAKECMDGOALS)))
RUN_MACHINE_ARGS ?= --max-cycles 500 --default-input 0

# === Files ===
LEX_FILE := $(PARSER_DIR)/lexer.l
YACC_FILE := $(PARSER_DIR)/parser.y
# The front-end executable is named c-c to match the linker output.
EXEC := $(BIN_DIR)/c-c

# === Intermediate files ===
YACC_C := $(BUILD_DIR)/parser.tab.c
YACC_H := $(BUILD_DIR)/parser.tab.h
LEX_C := $(BUILD_DIR)/lex.yy.c
OBJECTS := $(BUILD_DIR)/main.o \
           $(BUILD_DIR)/parser.tab.o \
           $(BUILD_DIR)/lex.yy.o \
           $(BUILD_DIR)/analysis_state.o \
           $(BUILD_DIR)/semantic.o \
           $(BUILD_DIR)/symbol_table.o \
           $(BUILD_DIR)/syntax_tree.o \
           $(BUILD_DIR)/utils.o \
					 $(BUILD_DIR)/ir.o \

# === Compiler and Linker Settings ===
CC := gcc
CXX := g++   # using g++ for linking
CFLAGS := -I$(BUILD_DIR) -I$(SRC_DIR)
LDFLAGS := -lfl

# === Source list ===
SRC_FILES := main.c \
            $(SRC_DIR)/analysis_state.c \
            $(SRC_DIR)/semantic.c \
            $(SRC_DIR)/symbol_table.c \
            $(SRC_DIR)/syntax_tree.c \
            $(SRC_DIR)/utils.c \
			$(SRC_DIR)/ir.c \

RUN_ALL_TEST_FILES := \
	$(DOCS_DIR)/sort.txt \
	$(DOCS_DIR)/teste2.txt \
	$(DOCS_DIR)/gcd.txt \
	$(DOCS_DIR)/teste4.txt \
	$(DOCS_DIR)/teste5.txt \
	$(DOCS_DIR)/factorial.txt \
	$(DOCS_DIR)/fibonacci.txt \
	$(DOCS_DIR)/teste8.txt \
	$(DOCS_DIR)/teste9.txt \
	$(DOCS_DIR)/teste10.txt \
	$(DOCS_DIR)/teste11.txt

# The ten numbered programs added as the focused test suite.
SELECTED_TEN_TEST_FILES := \
	$(DOCS_DIR)/01_soma_1_ate_n.txt \
	$(DOCS_DIR)/02_fatorial.txt \
	$(DOCS_DIR)/03_fibonacci.txt \
	$(DOCS_DIR)/04_numero_primo.txt \
	$(DOCS_DIR)/05_maior_elemento_vetor.txt \
	$(DOCS_DIR)/06_busca_linear_vetor.txt \
	$(DOCS_DIR)/07_bubble_sort.txt \
	$(DOCS_DIR)/08_mdc.txt \
	$(DOCS_DIR)/09_matriz_loops_aninhados.txt \
	$(DOCS_DIR)/10_carga_preempcao.txt
			
# === Rules ===

.PHONY: all run run_all run_selected_10 run_selected_10_diagnostics run_numbered_tests run_10 fpga_diagnostics generate_mif select_mif complete c --complete -c trace --trace test_analysis generate_analysis_vpp generate_sysml_vpp clean

all: clean run

# Create necessary directories
$(BUILD_DIR) $(BIN_DIR) $(GENERATED_DIR) $(FRONTEND_LOG_DIR) $(CODEGEN_LOG_DIR) $(MACHINE_RUNNER_DIR) $(ALL_OUTPUT_DIR) $(ALL_LOG_DIR) $(SELECTED_TEN_OUTPUT_DIR) $(SELECTED_TEN_LOG_DIR) $(SELECTED_TEN_ASSEMBLY_DIR) $(SELECTED_TEN_FPGA_DIAGNOSTIC_DIR):
	mkdir -p $@

# Generate parser using bison with flags -d -v -g
$(YACC_C) $(YACC_H): $(YACC_FILE) | $(BUILD_DIR)
	bison -d -v -g $(YACC_FILE)
	mv -f parser.tab.c $(BUILD_DIR)/
	mv -f parser.tab.h $(BUILD_DIR)/
	touch $(YACC_C) $(YACC_H)


# Generate lexer using flex
$(LEX_C): $(LEX_FILE) $(YACC_H) | $(BUILD_DIR)
	flex -o $(LEX_C) $(LEX_FILE)
	touch $(LEX_C)

# Compile .c files in the project root
$(BUILD_DIR)/%.o: %.c $(YACC_H) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Compile .c files in the src directory
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c $(YACC_H) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Compile parser C file (from bison) into an object file
$(BUILD_DIR)/parser.tab.o: $(YACC_C)
	$(CC) $(CFLAGS) -c $(YACC_C) -o $@

# Compile lexer file into an object file (ensuring gcc -c lex.yy.c is run)
$(BUILD_DIR)/lex.yy.o: $(LEX_C)
	$(CC) $(CFLAGS) -c $(LEX_C) -o $@

# Link all object files using g++ with the -lfl flag
$(EXEC): $(BUILD_DIR) $(BIN_DIR) $(YACC_C) $(LEX_C) $(OBJECTS) 
	$(CXX) $(CFLAGS) $(OBJECTS) -o $(EXEC) $(LDFLAGS)

# Run with test files based on the user-specified TEST variable
run: $(EXEC) | $(FRONTEND_LOG_DIR) $(CODEGEN_LOG_DIR) $(MACHINE_RUNNER_DIR)
	@case "$(TEST)" in \
		""|sort) test_file="$(DOCS_DIR)/sort.txt" ;; \
		1|teste) test_file="$(DOCS_DIR)/teste.txt" ;; \
		2|teste2) test_file="$(DOCS_DIR)/teste2.txt" ;; \
		3|gcd|teste3) test_file="$(DOCS_DIR)/gcd.txt" ;; \
		4|teste4) test_file="$(DOCS_DIR)/teste4.txt" ;; \
		5|teste5) test_file="$(DOCS_DIR)/teste5.txt" ;; \
		6|factorial|teste6) test_file="$(DOCS_DIR)/factorial.txt" ;; \
		7|fibonacci|teste7) test_file="$(DOCS_DIR)/fibonacci.txt" ;; \
		8|teste8) test_file="$(DOCS_DIR)/teste8.txt" ;; \
		9|teste9) test_file="$(DOCS_DIR)/teste9.txt" ;; \
		10|teste10) test_file="$(DOCS_DIR)/teste10.txt" ;; \
		11|teste11) test_file="$(DOCS_DIR)/teste11.txt" ;; \
		*) echo "Unknown TEST='$(TEST)'"; exit 1 ;; \
	esac; \
	$(EXEC) "$$test_file" > $(FRONTEND_LOG_DIR)/compiler.log
	python3 -u codegen/main.py > $(CODEGEN_LOG_DIR)/codegen.log
	@if [ -n "$(RUN_TRACE)" ]; then \
		if [ -f $(FINAL_MACHINE_CODE) ]; then \
			python3 -u tools/run_machine_code.py $(RUN_MACHINE_ARGS) --trace < /dev/null > $(MACHINE_RUNNER_DIR)/analysis_trace.log; \
		else \
			echo "Machine-code runner skipped because no machine code was generated." > $(MACHINE_RUNNER_DIR)/analysis_trace.log; \
		fi; \
	fi

# Run all test files and collect machine code outputs
run_all: clean $(EXEC) | $(ALL_OUTPUT_DIR) $(ALL_LOG_DIR)
	@rm -f $(ALL_OUTPUT_DIR)/*_machine_code.txt
	@rm -f $(ALL_LOG_DIR)/*.log
	@for test_file in $(RUN_ALL_TEST_FILES); do \
		echo "Running $$test_file"; \
		base=$$(basename $$test_file .txt); \
		rm -f $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt; \
		rm -f $(FINAL_MACHINE_CODE); \
		$(EXEC) $$test_file > $(ALL_LOG_DIR)/$${base}_compiler.log 2>&1 || true; \
		python3 -u codegen/main.py > $(ALL_LOG_DIR)/$${base}_codegen.log 2>&1 || true; \
		if [ -f $(FINAL_MACHINE_CODE) ]; then \
			cp $(FINAL_MACHINE_CODE) $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt; \
			if [ -n "$(RUN_ALL_COMPLETE)" ]; then \
				python3 -u tools/run_machine_code.py $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt $(RUN_MACHINE_ARGS) < /dev/null > $(ALL_LOG_DIR)/$${base}_machine_run.log 2>&1 || true; \
			fi; \
		else \
			echo "No machine code generated for $$test_file" >> $(ALL_LOG_DIR)/$${base}_codegen.log; \
			if [ -n "$(RUN_ALL_COMPLETE)" ]; then \
				echo "Machine-code runner skipped because no machine code was generated for $$test_file" > $(ALL_LOG_DIR)/$${base}_machine_run.log; \
			fi; \
		fi; \
	done

# Build if needed, then compile only the selected numbered ten-test suite.
# Each final machine-code file is kept independently under SELECTED_TEN_OUTPUT_DIR.
run_selected_10: $(EXEC) | $(SELECTED_TEN_OUTPUT_DIR) $(SELECTED_TEN_LOG_DIR) $(SELECTED_TEN_ASSEMBLY_DIR)
	@failures=0; \
	for test_file in $(SELECTED_TEN_TEST_FILES); do \
		base=$$(basename "$$test_file" .txt); \
		machine_code_file="$(SELECTED_TEN_OUTPUT_DIR)/$${base}_machine_code.txt"; \
		assembly_listing_file="$(SELECTED_TEN_ASSEMBLY_DIR)/$${base}_assembly_to_machine.txt"; \
		compiler_log="$(SELECTED_TEN_LOG_DIR)/$${base}_compiler.log"; \
		codegen_log="$(SELECTED_TEN_LOG_DIR)/$${base}_codegen.log"; \
		echo "Running $$test_file"; \
		rm -f "$$machine_code_file" "$$assembly_listing_file" "$(FINAL_MACHINE_CODE)"; \
		if "$(EXEC)" "$$test_file" > "$$compiler_log" 2>&1; then \
			if python3 -u codegen/main.py > "$$codegen_log" 2>&1; then \
				if [ -s "$(FINAL_MACHINE_CODE)" ]; then \
					cp "$(FINAL_MACHINE_CODE)" "$$machine_code_file"; \
					if [ -s "$(ASSEMBLY_LISTING)" ]; then \
						cp "$(ASSEMBLY_LISTING)" "$$assembly_listing_file"; \
					else \
						echo "No assembly listing was generated for $$test_file" >> "$$codegen_log"; \
						failures=$$((failures + 1)); \
					fi; \
				else \
					echo "No machine code was generated for $$test_file" >> "$$codegen_log"; \
					failures=$$((failures + 1)); \
				fi; \
			else \
				failures=$$((failures + 1)); \
			fi; \
		else \
			printf 'Skipped backend because front-end compilation failed.\n' > "$$codegen_log"; \
			failures=$$((failures + 1)); \
		fi; \
	done; \
	if [ "$$failures" -ne 0 ]; then \
		echo "$$failures selected test(s) failed; see $(SELECTED_TEN_LOG_DIR)."; \
		exit 1; \
	fi; \
	echo "Generated machine code for 10 selected tests in $(SELECTED_TEN_OUTPUT_DIR)."

# Run the Python processor model with fixed FPGA input/output vectors for all ten programs.
run_selected_10_diagnostics: run_selected_10 | $(SELECTED_TEN_FPGA_DIAGNOSTIC_DIR)
	python3 tools/run_machine_code.py --selected-10-diagnostics \
		--diagnostic-machine-code-dir $(SELECTED_TEN_OUTPUT_DIR) \
		--diagnostic-assembly-dir $(SELECTED_TEN_ASSEMBLY_DIR) \
		--diagnostic-output-dir $(SELECTED_TEN_FPGA_DIAGNOSTIC_DIR)

run_numbered_tests: run_selected_10

run_10: run_selected_10

fpga_diagnostics: run_selected_10_diagnostics

# Generate one 1024 x 32-bit MIF for each numbered test program.
generate_mif:
	python3 tools/generate_mif.py --selected-ten-dir "$(SELECTED_TEN_OUTPUT_DIR)" --output-dir "$(ROM_MIF_DIR)"

# Select a generated programN.mif as the ROM image consumed by InstructionMemory.
select_mif:
	@case "$(ROM_PROGRAM)" in \
		1|2|3|4|5|6|7|8|9|10) ;; \
		*) echo "ROM_PROGRAM must be a number from 1 to 10"; exit 1 ;; \
	esac; \
	test -s "$(ROM_MIF_DIR)/program$(ROM_PROGRAM).mif" || { echo "Missing $(ROM_MIF_DIR)/program$(ROM_PROGRAM).mif; run 'make generate_mif' first."; exit 1; }; \
	cp "$(ROM_MIF_DIR)/program$(ROM_PROGRAM).mif" "$(ROM_ACTIVE_MIF)"; \
	echo "Selected program$(ROM_PROGRAM).mif as $(ROM_ACTIVE_MIF)."

complete c --complete -c:
	@:

trace --trace:
	@:

test_analysis: $(EXEC)
	python3 tools/run_analysis_regressions.py

generate_analysis_vpp:
	python3 tools/generate_vpp_analysis_diagram.py

generate_sysml_vpp: generate_analysis_vpp

# Cleanup intermediate files and binary
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR) parser.gv parser.output
