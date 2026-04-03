# === Directories ===
SRC_DIR := src
PARSER_DIR := parser
BUILD_DIR := build
BIN_DIR := bin
DOCS_DIR := docs/test_files
ALL_OUTPUT_DIR := docs/output/all_machine_codes
ALL_LOG_DIR := $(ALL_OUTPUT_DIR)/logs
RUN_ALL_COMPLETE := $(strip $(filter 1 true yes on,$(COMPLETE)) $(filter complete c --complete -c,$(MAKECMDGOALS)))
RUN_MACHINE_ARGS ?= --max-cycles 500 --default-input 0

# === Files ===
LEX_FILE := $(PARSER_DIR)/lexer.l
YACC_FILE := $(PARSER_DIR)/parser.y
EXEC := $(BIN_DIR)/c-c  # renaming executable to "c-c" as per the linking command

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
			
# === Rules ===

.PHONY: all run run_all complete c --complete -c test_analysis generate_analysis_vpp clean

all: clean run

# Create necessary directories
$(BUILD_DIR) $(BIN_DIR) $(ALL_OUTPUT_DIR) $(ALL_LOG_DIR):
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
run: $(EXEC)
	@case "$(TEST)" in \
		""|1|sort|teste) test_file="$(DOCS_DIR)/sort.txt" ;; \
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
	$(EXEC) "$$test_file" > docs/output/log_compiler.txt
	python3 -u codegen/main.py > docs/output/log_codegen.txt

# Run all test files and collect machine code outputs
run_all: clean $(EXEC) | $(ALL_OUTPUT_DIR) $(ALL_LOG_DIR)
	@rm -f $(ALL_OUTPUT_DIR)/*_machine_code.txt
	@rm -f $(ALL_LOG_DIR)/*.log
	@for test_file in $(RUN_ALL_TEST_FILES); do \
		echo "Running $$test_file"; \
		base=$$(basename $$test_file .txt); \
		rm -f $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt; \
		rm -f docs/output/generated_machine_code.txt; \
		$(EXEC) $$test_file > $(ALL_LOG_DIR)/$${base}_compiler.log 2>&1 || true; \
		python3 -u codegen/main.py > $(ALL_LOG_DIR)/$${base}_codegen.log 2>&1 || true; \
		if [ -f docs/output/generated_machine_code.txt ]; then \
			cp docs/output/generated_machine_code.txt $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt; \
			if [ -n "$(RUN_ALL_COMPLETE)" ]; then \
				python3 -u tools/run_machine_code.py $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt $(RUN_MACHINE_ARGS) > $(ALL_LOG_DIR)/$${base}_machine_run.log 2>&1 || true; \
			fi; \
		else \
			echo "No machine code generated for $$test_file" >> $(ALL_LOG_DIR)/$${base}_codegen.log; \
			if [ -n "$(RUN_ALL_COMPLETE)" ]; then \
				echo "Machine-code runner skipped because no machine code was generated for $$test_file" > $(ALL_LOG_DIR)/$${base}_machine_run.log; \
			fi; \
		fi; \
	done

complete c --complete -c:
	@:

test_analysis: $(EXEC)
	python3 tools/run_analysis_regressions.py

generate_analysis_vpp:
	python3 tools/generate_vpp_analysis_diagram.py

# Cleanup intermediate files and binary
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR) parser.gv parser.output
