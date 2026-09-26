#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


WORD_MASK_32 = (1 << 32) - 1
INSTRUCTION_MEMORY_WORDS = 1 << 10
DATA_MEMORY_WORDS = 1 << 6
REPO_ROOT = Path(__file__).resolve().parents[1]
COMPILER_ROOT = REPO_ROOT / "compiler"
DEFAULT_MACHINE_CODE_PATH = COMPILER_ROOT / "docs/generated/final/assembler/machine_code/generated_machine_code.txt"
DEFAULT_ANALYSIS_OUTPUT_PATH = COMPILER_ROOT / "docs/generated/diagnostics/machine_runner/result_analysis.txt"
DEFAULT_ASSEMBLY_LISTING_PATH = COMPILER_ROOT / "docs/generated/diagnostics/assembler/assembly_to_machine.txt"
DEFAULT_SELECTED_TEN_MACHINE_CODE_DIR = COMPILER_ROOT / "docs/generated/batch/selected_10_machine_code"
DEFAULT_SELECTED_TEN_ASSEMBLY_DIR = COMPILER_ROOT / "docs/generated/batch/selected_10_assembly"
DEFAULT_SELECTED_TEN_DIAGNOSTIC_DIR = COMPILER_ROOT / "docs/generated/batch/selected_10_fpga_diagnostics"
SELECTED_TEN_DIAGNOSTIC_MAX_CYCLES = 20_000

SELECTED_TEN_PRESET_VECTORS = (
    ("01_soma_1_ate_n", (10,), (55,)),
    ("02_fatorial", (5,), (120,)),
    ("03_fibonacci", (10,), (55,)),
    ("04_numero_primo", (29,), (1,)),
    ("05_maior_elemento_vetor", (), (25,)),
    ("06_busca_linear_vetor", (15,), (4,)),
    ("07_bubble_sort", (), (1, 2, 3, 7, 8, 9)),
    ("08_mdc", (48, 18), (6,)),
    ("09_matriz_loops_aninhados", (), (100, 30)),
    ("10_carga_preempcao", (), (4992,)),
)

CONDITION_NAMES = {
    0b0000: "do",
    0b0001: "eq",
    0b0010: "neq",
    0b0011: "gt",
    0b0100: "gteq",
    0b0101: "lt",
    0b0110: "lteq",
}

SUPPORT_NAMES = {
    0b00: "na",
    0b01: "s",
    0b10: "i",
    0b11: "is",
}

OPCODE_NAMES = {
    (0b00, 0b0000): "add",
    (0b00, 0b0001): "sub",
    (0b00, 0b0010): "mul",
    (0b00, 0b0011): "div",
    (0b00, 0b0100): "and",
    (0b00, 0b0101): "or",
    (0b00, 0b0110): "xor",
    (0b00, 0b0111): "not",
    (0b00, 0b1000): "mov",
    (0b00, 0b1001): "in",
    (0b00, 0b1010): "out",
    (0b01, 0b0000): "store",
    (0b01, 0b0001): "load",
    (0b11, 0b0000): "b",
    (0b11, 0b0100): "l",
    (0b11, 0b1000): "bl",
    (0b11, 0b1100): "ll",
}


def mask32(value: int) -> int:
    return value & WORD_MASK_32


def to_signed32(value: int) -> int:
    value &= WORD_MASK_32
    if value & (1 << 31):
        return value - (1 << 32)
    return value


def sign_extend(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    mask = (1 << bits) - 1
    value &= mask
    if value & sign_bit:
        value -= 1 << bits
    return value


def verilog_divide(lhs: int, rhs: int) -> int:
    if rhs == 0:
        raise ZeroDivisionError("division by zero in simulated ALU")
    quotient = abs(lhs) // abs(rhs)
    if (lhs < 0) ^ (rhs < 0):
        quotient = -quotient
    return quotient


def parse_int(text: str) -> int:
    return int(text, 0)


def prompt_for_input_value(cycle: int, pc: int) -> int:
    while True:
        try:
            raw_value = input(f"input requested at cycle {cycle}, pc {pc}: ").strip()
        except EOFError as exc:
            raise RuntimeError(
                f"machine code requested input at cycle {cycle}, pc {pc}, "
                "but stdin ended; provide --input values or run interactively"
            ) from exc

        if not raw_value:
            continue

        try:
            return parse_int(raw_value)
        except ValueError:
            print("invalid input; enter an integer literal such as 7, -3, 0x10, or 0b101", file=sys.stderr)


@dataclass
class DecodedInstruction:
    raw: int
    cond: int
    type_code: int
    supp: int
    funct: int
    rd: int
    rh: int
    operand2: int
    ro: int
    load_bit: int
    is_immediate: bool
    set_cond_bit: bool
    should_branch: bool
    should_store_link: bool
    should_branch_to_link: bool


@dataclass
class StepTrace:
    cycle: int
    pc_before: int
    instruction_word: str
    decoded_instruction: str
    assembly_instruction: str | None
    write_condition: bool
    halted_before: bool
    halted_after: bool
    pc_after: int
    link_register: int
    output_value: list[int]


@dataclass
class ProcessorState:
    registers: list[int] = field(default_factory=lambda: [0] * 32)
    link_register: int = 0
    pc: int = 0
    flags: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    data_memory: list[int] = field(default_factory=lambda: [0] * DATA_MEMORY_WORDS)
    output_register: int = 0
    output_value: list[int] = field(default_factory=list)
    halted_temporarily: bool = False
    cycles: int = 0

    def register_variables(self) -> dict[str, int | list[int]]:
        values = {f"r{index}": value for index, value in enumerate(self.registers)}
        values["link_register"] = self.link_register
        values["pc"] = self.pc
        values["output_register"] = self.output_register
        values["output_value"] = self.output_value.copy()
        values["flag_z"] = self.flags[0]
        values["flag_n"] = self.flags[1]
        return values


@dataclass
class MachineRunResult:
    state: ProcessorState
    trace: list[StepTrace]
    machine_words: list[int]
    termination_reason: str
    last_pc_before: int | None
    last_instruction_word: str | None
    last_decoded_instruction: str | None
    last_assembly_instruction: str | None

    def to_dict(self) -> dict:
        return {
            "state": {
                **asdict(self.state),
                "register_variables": self.state.register_variables(),
            },
            "trace": [asdict(entry) for entry in self.trace],
            "machine_words": [format(word, "032b") for word in self.machine_words],
            "summary": {
                "termination_reason": self.termination_reason,
                "last_pc_before": self.last_pc_before,
                "last_instruction_word": self.last_instruction_word,
                "last_decoded_instruction": self.last_decoded_instruction,
                "last_assembly_instruction": self.last_assembly_instruction,
            },
        }


def decode_instruction(word: int) -> DecodedInstruction:
    return DecodedInstruction(
        raw=word,
        cond=(word >> 28) & 0xF,
        type_code=(word >> 26) & 0x3,
        supp=(word >> 24) & 0x3,
        funct=(word >> 20) & 0xF,
        rd=(word >> 15) & 0x1F,
        rh=(word >> 10) & 0x1F,
        operand2=word & 0x3FF,
        ro=(word >> 5) & 0x1F,
        load_bit=(word >> 20) & 0x1,
        is_immediate=bool((word >> 25) & 0x1),
        set_cond_bit=bool((word >> 24) & 0x1),
        should_branch=bool((word >> 27) & 0x1 and (word >> 26) & 0x1),
        should_store_link=bool((word >> 27) & 0x1 and (word >> 26) & 0x1 and (word >> 23) & 0x1),
        should_branch_to_link=bool((word >> 27) & 0x1 and (word >> 26) & 0x1 and (word >> 22) & 0x1),
    )


def evaluate_condition(cond: int, flags: list[int]) -> bool:
    zero = bool(flags[0])
    negative = bool(flags[1])

    if cond == 0b0000:
        return True
    if cond == 0b0001:
        return zero
    if cond == 0b0010:
        return not zero
    if cond == 0b0011:
        return (not zero) and (not negative)
    if cond == 0b0100:
        return zero or (not negative)
    if cond == 0b0101:
        return negative
    if cond == 0b0110:
        return zero or negative
    return False


def compute_alu_result(
    decoded: DecodedInstruction,
    rh_value: int,
    ro_value: int,
    peripheral_value: int,
) -> tuple[int, int, int]:
    operand2 = sign_extend(decoded.operand2, 10) if decoded.is_immediate else to_signed32(ro_value)
    lhs = to_signed32(rh_value)
    result = 0

    if decoded.type_code == 0b00:
        if decoded.funct == 0b0000:
            result = lhs + operand2
        elif decoded.funct == 0b0001:
            result = lhs - operand2
        elif decoded.funct == 0b0010:
            result = lhs * operand2
        elif decoded.funct == 0b0011:
            result = verilog_divide(lhs, operand2)
        elif decoded.funct == 0b0100:
            result = lhs & operand2
        elif decoded.funct == 0b0101:
            result = lhs | operand2
        elif decoded.funct == 0b0110:
            result = lhs ^ operand2
        elif decoded.funct == 0b0111:
            result = -lhs
        elif decoded.funct == 0b1000:
            result = operand2
        elif decoded.funct == 0b1001:
            result = peripheral_value
        elif decoded.funct == 0b1010:
            result = operand2
    elif decoded.type_code == 0b01:
        if decoded.funct in (0b0000, 0b0001):
            result = lhs
    elif decoded.type_code == 0b11:
        result = operand2

    signed_result = to_signed32(mask32(result))
    zero = 1 if signed_result == 0 else 0
    negative = 1 if signed_result < 0 else 0
    return mask32(result), zero, negative


def load_machine_words(machine_code_path: Path | None, inline_words: list[str]) -> list[int]:
    words: list[str] = []
    if machine_code_path is not None:
        for line in machine_code_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                words.append(stripped)
    words.extend(word.strip() for word in inline_words if word.strip())

    if not words:
        raise ValueError(
            "no machine code words were provided; pass a machine-code file, use --word, "
            f"or create the default file at '{DEFAULT_MACHINE_CODE_PATH}'"
        )

    parsed_words: list[int] = []
    for word in words:
        if len(word) != 32 or any(bit not in "01" for bit in word):
            raise ValueError(f"invalid 32-bit binary machine word '{word}'")
        parsed_words.append(int(word, 2))
    return parsed_words


def build_instruction_memory(machine_words: list[int]) -> list[int]:
    rom = [0] * INSTRUCTION_MEMORY_WORDS
    for index, word in enumerate(machine_words[:INSTRUCTION_MEMORY_WORDS]):
        rom[index] = word
    return rom


def format_decoded_instruction(word: int) -> str:
    decoded = decode_instruction(word)
    cond_name = CONDITION_NAMES.get(decoded.cond, "unknown")
    supp_name = SUPPORT_NAMES.get(decoded.supp, "unknown")
    opcode_name = OPCODE_NAMES.get((decoded.type_code, decoded.funct), "data")

    if decoded.type_code == 0b11:
        if opcode_name in ("l", "ll"):
            return f"{opcode_name} {cond_name}"
        if supp_name == "na":
            return f"{opcode_name} {cond_name} r{decoded.ro}"
        return f"{opcode_name} {supp_name} {cond_name} {sign_extend(decoded.operand2, 10)}"

    if supp_name in ("i", "is"):
        operand_text = str(sign_extend(decoded.operand2, 10))
    else:
        operand_text = f"r{decoded.ro}"

    return f"{opcode_name} {supp_name} {cond_name} r{decoded.rd} = r{decoded.rh}, {operand_text}"


def parse_assembly_listing_line(line: str) -> tuple[str, str] | None:
    if " -> " not in line:
        return None

    word_text, assembly_text = line.split(" -> ", 1)
    stripped_word = word_text.strip()
    if len(stripped_word) != 32 or any(bit not in "01" for bit in stripped_word):
        return None
    return stripped_word, assembly_text.strip()


def load_assembly_listing(
    machine_words: list[int],
    assembly_listing_path: Path | None,
) -> tuple[list[str] | None, Path | None]:
    if assembly_listing_path is None or not assembly_listing_path.exists():
        return None, None

    entries: list[tuple[str, str]] = []
    for line in assembly_listing_path.read_text(encoding="utf-8").splitlines():
        parsed = parse_assembly_listing_line(line)
        if parsed is not None:
            entries.append(parsed)

    if len(entries) != len(machine_words):
        return None, None

    for index, (word_text, _) in enumerate(entries):
        if word_text != format(machine_words[index], "032b"):
            return None, None

    return [assembly_text for _, assembly_text in entries], assembly_listing_path


def select_analysis_output_path(machine_code_path: Path | None, inline_words: list[str], json_requested: bool) -> Path | None:
    if json_requested or inline_words:
        return None
    if machine_code_path is None or machine_code_path == DEFAULT_MACHINE_CODE_PATH:
        return DEFAULT_ANALYSIS_OUTPUT_PATH
    return None


def build_analysis_report(
    result: MachineRunResult,
    *,
    machine_code_path: Path | None,
    assembly_listing_path: Path | None,
    trace_enabled: bool,
) -> str:
    lines = [
        "=== MACHINE CODE ANALYSIS ===",
        f"machine_code={machine_code_path or '<inline>'}",
        f"machine_words={len(result.machine_words)}",
        f"assembly_listing={assembly_listing_path or '<none>'}",
        "",
        "summary:",
        f"  cycles={result.state.cycles}",
        f"  termination_reason={result.termination_reason}",
        f"  final_pc={result.state.pc}",
        f"  halted_temporarily={int(result.state.halted_temporarily)}",
        f"  output_count={len(result.state.output_value)}",
        f"  last_pc_before={result.last_pc_before}",
        f"  last_instruction_word={result.last_instruction_word}",
        f"  last_decoded_instruction={result.last_decoded_instruction}",
    ]

    if result.last_assembly_instruction is not None:
        lines.append(f"  last_assembly_instruction={result.last_assembly_instruction}")

    lines.extend(
        [
            "",
            "final_state:",
            f"  cycles={result.state.cycles}",
            f"  pc={result.state.pc}",
            f"  link_register={result.state.link_register}",
            f"  halted_temporarily={int(result.state.halted_temporarily)}",
            f"  output_value={result.state.output_value}",
            f"  flags=Z{result.state.flags[0]} N{result.state.flags[1]}",
            "registers:",
        ]
    )

    for index, value in enumerate(result.state.registers):
        lines.append(f"  r{index}={value}")

    non_zero_memory = [
        (index, value)
        for index, value in enumerate(result.state.data_memory)
        if value != 0
    ]
    lines.append("data_memory_non_zero:")
    if non_zero_memory:
        for index, value in non_zero_memory:
            lines.append(f"  mem[{index}]={value}")
    else:
        lines.append("  <all zero>")

    if trace_enabled:
        lines.append("trace:")
        for entry in result.trace:
            trace_line = (
                f"  cycle={entry.cycle} pc_before={entry.pc_before} "
                f"instr={entry.instruction_word} decoded=\"{entry.decoded_instruction}\" "
                f"pc_after={entry.pc_after} link={entry.link_register} "
                f"halt={int(entry.halted_after)} output_value={entry.output_value}"
            )
            if entry.assembly_instruction is not None:
                trace_line += f" asm=\"{entry.assembly_instruction}\""
            lines.append(trace_line)

    return "\n".join(lines) + "\n"


def run_machine_code(
    machine_words: list[int],
    *,
    max_cycles: int,
    peripheral_inputs: list[int] | None = None,
    default_peripheral_value: int = 0,
    default_input_value: int | None = None,
    assembly_listing: list[str] | None = None,
    trace_enabled: bool = False,
    prompt_for_missing_inputs: bool = False,
) -> MachineRunResult:
    rom = build_instruction_memory(machine_words)
    state = ProcessorState()
    pending_inputs = list(peripheral_inputs or [])
    trace: list[StepTrace] = []
    last_pc_before: int | None = None
    last_instruction_word: str | None = None
    last_decoded_instruction: str | None = None
    last_assembly_instruction: str | None = None
    termination_reason = "max_cycles"

    for cycle in range(max_cycles):
        pc_before = state.pc
        halted_before = state.halted_temporarily
        instruction_word = rom[state.pc & (INSTRUCTION_MEMORY_WORDS - 1)]
        decoded = decode_instruction(instruction_word)
        instruction_word_text = format(instruction_word, "032b")
        decoded_instruction = format_decoded_instruction(instruction_word)
        assembly_instruction = None
        if assembly_listing is not None and pc_before < len(assembly_listing):
            assembly_instruction = assembly_listing[pc_before]

        rh_value = state.registers[decoded.rh]
        ro_value = state.registers[decoded.ro]
        link_value = state.link_register
        data_address = ro_value & (DATA_MEMORY_WORDS - 1)
        ram_output = state.data_memory[data_address]

        peripheral_signal = False
        peripheral_value = default_peripheral_value
        if state.halted_temporarily and pending_inputs:
            peripheral_signal = True
            peripheral_value = pending_inputs.pop(0)
        elif state.halted_temporarily and default_input_value is not None:
            peripheral_signal = True
            peripheral_value = default_input_value
        elif state.halted_temporarily and prompt_for_missing_inputs:
            peripheral_signal = True
            peripheral_value = prompt_for_input_value(cycle, state.pc)

        write_condition = evaluate_condition(decoded.cond, state.flags)
        alu_result, zero, negative = compute_alu_result(decoded, rh_value, ro_value, peripheral_value)

        is_load_instruction = decoded.type_code == 0b01 and decoded.load_bit == 1
        write_data = ram_output if is_load_instruction else alu_result

        store_link_signal = write_condition and decoded.should_store_link
        store_reg_signal = write_condition and (
            decoded.type_code == 0b00 or (decoded.type_code == 0b01 and decoded.load_bit == 1)
        )
        store_condition = write_condition and decoded.type_code == 0b01 and decoded.load_bit == 0
        update_output_reg_signal = decoded.type_code == 0b00 and decoded.funct == 0b1010

        new_halt = state.halted_temporarily
        if state.halted_temporarily and peripheral_signal:
            new_halt = False
        elif decoded.type_code == 0b00 and decoded.funct == 0b1001:
            new_halt = True

        new_registers = state.registers.copy()
        new_link_register = state.link_register
        new_data_memory = state.data_memory.copy()
        new_output_register = state.output_register
        new_output_values = state.output_value.copy()
        new_flags = state.flags.copy()

        if store_reg_signal:
            new_registers[decoded.rd] = mask32(write_data)

        if store_link_signal:
            new_link_register = mask32(state.pc + 1)

        if store_condition:
            new_data_memory[data_address] = mask32(alu_result)

        if update_output_reg_signal:
            new_output_register = mask32(alu_result)
            new_output_values.append(to_signed32(new_output_register))

        if decoded.set_cond_bit and write_condition:
            new_flags[0] = zero
            new_flags[1] = negative
            new_flags[2] = 0
            new_flags[3] = 0

        new_pc = state.pc
        if not new_halt:
            if write_condition and decoded.should_branch:
                if decoded.should_branch_to_link:
                    new_pc = mask32(link_value)
                elif decoded.is_immediate:
                    new_pc = mask32(state.pc + alu_result)
                else:
                    new_pc = mask32(alu_result)
            else:
                new_pc = mask32(state.pc + 1)

        state = ProcessorState(
            registers=new_registers,
            link_register=new_link_register,
            pc=new_pc,
            flags=new_flags,
            data_memory=new_data_memory,
            output_register=new_output_register,
            output_value=new_output_values,
            halted_temporarily=new_halt,
            cycles=cycle + 1,
        )

        last_pc_before = pc_before
        last_instruction_word = instruction_word_text
        last_decoded_instruction = decoded_instruction
        last_assembly_instruction = assembly_instruction

        if trace_enabled:
            trace.append(
                StepTrace(
                    cycle=cycle,
                    pc_before=pc_before,
                    instruction_word=instruction_word_text,
                    decoded_instruction=decoded_instruction,
                    assembly_instruction=assembly_instruction,
                    write_condition=write_condition,
                    halted_before=halted_before,
                    halted_after=new_halt,
                    pc_after=state.pc,
                    link_register=state.link_register,
                    output_value=state.output_value.copy(),
                )
            )

        if assembly_instruction == "ret -> bi 0":
            termination_reason = "ret"
            break

    return MachineRunResult(
        state=state,
        trace=trace,
        machine_words=machine_words,
        termination_reason=termination_reason,
        last_pc_before=last_pc_before,
        last_instruction_word=last_instruction_word,
        last_decoded_instruction=last_decoded_instruction,
        last_assembly_instruction=last_assembly_instruction,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run machine code against a Python model of the current Processor(v2026-1) RTL."
    )
    parser.add_argument(
        "machine_code",
        nargs="?",
        help="Path to a text file containing one 32-bit binary machine word per line.",
    )
    parser.add_argument(
        "--word",
        action="append",
        default=[],
        help="Inline 32-bit binary machine word. May be repeated.",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=500,
        help="Maximum number of instruction cycles to simulate.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        type=parse_int,
        help="Peripheral input value delivered when the processor is halted on an IN instruction. May be repeated.",
    )
    parser.add_argument(
        "--prompt-inputs",
        action="store_true",
        help="Prompt on stdin when an `in` instruction needs a value and no --input values remain.",
    )
    parser.add_argument(
        "--default-peripheral",
        type=parse_int,
        default=0,
        help="Default peripheral value seen by non-blocking reads.",
    )
    parser.add_argument(
        "--default-input",
        type=parse_int,
        help="Fallback input value used when an `in` instruction blocks and no --input values remain.",
    )
    parser.add_argument(
        "--assembly-listing",
        help=(
            "Path to a debug assembly listing in '<binary> -> <assembly>' format. "
            "When present, trace lines also show the matching assembly instruction."
        ),
    )
    parser.add_argument(
        "--analysis-output",
        help="Write the final analysis report to this path.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Include per-cycle trace information in the output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the final state as JSON.",
    )
    parser.add_argument(
        "--selected-10-diagnostics",
        action="store_true",
        help="Run the fixed input/output FPGA diagnostic vectors for the selected ten-test suite.",
    )
    parser.add_argument(
        "--diagnostic-machine-code-dir",
        default=str(DEFAULT_SELECTED_TEN_MACHINE_CODE_DIR),
        help="Directory containing the selected-ten *_machine_code.txt files.",
    )
    parser.add_argument(
        "--diagnostic-assembly-dir",
        default=str(DEFAULT_SELECTED_TEN_ASSEMBLY_DIR),
        help="Directory containing per-test *_assembly_to_machine.txt listings.",
    )
    parser.add_argument(
        "--diagnostic-output-dir",
        default=str(DEFAULT_SELECTED_TEN_DIAGNOSTIC_DIR),
        help="Directory where selected-ten FPGA diagnostic reports are written.",
    )
    parser.add_argument(
        "--diagnostic-max-cycles",
        type=int,
        default=SELECTED_TEN_DIAGNOSTIC_MAX_CYCLES,
        help="Maximum cycles per selected-ten FPGA diagnostic run.",
    )
    return parser


def fpga_display_value(value: int | None) -> str:
    if value is None:
        return "<no output>"
    return f"{value % 100:02d}"


def run_selected_ten_diagnostics(
    *,
    machine_code_dir: Path,
    assembly_dir: Path,
    output_dir: Path,
    max_cycles: int,
    trace_enabled: bool,
) -> bool:
    if max_cycles <= 0:
        raise ValueError("diagnostic max cycles must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    for test_name, input_values, expected_outputs in SELECTED_TEN_PRESET_VECTORS:
        machine_code_path = machine_code_dir / f"{test_name}_machine_code.txt"
        assembly_listing_path = assembly_dir / f"{test_name}_assembly_to_machine.txt"
        if not machine_code_path.is_file():
            raise FileNotFoundError(f"machine code for '{test_name}' not found: {machine_code_path}")
        if not assembly_listing_path.is_file():
            raise FileNotFoundError(f"assembly listing for '{test_name}' not found: {assembly_listing_path}")

        machine_words = load_machine_words(machine_code_path, [])
        assembly_listing, resolved_listing_path = load_assembly_listing(machine_words, assembly_listing_path)
        if assembly_listing is None or resolved_listing_path is None:
            raise ValueError(f"assembly listing does not match machine code for '{test_name}'")

        result = run_machine_code(
            machine_words,
            max_cycles=max_cycles,
            peripheral_inputs=list(input_values),
            assembly_listing=assembly_listing,
            trace_enabled=trace_enabled,
            prompt_for_missing_inputs=False,
        )
        actual_outputs = result.state.output_value
        passed = actual_outputs == list(expected_outputs) and result.termination_reason == "ret"
        report_path = output_dir / f"{test_name}_fpga_diagnostic.txt"
        json_path = output_dir / f"{test_name}_fpga_diagnostic.json"
        report_header = [
            "=== PRESET FPGA DIAGNOSTIC ===",
            f"test={test_name}",
            f"status={'PASS' if passed else 'FAIL'}",
            f"input_values={list(input_values)}",
            f"expected_output={list(expected_outputs)}",
            f"model_output={actual_outputs}",
            f"fpga_hex6_hex7_after_last_output={fpga_display_value(actual_outputs[-1] if actual_outputs else None)}",
            f"cycles={result.state.cycles}",
            f"termination_reason={result.termination_reason}",
            "fpga_input_note=For each input value, set SW[7:0], then release the halted IN instruction with SW[15] transition 1->0.",
            "fpga_output_note=HEX6-HEX7 show the last output's two least-significant decimal digits; capture each OUT for multi-output tests.",
            "",
        ]
        report_path.write_text(
            "\n".join(report_header)
            + build_analysis_report(
                result,
                machine_code_path=machine_code_path,
                assembly_listing_path=resolved_listing_path,
                trace_enabled=trace_enabled,
            ),
            encoding="utf-8",
        )
        diagnostic_result = {
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "input_values": list(input_values),
            "expected_output": list(expected_outputs),
            "model_output": actual_outputs,
            "fpga_hex6_hex7_after_last_output": fpga_display_value(actual_outputs[-1] if actual_outputs else None),
            "cycles": result.state.cycles,
            "termination_reason": result.termination_reason,
            "report": str(report_path),
        }
        json_path.write_text(json.dumps({**diagnostic_result, "machine_result": result.to_dict()}, indent=2) + "\n", encoding="utf-8")
        results.append(diagnostic_result)
        print(f"{'PASS' if passed else 'FAIL'} {test_name}: expected {list(expected_outputs)}, got {actual_outputs}")

    passed_count = sum(result["status"] == "PASS" for result in results)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "passed": passed_count,
                "total": len(results),
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Preset FPGA diagnostics: {passed_count}/{len(results)} passed. Reports: {output_dir}")
    return passed_count == len(results)


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.selected_10_diagnostics:
        try:
            passed = run_selected_ten_diagnostics(
                machine_code_dir=Path(args.diagnostic_machine_code_dir),
                assembly_dir=Path(args.diagnostic_assembly_dir),
                output_dir=Path(args.diagnostic_output_dir),
                max_cycles=args.diagnostic_max_cycles,
                trace_enabled=args.trace,
            )
        except (OSError, ValueError) as error:
            parser.exit(1, f"Selected-ten FPGA diagnostics failed: {error}\n")
        if not passed:
            raise SystemExit(1)
        return

    machine_code_path = Path(args.machine_code) if args.machine_code else None
    if machine_code_path is None and not args.word and DEFAULT_MACHINE_CODE_PATH.exists():
        machine_code_path = DEFAULT_MACHINE_CODE_PATH
    machine_words = load_machine_words(machine_code_path, args.word)
    requested_assembly_listing_path = Path(args.assembly_listing) if args.assembly_listing else DEFAULT_ASSEMBLY_LISTING_PATH
    assembly_listing, resolved_assembly_listing_path = load_assembly_listing(machine_words, requested_assembly_listing_path)
    result = run_machine_code(
        machine_words,
        max_cycles=args.max_cycles,
        peripheral_inputs=args.input,
        default_peripheral_value=args.default_peripheral,
        default_input_value=args.default_input,
        assembly_listing=assembly_listing,
        trace_enabled=args.trace,
        prompt_for_missing_inputs=args.prompt_inputs or sys.stdin.isatty(),
    )

    if args.json:
        rendered_output = json.dumps(result.to_dict(), indent=2)
        print(rendered_output)
        if args.analysis_output:
            analysis_output_path = Path(args.analysis_output)
            analysis_output_path.parent.mkdir(parents=True, exist_ok=True)
            analysis_output_path.write_text(rendered_output + "\n", encoding="utf-8")
        return

    rendered_output = build_analysis_report(
        result,
        machine_code_path=machine_code_path,
        assembly_listing_path=resolved_assembly_listing_path,
        trace_enabled=args.trace,
    )
    print(rendered_output, end="")

    analysis_output_path = Path(args.analysis_output) if args.analysis_output else select_analysis_output_path(
        machine_code_path,
        args.word,
        args.json,
    )
    if analysis_output_path is not None:
        analysis_output_path.parent.mkdir(parents=True, exist_ok=True)
        analysis_output_path.write_text(rendered_output, encoding="utf-8")


if __name__ == "__main__":
    main()
