#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ACTIVITY_DIAGRAM_NAME = "Diagrama de Atividades - Fluxo de Compilação C- para Código Binário ARM Simplificado"
BLOCK_DIAGRAM_NAME = "Diagrama de Blocos - Arquitetura Interna do Compilador"
ENCODER_DIAGRAM_NAME = "Diagrama Interno - Codificador Binário"
TRACEABILITY_DIAGRAM_NAME = "Diagrama de Rastreabilidade - C- para IR, Assembly e Binário"
MODULE_HIERARCHY_DIAGRAM_NAME = "Diagrama de Blocos — Hierarquia dos Módulos do Compilador"
PARENT_ACTIVITY_NAME = "Fluxo de Compilação C- para ARM Simplificado"
MAIN_BLOCK_NAME = "Compilador C- para ARM Simplificado"
HEADERS = {
    "Entrada do Usuário / Código-fonte",
    "Analisador Léxico",
    "Analisador Sintático",
    "Analisador Semântico",
    "Tabela de Símbolos",
    "Gerador de Código Intermediário",
    "Alocador de Registradores",
    "Gerador de Assembly",
    "Resolvedor de Rótulos",
    "Codificador Binário",
    "Validador / Gerador de Arquivo",
}
REQUIRED_ACTIONS = {
    "Receber código-fonte C-",
    "Realizar análise léxica",
    "Gerar relatório de erro léxico",
    "Realizar análise sintática",
    "Gerar relatório de erro sintático",
    "Realizar análise semântica",
    "Consultar/atualizar tabela de símbolos",
    "Gerar relatório de erro semântico",
    "Consultar tabela para geração de IR",
    "Gerar código intermediário",
    "Consultar tabela para alocação",
    "Mapear variáveis e temporários para registradores",
    "Gerar assembly ARM simplificado",
    "Resolver rótulos e desvios",
    "Codificar instruções em binário de 32 bits - Cond[31:28], Type[27:26], Supp[25:24], Funct[23:20], Rd[19:15], Rh[14:10], Operand2[9:0]",
    "Validar instruções binárias",
    "Gerar relatório de erro de codificação",
    "Gerar arquivo de código de máquina",
    "Gerar relatório de erro",
}
REQUIRED_DECISIONS = {
    "Tokens válidos?",
    "Sintaxe válida?",
    "Semântica válida?",
    "Binário válido?",
}
REQUIRED_BLOCKS = {
    MAIN_BLOCK_NAME,
    "Gerenciador de Compilação",
    "Analisador Léxico",
    "Analisador Sintático",
    "Analisador Semântico",
    "Tabela de Símbolos",
    "Gerador de Código Intermediário",
    "Alocador de Registradores",
    "Gerador de Assembly ARM Simplificado",
    "Resolvedor de Rótulos",
    "Codificador Binário - recebe assemblyResolvido; gera instrucoesBinarias; formato Cond[31:28], Type[27:26], Supp[25:24], Funct[23:20], Rd[19:15], Rh[14:10], Operand2[9:0]",
    "CondEncoder - Cond[31:28]: do/sem condição=0000, eq=0001, neq=0010, gt=0011, gteq=0100, lt=0101, lteq=0110",
    "TypeEncoder - Type[27:26]: 00 processamento de dados, 01 load/store, 11 branch",
    "SuppEncoder - Supp[25:24]: 00 normal, 10 imediato, 01 atualiza CPSR, 11 imediato e CPSR",
    "FunctEncoder - Funct[23:20]: add=0000, sub=0001, mul=0010, div=0011, and=0100, or=0101, xor=0110, not=0111, mov=1000",
    "RegisterEncoder - Rd[19:15] e Rh[14:10]: r0=00000, r1=00001, r2=00010, r31=11111",
    "Operand2Encoder - Operand2[9:0]: imediato de 10 bits com sinal ou Ro em [9:5] e [4:0]=00000",
    "Validador de Código Binário",
    "Gerador de Arquivo de Saída",
}

EXPECTED_DIAGRAM_NAMES = {
    ACTIVITY_DIAGRAM_NAME,
    BLOCK_DIAGRAM_NAME,
    ENCODER_DIAGRAM_NAME,
    TRACEABILITY_DIAGRAM_NAME,
    MODULE_HIERARCHY_DIAGRAM_NAME,
}

MODULE_HIERARCHY_BLOCKS = {
    "Hierarquia real do código — pastas, arquivos e partes importantes",
    "compiler/main.c — abre entrada, chama parser, semântica e limpeza",
    "lexer.l — regras Flex da análise léxica",
    "parser.y — gramática C- e ações semânticas do parser",
    "syntax_tree.c/h — árvore sintática genérica",
    "symbol_table.c/h — tabela de símbolos do frontend",
    "semantic.c/h — análise semântica",
    "ir.c/h — geração de código intermediário",
    "codegen.py — IR textual para assembly",
    "assembler.py — assembler e codificador binário",
    "tools/generate_vpp_analysis_diagram.py — gera os diagramas SysML do projeto",
}


@dataclass
class FrontendRun:
    returncode: int
    stdout: str
    stderr: str
    ir_text: str | None


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_frontend(binary: Path, fixture: Path) -> FrontendRun:
    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        result = subprocess.run(
            [str(binary), str(fixture)],
            cwd=workdir,
            text=True,
            capture_output=True,
        )
        ir_path = workdir / "docs" / "generated" / "intermediate" / "semantic" / "ir" / "generated_IR.txt"
        ir_text = ir_path.read_text(encoding="utf-8") if ir_path.exists() else None
        return FrontendRun(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            ir_text=ir_text,
        )


def test_valid_case(binary: Path, fixtures_dir: Path) -> None:
    run = run_frontend(binary, fixtures_dir / "sort.txt")
    assert_true(run.returncode == 0, "valid case should exit with 0")
    assert_true("=== AST ===" in run.stdout, "valid case should print AST")
    assert_true("======= SYMBOL TABLE =======" in run.stdout, "valid case should print symbol table")
    assert_true("=== IR ===" in run.stdout, "valid case should print IR marker")
    assert_true(run.ir_text is not None, "valid case should generate IR file")
    assert_true("main:" in run.ir_text, "generated IR should contain main label")
    assert_true(
        run.stdout.index("=== IR ===") < run.stdout.index("======= SYMBOL TABLE ======="),
        "symbol table must be printed after semantic analysis closes",
    )


def test_lexical_case(binary: Path, fixtures_dir: Path) -> None:
    run = run_frontend(binary, fixtures_dir / "invalid_lexical_error.txt")
    combined = run.stdout + run.stderr
    assert_true(run.returncode != 0, "lexical case should fail")
    assert_true("lexical error" in combined.lower(), "lexical case should report a lexical error")
    assert_true("syntax error" not in combined.lower(), "lexical case must not emit syntax error")
    assert_true("=== AST ===" not in run.stdout, "lexical case must not print AST")
    assert_true("======= SYMBOL TABLE =======" not in run.stdout, "lexical case must not print symbol table")
    assert_true("=== IR ===" not in run.stdout, "lexical case must not print IR")
    assert_true(run.ir_text is None, "lexical case must not generate IR")


def test_syntax_case(binary: Path, fixtures_dir: Path) -> None:
    run = run_frontend(binary, fixtures_dir / "invalid_syntax_error.txt")
    combined = run.stdout + run.stderr
    assert_true(run.returncode != 0, "syntax case should fail")
    assert_true("syntax error" in combined.lower(), "syntax case should report syntax error")
    assert_true("Semantic analysis failed" not in run.stderr, "syntax case must not run semantics")
    assert_true("=== AST ===" not in run.stdout, "syntax case must not print AST")
    assert_true("======= SYMBOL TABLE =======" not in run.stdout, "syntax case must not print symbol table")
    assert_true("=== IR ===" not in run.stdout, "syntax case must not print IR")
    assert_true(run.ir_text is None, "syntax case must not generate IR")


def test_semantic_case(binary: Path, fixtures_dir: Path) -> None:
    run = run_frontend(binary, fixtures_dir / "invalid_missing_return.txt")
    combined = run.stdout + run.stderr
    assert_true(run.returncode != 0, "semantic case should fail")
    assert_true("non-void function" in combined, "semantic case should report missing return")
    assert_true("Syntactic analysis failed" not in run.stderr, "semantic case must not be counted as syntax")
    assert_true("=== AST ===" in run.stdout, "semantic case should still print AST")
    assert_true("=== IR ===" not in run.stdout, "semantic case must not print IR")
    assert_true(run.ir_text is None, "semantic case must not generate IR")


def test_undeclared_identifier_case(binary: Path, fixtures_dir: Path) -> None:
    run = run_frontend(binary, fixtures_dir / "invalid_undeclared_identifier.txt")
    combined = run.stdout + run.stderr
    assert_true(run.returncode != 0, "undeclared identifier case should fail")
    assert_true("use of undeclared identifier 'y'" in combined, "semantic case should report undeclared identifier")
    assert_true("Syntactic analysis failed" not in run.stderr, "undeclared identifier must not go through yyerror")
    assert_true("=== AST ===" in run.stdout, "undeclared identifier case should still print AST")
    assert_true(run.ir_text is None, "undeclared identifier case must not generate IR")


def test_missing_main_case(binary: Path, fixtures_dir: Path) -> None:
    run = run_frontend(binary, fixtures_dir / "invalid_missing_main.txt")
    combined = run.stdout + run.stderr
    assert_true(run.returncode != 0, "missing main case should fail")
    assert_true("missing global function 'main'" in combined, "missing main case should report dedicated message")
    assert_true("=== AST ===" in run.stdout, "missing main case should still print AST")
    assert_true("=== IR ===" not in run.stdout, "missing main case must not print IR")
    assert_true(run.ir_text is None, "missing main case must not generate IR")


def test_vpp_case(repo_root: Path) -> None:
    generator = repo_root / "tools" / "generate_vpp_analysis_diagram.py"
    source_vpp = repo_root / "vpp" / "cminus-compiler-expanded.vpp"
    with tempfile.TemporaryDirectory() as tmpdir:
        target_vpp = Path(tmpdir) / "analysis-test.vpp"
        shutil.copy2(source_vpp, target_vpp)
        subprocess.run(
            [sys.executable, str(generator), str(target_vpp)],
            check=True,
            text=True,
            capture_output=True,
        )

        connection = sqlite3.connect(target_vpp)
        cursor = connection.cursor()
        diagram_names = {
            name
            for (name,) in cursor.execute("select NAME from DIAGRAM")
        }
        assert_true(diagram_names == EXPECTED_DIAGRAM_NAMES, "VPP must contain only the current compiler SysML diagrams")

        activity_diagram = cursor.execute(
            "select ID, PARENT_MODEL_ID from DIAGRAM where NAME=?",
            (ACTIVITY_DIAGRAM_NAME,),
        ).fetchone()
        assert_true(activity_diagram is not None, "activity diagram must exist in VPP")
        activity_diagram_id, parent_id = activity_diagram

        parent = cursor.execute(
            "select MODEL_TYPE, NAME from MODEL_ELEMENT where ID=?",
            (parent_id,),
        ).fetchone()
        assert_true(parent == ("Activity", PARENT_ACTIVITY_NAME), "activity diagram parent must be the compiler flow activity")

        model_rows = cursor.execute(
            "select MODEL_TYPE, NAME from MODEL_ELEMENT where PARENT_ID=?",
            (parent_id,),
        ).fetchall()
        names = {name for _, name in model_rows}
        assert_true(HEADERS.issubset(names), "all activity swimlane headers must exist")
        assert_true(REQUIRED_ACTIONS.issubset(names), "all required actions must exist")
        assert_true(REQUIRED_DECISIONS.issubset(names), "all required decisions must exist")

        controlflow_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='ControlFlow'
            """,
            (activity_diagram_id,),
        ).fetchone()[0]
        assert_true(controlflow_count == 28, "activity diagram must contain the expected control flows")

        block_diagram = cursor.execute(
            "select ID, PARENT_MODEL_ID from DIAGRAM where NAME=?",
            (BLOCK_DIAGRAM_NAME,),
        ).fetchone()
        assert_true(block_diagram is not None, "block definition diagram must exist in VPP")
        block_diagram_id, block_parent_id = block_diagram

        block_parent = cursor.execute(
            "select MODEL_TYPE, NAME from MODEL_ELEMENT where ID=?",
            (block_parent_id,),
        ).fetchone()
        assert_true(block_parent == ("SysMLBlock", MAIN_BLOCK_NAME), "block diagram parent must be the main compiler block")

        block_names = {
            name
            for (name,) in cursor.execute(
                "select NAME from MODEL_ELEMENT where MODEL_TYPE='SysMLBlock'"
            )
        }
        assert_true(REQUIRED_BLOCKS.issubset(block_names), "all required compiler blocks must exist")

        block_shape_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='SysMLBlock'
            """,
            (block_diagram_id,),
        ).fetchone()[0]
        assert_true(block_shape_count == 19, "block diagram must contain the expected block shapes")

        association_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='Association'
            """,
            (block_diagram_id,),
        ).fetchone()[0]
        assert_true(association_count == 18, "block diagram must contain the expected associations")

        encoder_diagram = cursor.execute(
            "select ID from DIAGRAM where NAME=?",
            (ENCODER_DIAGRAM_NAME,),
        ).fetchone()
        assert_true(encoder_diagram is not None, "encoder detail diagram must exist in VPP")
        encoder_diagram_id = encoder_diagram[0]
        encoder_block_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='SysMLBlock'
            """,
            (encoder_diagram_id,),
        ).fetchone()[0]
        assert_true(encoder_block_count == 9, "encoder diagram must show the codifier encoders and boundary flow")

        module_hierarchy_diagram = cursor.execute(
            "select ID, PARENT_MODEL_ID from DIAGRAM where NAME=?",
            (MODULE_HIERARCHY_DIAGRAM_NAME,),
        ).fetchone()
        assert_true(module_hierarchy_diagram is not None, "module hierarchy diagram must exist in VPP")
        module_hierarchy_diagram_id, module_parent_id = module_hierarchy_diagram
        module_parent = cursor.execute(
            "select MODEL_TYPE, NAME from MODEL_ELEMENT where ID=?",
            (module_parent_id,),
        ).fetchone()
        assert_true(
            module_parent == ("SysMLBlock", MAIN_BLOCK_NAME),
            "module hierarchy diagram parent must be the main compiler block",
        )
        assert_true(MODULE_HIERARCHY_BLOCKS.issubset(block_names), "module hierarchy must use real code block names")
        module_block_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='SysMLBlock'
            """,
            (module_hierarchy_diagram_id,),
        ).fetchone()[0]
        assert_true(module_block_count >= 70, "module hierarchy diagram must contain the real file/function blocks")
        module_association_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='Association'
            """,
            (module_hierarchy_diagram_id,),
        ).fetchone()[0]
        assert_true(module_association_count >= 20, "module hierarchy diagram must show dependencies between modules")

        traceability_diagram = cursor.execute(
            "select ID from DIAGRAM where NAME=?",
            (TRACEABILITY_DIAGRAM_NAME,),
        ).fetchone()
        assert_true(traceability_diagram is not None, "traceability diagram must exist in VPP")
        traceability_diagram_id = traceability_diagram[0]
        traceability_action_count = cursor.execute(
            """
            select count(*)
            from DIAGRAM_ELEMENT
            where DIAGRAM_ID=? and SHAPE_TYPE='ActivityAction'
            """,
            (traceability_diagram_id,),
        ).fetchone()[0]
        assert_true(traceability_action_count == 4, "traceability diagram must show C-, IR, assembly, and binary")

        for generated_diagram_id in (
            activity_diagram_id,
            block_diagram_id,
            encoder_diagram_id,
            module_hierarchy_diagram_id,
            traceability_diagram_id,
        ):
            project_files = {
                row[0]
                for row in cursor.execute(
                    "select PATH from PROJECT_FILE where PATH like ? or PATH like ?",
                    (f"vpdiagramshapes/{generated_diagram_id}.vps/%", "diagramPreviewData/%"),
                )
            }
            assert_true(
                any(path.endswith("details.xml") for path in project_files),
                "details.xml blob must exist for each generated diagram",
            )

        connection.close()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    compiler_root = repo_root / "compiler"
    binary = compiler_root / "bin" / "c-c"
    fixtures_dir = compiler_root / "docs" / "input" / "cminus"

    assert_true(binary.exists(), "frontend binary not found; run `make -C compiler bin/c-c` first")

    tests = [
        ("valid case", lambda: test_valid_case(binary, fixtures_dir)),
        ("lexical case", lambda: test_lexical_case(binary, fixtures_dir)),
        ("syntax case", lambda: test_syntax_case(binary, fixtures_dir)),
        ("semantic case", lambda: test_semantic_case(binary, fixtures_dir)),
        ("undeclared identifier case", lambda: test_undeclared_identifier_case(binary, fixtures_dir)),
        ("missing main case", lambda: test_missing_main_case(binary, fixtures_dir)),
    ]

    source_vpp = repo_root / "vpp" / "cminus-compiler-expanded.vpp"
    if source_vpp.exists():
        tests.append(("vpp case", lambda: test_vpp_case(repo_root)))
    else:
        print(f"SKIP vpp case (optional artifact not found: {source_vpp})")

    for label, func in tests:
        func()
        print(f"PASS {label}")

    print("Analysis regressions passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
