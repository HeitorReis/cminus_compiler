# === Directories ===
SRC_DIR := src
PARSER_DIR := parser
BUILD_DIR := build
BIN_DIR := bin
DOCS_DIR := docs/test_files
ALL_OUTPUT_DIR := docs/output/all_machine_codes
ALL_LOG_DIR := $(ALL_OUTPUT_DIR)/logs

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
            $(SRC_DIR)/semantic.c \
            $(SRC_DIR)/symbol_table.c \
            $(SRC_DIR)/syntax_tree.c \
            $(SRC_DIR)/utils.c \
			$(SRC_DIR)/ir.c \

TEST_FILES := $(wildcard $(DOCS_DIR)/teste*.txt)
			
# === Rules ===

all: clean run

# Create necessary directories
$(BUILD_DIR) $(BIN_DIR) $(ALL_OUTPUT_DIR) $(ALL_LOG_DIR):
	mkdir -p $@

# Generate parser using bison with flags -d -v -g
$(YACC_C) $(YACC_H): $(YACC_FILE) | $(BUILD_DIR)
	bison -d -v -g $(YACC_FILE)
	mv -f parser.tab.c $(BUILD_DIR)/
	mv -f parser.tab.h $(BUILD_DIR)/


# Generate lexer using flex
$(LEX_C): $(LEX_FILE) $(YACC_H) | $(BUILD_DIR)
	flex -o $(LEX_C) $(LEX_FILE)

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
ifeq ($(TEST),1)
	$(EXEC) $(DOCS_DIR)/teste.txt > docs/output/log_compiler.txt
else ifeq ($(TEST),2)
	$(EXEC) $(DOCS_DIR)/teste2.txt > docs/output/log_compiler.txt
else ifeq ($(TEST),3)
	$(EXEC) $(DOCS_DIR)/teste3.txt > docs/output/log_compiler.txt
else ifeq ($(TEST),4)
	$(EXEC) $(DOCS_DIR)/teste4.txt > docs/output/log_compiler.txt
else ifeq ($(TEST),5)
	$(EXEC) $(DOCS_DIR)/teste5.txt > docs/output/log_compiler.txt
else ifeq ($(TEST),6)
	$(EXEC) $(DOCS_DIR)/teste6.txt > docs/output/log_compiler.txt
else ifeq ($(TEST),7)
	$(EXEC) $(DOCS_DIR)/teste7.txt > docs/output/log_compiler.txt
else
	$(EXEC) $(DOCS_DIR)/teste.txt > docs/output/log_compiler.txt
endif
	python -u codegen/main.py > docs/output/log_codegen.txt

# Run all test files and collect machine code outputs
run_all: clean $(EXEC) | $(ALL_OUTPUT_DIR) $(ALL_LOG_DIR)
	@for test_file in $(TEST_FILES); do \
		echo "Running $$test_file"; \
		base=$$(basename $$test_file .txt); \
		rm -f $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt; \
		rm -f docs/output/generated_machine_code.txt; \
		$(EXEC) $$test_file > $(ALL_LOG_DIR)/$${base}_compiler.log 2>&1 || true; \
		python3 -u codegen/main.py > $(ALL_LOG_DIR)/$${base}_codegen.log 2>&1 || true; \
		if [ -f docs/output/generated_machine_code.txt ]; then \
			cp docs/output/generated_machine_code.txt $(ALL_OUTPUT_DIR)/$${base}_machine_code.txt; \
		else \
			echo "No machine code generated for $$test_file" >> $(ALL_LOG_DIR)/$${base}_codegen.log; \
		fi; \
	done

# Cleanup intermediate files and binary
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR) parser.gv parser.output
