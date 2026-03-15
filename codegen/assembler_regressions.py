from assembler import FullCode
from constants import STACK_WORDS


def assert_success(machine_code, context):
    if 'Error' in machine_code.response:
        raise AssertionError(f"{context}: {machine_code.response}")


def run_conditional_parse_regression():
    assembly = [
        ".text",
        ".global main",
        "main:",
        "\taddeqi: r1 = r2, 3",
        "\tret:",
        ".data",
        f"stack_space: .space {STACK_WORDS}",
    ]
    machine_code = FullCode(assembly)
    assert_success(machine_code, "conditional parse")
    first_word = machine_code.full_code.splitlines()[0]
    assert first_word[:4] == "0001", "conditional parse: expected EQ condition bits"
    assert first_word[6:8] == "10", "conditional parse: expected immediate support bits"


def run_long_branch_regression():
    assembly = [
        ".text",
        ".global main",
        "main:",
        "\tbi: far_away",
    ]
    assembly.extend("\taddi: r4 = r4, 1" for _ in range(620))
    assembly.extend(
        [
            "far_away:",
            "\tret:",
            ".data",
            f"stack_space: .space {STACK_WORDS}",
        ]
    )
    machine_code = FullCode(assembly)
    assert_success(machine_code, "long branch")
    assert "long branch" in machine_code.debug_output, "long branch: expansion did not happen"


if __name__ == "__main__":
    run_conditional_parse_regression()
    run_long_branch_regression()
    print("Assembler regressions passed.")
