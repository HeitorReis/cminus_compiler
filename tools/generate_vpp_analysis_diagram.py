#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import random
import re
import sqlite3
import string
import struct
import sys
import time
import zlib
from dataclasses import dataclass
from pathlib import Path


AUTHOR = "codex"
ROOT_MODEL_NAME = "main"
ACTIVITY_PARENT_NAME = "Fluxo de Compilação C- para ARM Simplificado"
MAIN_BLOCK_NAME = "Compilador C- para ARM Simplificado"
TRACEABILITY_PARENT_NAME = "Rastreabilidade C- para IR, Assembly e Binário"
ACTIVITY_DIAGRAM_NAME = "Diagrama de Atividades - Fluxo de Compilação C- para Código Binário ARM Simplificado"
BLOCK_DIAGRAM_NAME = "Diagrama de Blocos - Arquitetura Interna do Compilador"
ENCODER_DIAGRAM_NAME = "Diagrama Interno - Codificador Binário"
TRACEABILITY_DIAGRAM_NAME = "Diagrama de Rastreabilidade - C- para IR, Assembly e Binário"
MODULE_HIERARCHY_DIAGRAM_NAME = "Diagrama de Blocos — Hierarquia dos Módulos do Compilador"
TARGET_BLOCK_NAME = "Arquitetura alvo ARM simplificada (Processor(v2026-1)/) — destino do binário gerado"
BLOCK_STEREOTYPE_NAME = "block"
ID_ALPHABET = string.ascii_letters + string.digits + "._"
TOKEN_RE = re.compile(r"[A-Za-z0-9._]{16}")

CURRENT_DIAGRAM_NAMES = {
    ACTIVITY_DIAGRAM_NAME,
    BLOCK_DIAGRAM_NAME,
    ENCODER_DIAGRAM_NAME,
    TRACEABILITY_DIAGRAM_NAME,
    MODULE_HIERARCHY_DIAGRAM_NAME,
}

CURRENT_ROOT_MODEL_NAMES = {
    ACTIVITY_PARENT_NAME,
    MAIN_BLOCK_NAME,
    TRACEABILITY_PARENT_NAME,
    TARGET_BLOCK_NAME,
}

ACTIVITY_LANES = (
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
)

REQUIRED_ACTIVITY_ACTIONS = (
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
)

REQUIRED_ACTIVITY_DECISIONS = (
    "Tokens válidos?",
    "Sintaxe válida?",
    "Semântica válida?",
    "Binário válido?",
)

REQUIRED_BLOCKS = (
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
)


@dataclass(frozen=True)
class ActivityNodeSpec:
    key: str
    model_type: str
    name: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class EdgeSpec:
    key: str
    src: str
    dst: str
    label: str | None = None


@dataclass(frozen=True)
class BlockSpec:
    key: str
    name: str
    x: int
    y: int
    width: int
    height: int
    parent_key: str | None = None


@dataclass(frozen=True)
class AssociationSpec:
    key: str
    src: str
    dst: str
    label: str


def now_ms() -> int:
    return int(time.time() * 1000)


def now_s() -> int:
    return int(time.time())


def quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def name_literal(value: str | None) -> str:
    return "NULL" if value is None else f'"{quote(value)}"'


def encode_text(value: str) -> bytes:
    return value.encode("utf-8")


def blob_to_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def generate_id(existing_ids: set[str]) -> str:
    while True:
        candidate = "".join(random.choice(ID_ALPHABET) for _ in range(16))
        if candidate not in existing_ids:
            existing_ids.add(candidate)
            return candidate


def find_one(cursor: sqlite3.Cursor, query: str, params: tuple = ()) -> tuple:
    row = cursor.execute(query, params).fetchone()
    if not row:
        raise RuntimeError(f"Query returned no rows: {query!r}")
    return row


def extract_child_ids(definition: str) -> list[str]:
    match = re.search(r"Child=\(\s*(.*?)\s*\);", definition, re.S)
    if not match:
        return []
    return re.findall(r"<[^>]*:([^:>]+)>", match.group(1))


def extract_simple_ids(definition: str) -> list[str]:
    match = re.search(r"Child=\(\s*(.*?)\s*\);", definition, re.S)
    if not match:
        return []
    return re.findall(r"<([^>]+)>", match.group(1))


def extract_preview_id(definition: str) -> str | None:
    match = re.search(r'diagramPreviewData_id="([^"]+)"', definition)
    return match.group(1) if match else None


def render_ref_list(refs: list[str], indent: str = "\t\t") -> str:
    if not refs:
        return "NULL"
    return ", \n".join(f"{indent}{ref}" for ref in refs)


def render_path_refs(prefix: str, ids: list[str], indent: str = "\t\t") -> str:
    return render_ref_list([f"<{prefix}:{item}>" for item in ids], indent)


def render_simple_refs(ids: list[str], indent: str = "\t\t") -> str:
    return render_ref_list([f"<{item}>" for item in ids], indent)


def fetch_existing_ids(cursor: sqlite3.Cursor) -> set[str]:
    existing: set[str] = set()
    for table, column in (
        ("MODEL_ELEMENT", "ID"),
        ("DIAGRAM", "ID"),
        ("DIAGRAM_ELEMENT", "ID"),
        ("PROJECT_INFO", "ID"),
    ):
        existing.update(row[0] for row in cursor.execute(f"select {column} from {table}"))

    for table, column in (
        ("MODEL_ELEMENT", "DEFINITION"),
        ("DIAGRAM", "DEFINITION"),
        ("DIAGRAM_ELEMENT", "DEFINITION"),
        ("PROJECT_INFO", "DEFINITION"),
        ("PROJECT_INFO", "DIAGRAMS_DEFINITION"),
        ("PROJECT_INFO", "ROOT_MODEL_ELEMENTS_DEFINITION"),
    ):
        for (payload,) in cursor.execute(f"select {column} from {table}"):
            existing.update(TOKEN_RE.findall(blob_to_text(payload)))
    return existing


def render_root_model_definition(root_model_id: str, child_ids: list[str], created_at: int, modified_at: int) -> str:
    return (
        f'{root_model_id}:"{ROOT_MODEL_NAME}":Model {{\n'
        f'\tpmLastModified="{modified_at}";\n'
        f'\tpmAuthor="{AUTHOR}";\n'
        "\tChild=(\n"
        f"{render_path_refs(root_model_id, child_ids)}\n"
        "\t);\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\t_modelViews=NULL;\n"
        f"\tlastModifiedTime={modified_at};\n"
        "\t_modelEditable=T;\n"
        "}\n"
    )


def render_root_diagrams_definition(diagram_ids: list[str]) -> str:
    return (
        'rootDiagrams:"rootDiagrams":rootDiagrams {\n'
        "\tChild=(\n"
        f"{render_simple_refs(diagram_ids)}\n"
        "\t);\n"
        "}\n"
    )


def render_relationship_container_definition(
    relationship_container_id: str,
    container_id: str,
    container_name: str,
    child_ids: list[str],
    created_at: int,
    modified_at: int,
) -> str:
    return (
        f'{container_id}:"{container_name}":ModelRelationshipContainer {{\n'
        f'\tpmLastModified="{modified_at}";\n'
        f'\tpmAuthor="{AUTHOR}";\n'
        "\tChild=(\n"
        f"{render_path_refs(f'{relationship_container_id}:{container_id}', child_ids)}\n"
        "\t);\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\t_modelViews=NULL;\n"
        f"\tlastModifiedTime={modified_at};\n"
        "\t_modelEditable=T;\n"
        "}\n"
    )


def render_parent_activity_definition(
    root_model_id: str,
    parent_activity_id: str,
    parent_activity_name: str,
    child_ids: list[str],
    diagram_id: str,
    created_at: int,
    modified_at: int,
) -> str:
    return (
        f'{parent_activity_id}:"{quote(parent_activity_name)}":Activity {{\n'
        "\t_modelEditable=T;\n"
        f'\t_subDiagrams=(\n\t\t"{diagram_id}"\n\t);\n'
        f'\tpmAuthor="{AUTHOR}";\n'
        f"\tlastModifiedTime={modified_at};\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\t_modelViews=NULL;\n"
        "\tChild=(\n"
        f"{render_path_refs(f'{root_model_id}:{parent_activity_id}', child_ids)}\n"
        "\t);\n"
        f'\tpmLastModified="{modified_at}";\n'
        "}\n"
    )


def render_activity_model_definition(
    root_model_id: str,
    parent_activity_id: str,
    diagram_id: str,
    model_id: str,
    shape_id: str,
    view_ref_id: str,
    model_type: str,
    name: str,
    incoming_edges: list[str],
    outgoing_edges: list[str],
    created_at: int,
    modified_at: int,
) -> str:
    parts = [
        f'{model_id}:"{quote(name)}":{model_type} {{',
        "\t_modelEditable=T;",
        f'\t_masterViewId="{shape_id}";',
    ]

    if incoming_edges:
        parts.extend(
            [
                "\tToSimpleRelationships=(",
                render_path_refs("nrlBmOmGAqACBAnS:pt_RmOmGAqACBAw8", incoming_edges),
                "\t);",
            ]
        )

    parts.append(f'\tpmAuthor="{AUTHOR}";')

    if outgoing_edges:
        parts.extend(
            [
                "\tFromSimpleRelationships=(",
                render_path_refs("nrlBmOmGAqACBAnS:pt_RmOmGAqACBAw8", outgoing_edges),
                "\t);",
            ]
        )

    parts.extend(
        [
            f"\tlastModifiedTime={modified_at};",
            f'\tpmCreateDateTime="{created_at}";',
            "\t_modelViews=(",
            f'\t\t{{{view_ref_id}:"View":ModelView {{',
            f"\t\t\tcontainer=<{diagram_id}>;",
            f'\t\t\tview="{shape_id}";',
            "\t\t}}",
            "\t);",
            f'\tpmLastModified="{modified_at}";',
            "}",
            "",
        ]
    )
    return "\n".join(parts)


def render_activity_node_shape_definition(
    root_model_id: str,
    parent_activity_id: str,
    model_id: str,
    shape_id: str,
    shape_type: str,
    name: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    if shape_type == "DecisionNode":
        caption = (
            "\t_captionUIModel=(\n"
            f"\t\t@x={width + 12};, \n"
            "\t\t@y=7;, \n"
            "\t\t@width=190;, \n"
            "\t\t@height=20;, \n"
            "\t\t@side=1;, \n"
            "\t\t@visible=T;, \n"
            "\t\t@internalWidth=190;, \n"
            "\t\t@internalHeight=20;\n"
            "\t);"
        )
        connection_point = "\tconnectionPointType=1;\n\tcreatorDiagramType=\"ActivityDiagram\";"
    elif shape_type in {"InitialNode", "ActivityFinalNode"}:
        caption_width = max(70, len(name) * 8)
        caption = (
            "\t_captionUIModel=(\n"
            "\t\t@x=-24;, \n"
            "\t\t@y=22;, \n"
            f"\t\t@width={caption_width};, \n"
            "\t\t@height=15;, \n"
            "\t\t@side=1;, \n"
            "\t\t@visible=T;, \n"
            "\t\t@internalWidth=-2147483648;, \n"
            "\t\t@internalHeight=-2147483648;\n"
            "\t);"
        )
        connection_point = "\tconnectionPointType=1;\n\tcreatorDiagramType=\"ActivityDiagram\";"
    else:
        caption = (
            "\t_captionUIModel=(\n"
            "\t\t@x=0;, \n"
            "\t\t@y=0;, \n"
            f"\t\t@width={width};, \n"
            f"\t\t@height={height};, \n"
            "\t\t@side=6;, \n"
            "\t\t@visible=T;, \n"
            "\t\t@internalWidth=-2147483648;, \n"
            "\t\t@internalHeight=-2147483648;\n"
            "\t);"
        )
        connection_point = ""

    if shape_type in {"InitialNode", "ActivityFinalNode"}:
        color = "0, \n\t\t\t0, \n\t\t\t0, \n\t\t\t255"
    elif name in ACTIVITY_LANES:
        color = "214, \n\t\t\t231, \n\t\t\t245, \n\t\t\t255"
    elif "erro" in name.lower():
        color = "255, \n\t\t\t224, \n\t\t\t214, \n\t\t\t255"
    else:
        color = "122, \n\t\t\t207, \n\t\t\t245, \n\t\t\t255"

    return (
        f'{shape_id}:"{quote(name)}":{shape_type} {{\n'
        "\tparentConnectorHeaderLength=40;\n"
        "\t_fillColor=(\n"
        "\t\t@gradientStyle=1;, \n"
        "\t\t@transparency=0;, \n"
        "\t\t@type=1;, \n"
        "\t\t@color1=(\n"
        f"\t\t\t{color}\n"
        "\t\t);\n"
        "\t);\n"
        "\tbackground=(\n"
        "\t\t122, \n"
        "\t\t207, \n"
        "\t\t245, \n"
        "\t\t255\n"
        "\t);\n"
        f"\twidth={width};\n"
        f"{connection_point}\n"
        f"{caption}\n"
        "\t_elementFont=(\n"
        '\t\t@name="Dialog";, \n'
        "\t\t@color=(\n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t255\n"
        "\t\t);, \n"
        "\t\t@size=11;, \n"
        "\t\t@style=0;\n"
        "\t);\n"
        f"\tmetaModelElement=<{root_model_id}:{parent_activity_id}:{model_id}>;\n"
        "\tforeground=(\n"
        "\t\t0, \n"
        "\t\t0, \n"
        "\t\t0, \n"
        "\t\t255\n"
        "\t);\n"
        "\tconnectToPoint=T;\n"
        f"\ty={y};\n"
        "\toverrideAppearanceWithStereotypeIcon=T;\n"
        f"\tx={x};\n"
        "\t_lineModel=(\n"
        "\t\t@cap=0;, \n"
        "\t\t@transparency=0;, \n"
        "\t\t@weight=1.0;, \n"
        "\t\t@color=(\n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t255\n"
        "\t\t);, \n"
        "\t\t@hasStroke=T;\n"
        "\t);\n"
        f"\theight={height};\n"
        "\tparentConnectorLineLength=10;\n"
        "}\n"
    )


def render_controlflow_model_definition(
    root_model_id: str,
    parent_activity_id: str,
    diagram_id: str,
    edge_id: str,
    shape_id: str,
    view_ref_id: str,
    from_model_id: str,
    to_model_id: str,
    label: str | None,
    created_at: int,
    modified_at: int,
) -> str:
    return (
        f"{edge_id}:{name_literal(label)}:ControlFlow {{\n"
        "\t_modelEditable=T;\n"
        f"\ttoModel=<{root_model_id}:{parent_activity_id}:{to_model_id}>;\n"
        f'\t_masterViewId="{shape_id}";\n'
        f'\tpmAuthor="{AUTHOR}";\n'
        f"\tlastModifiedTime={modified_at};\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\t_modelViews=(\n"
        f'\t\t{{{view_ref_id}:"View":ModelView {{\n'
        f"\t\t\tcontainer=<{diagram_id}>;\n"
        f'\t\t\tview="{shape_id}";\n'
        "\t\t}}\n"
        "\t);\n"
        f"\tfromModel=<{root_model_id}:{parent_activity_id}:{from_model_id}>;\n"
        f'\tpmLastModified="{modified_at}";\n'
        "}\n"
    )


def compute_edge_geometry(
    source_x: int,
    source_y: int,
    source_width: int,
    source_height: int,
    target_x: int,
    target_y: int,
    target_width: int,
    target_height: int,
) -> tuple[str, int, int, int, int]:
    sx = source_x + source_width // 2
    sy = source_y + source_height // 2
    tx = target_x + target_width // 2
    ty = target_y + target_height // 2
    box_x = min(sx, tx) - 20
    box_y = min(sy, ty) - 20
    box_w = max(40, abs(tx - sx) + 40)
    box_h = max(40, abs(ty - sy) + 40)
    points = f"{sx - box_x},{sy - box_y};{tx - box_x},{ty - box_y};"
    return points, box_x, box_y, box_w, box_h


def render_controlflow_shape_definition(
    diagram_id: str,
    edge_id: str,
    shape_id: str,
    from_shape_id: str,
    to_shape_id: str,
    label: str | None,
    points: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    label_width = max(20, min(260, len(label or "") * 7 + 12))
    label_height = 15 if label else 0
    return (
        f"{shape_id}:{name_literal(label)}:ControlFlow {{\n"
        "\tforeground=(\n"
        "\t\t0, \n"
        "\t\t0, \n"
        "\t\t0, \n"
        "\t\t255\n"
        "\t);\n"
        "\tfromPinType=1;\n"
        f'\t_points="{points}";\n'
        "\ttoPinType=1;\n"
        "\tuseToShapeCenter=T;\n"
        '\tcreatorDiagramType="ActivityDiagram";\n'
        f"\t_fromShape=<{diagram_id}:{from_shape_id}>;\n"
        "\t_durationConstraintUIInfo=NULL;\n"
        "\tuseFromShapeCenter=T;\n"
        f"\ty={y};\n"
        f"\tx={x};\n"
        f"\tmetaModelElement=<nrlBmOmGAqACBAnS:pt_RmOmGAqACBAw8:{edge_id}>;\n"
        f"\theight={height};\n"
        f"\twidth={width};\n"
        "\tbackground=(\n"
        "\t\t122, \n"
        "\t\t207, \n"
        "\t\t245, \n"
        "\t\t255\n"
        "\t);\n"
        "\t_elementFont=(\n"
        '\t\t@name="Dialog";, \n'
        "\t\t@color=(\n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t255\n"
        "\t\t);, \n"
        "\t\t@size=11;, \n"
        "\t\t@style=0;\n"
        "\t);\n"
        "\t_captionUIModel=(\n"
        "\t\t@x=1;, \n"
        "\t\t@y=21;, \n"
        f"\t\t@width={label_width};, \n"
        f"\t\t@height={label_height};, \n"
        "\t\t@side=1;, \n"
        "\t\t@visible=T;, \n"
        "\t\t@internalWidth=-2147483648;, \n"
        "\t\t@internalHeight=-2147483648;\n"
        "\t);\n"
        f"\t_toShape=<{diagram_id}:{to_shape_id}>;\n"
        "\t_lineModel=(\n"
        "\t\t@cap=0;, \n"
        "\t\t@transparency=0;, \n"
        "\t\t@weight=1.0;, \n"
        "\t\t@color=(\n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t0, \n"
        "\t\t\t255\n"
        "\t\t);, \n"
        "\t\t@hasStroke=T;\n"
        "\t);\n"
        "}\n"
    )


def render_activity_diagram_definition(
    root_model_id: str,
    parent_activity_id: str,
    diagram_name: str,
    diagram_id: str,
    preview_id: str,
    shape_ids: list[str],
    created_at: int,
    modified_at: int,
) -> str:
    quoted_ids = ", \n".join(f'\t\t"{shape_id}"' for shape_id in shape_ids)
    child_refs = ", \n".join(f"\t\t<{diagram_id}:{shape_id}>" for shape_id in shape_ids)
    return (
        f'{diagram_id}:"{quote(diagram_name)}":ActivityDiagram {{\n'
        "\tpaintConnectorThroughLabel=1;\n"
        "\t_shapeGroups=NULL;\n"
        "\tdiagramBackground=(\n\t\t255, \n\t\t255, \n\t\t255, \n\t\t255\n\t);\n"
        "\tconnectorLabelOrientation=0;\n"
        "\tshowPackageNameStyle=0;\n"
        "\tshowPartitionHeader=1;\n"
        "\tshowDefaultPackage=F;\n"
        "\tpointConnectorEndToCompartmentMember=T;\n"
        "\t_scenarios=NULL;\n"
        "\tobjectNodeShowInStates=2;\n"
        "\tautoFitShapesSize=F;\n"
        "\tshowDiagramFrame=T;\n"
        "\tconnectorStyle=1;\n"
        "\tdiagramPreviewData_name=NULL;\n"
        "\tshowActionCallBehaviorOption=1;\n"
        "\t_globalPaletteOption=T;\n"
        "\tconnectionPointStyle=0;\n"
        "\tgridWidth=10;\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\tcustomizedSortDiagramElementIds=(\n"
        f"{quoted_ids}\n"
        "\t);\n"
        "\talignToGrid=F;\n"
        f"\tparentModel=<{root_model_id}:{parent_activity_id}>;\n"
        f'\tdiagramPreviewData_id="{preview_id}";\n'
        f'\tpmLastModified="{modified_at}";\n'
        "\thiddenDiagramElementIds=NULL;\n"
        "\tgridVisible=F;\n"
        f"\tcreationTime={created_at};\n"
        "\tobjectNodeShowType=T;\n"
        "\tzoomRatio=0.7;\n"
        f'\tpmAuthor="{AUTHOR}";\n'
        f"\tlastModified={modified_at};\n"
        "\tconnectorLineJumpsSize=0;\n"
        "\tshowStereotypes=T;\n"
        "\tdecisionMergeNodeConnectionPointStyle=1;\n"
        "\tshowActivityEdgeWeight=T;\n"
        "\tshapePresentationOption=0;\n"
        "\tconnectorModelElementNameAlignment=4;\n"
        "\tvoiceIds=NULL;\n"
        "\tcontrolFlowDisplayOption=0;\n"
        "\tinitializeDiagramForCreate=T;\n"
        "\treferenceMappingReferencedElementIds=NULL;\n"
        "\tChild=(\n"
        f"{child_refs}\n"
        "\t);\n"
        "\treferenceMappingElementIds=NULL;\n"
        "\tmodelElementNameAlignment=4;\n"
        "\tshowActivityStateNodeCaption=524287;\n"
        "\tconnectorLineJumps=0;\n"
        "\tgridHeight=10;\n"
        "\tgridColor=(\n\t\t192, \n\t\t192, \n\t\t192, \n\t\t255\n\t);\n"
        "\tshowModelElementIdModelTypes=NULL;\n"
        "}\n"
    )


def model_address(root_model_id: str, block_ids: dict[str, str], specs: dict[str, BlockSpec], key: str) -> str:
    chain = [block_ids[key]]
    parent_key = specs[key].parent_key
    while parent_key:
        chain.append(block_ids[parent_key])
        parent_key = specs[parent_key].parent_key
    return ":".join([root_model_id, *reversed(chain)])


def render_sysml_block_definition(
    root_model_id: str,
    diagram_id: str,
    block_stereotype_id: str,
    block_id: str,
    shape_id: str,
    view_ref_id: str,
    address: str,
    name: str,
    child_refs: list[str],
    from_assoc_refs: list[str],
    to_assoc_refs: list[str],
    created_at: int,
    modified_at: int,
) -> str:
    parts = [
        f'{block_id}:"{quote(name)}":SysMLBlock {{',
        "\tstereotypes=(",
        f"\t\t<{block_stereotype_id}>",
        "\t);",
        "\t_modelEditable=T;",
        f'\t_masterViewId="{shape_id}";',
        f'\tpmAuthor="{AUTHOR}";',
    ]
    if from_assoc_refs:
        parts.extend(["\tFromEndRelationships=(", render_ref_list(from_assoc_refs), "\t);"])
    if to_assoc_refs:
        parts.extend(["\tToEndRelationships=(", render_ref_list(to_assoc_refs), "\t);"])
    parts.extend(
        [
            f"\tlastModifiedTime={modified_at};",
            f'\tpmCreateDateTime="{created_at}";',
            "\t_modelViews=(",
            f'\t\t{{{view_ref_id}:"View":ModelView {{',
            f"\t\t\tcontainer=<{diagram_id}>;",
            f'\t\t\tview="{shape_id}";',
            "\t\t}}",
            "\t);",
        ]
    )
    if child_refs:
        parts.extend(["\tChild=(", render_path_refs(address, child_refs), "\t);"])
    parts.extend([f'\tpmLastModified="{modified_at}";', "}", ""])
    return "\n".join(parts)


def render_block_shape_definition(
    diagram_id: str,
    shape_id: str,
    model_address_value: str,
    name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    parent_shape_id: str | None,
    contained_shape_ids: list[str],
) -> str:
    contained = ""
    if contained_shape_ids:
        contained = (
            "\tContainedDiagramElements=(\n"
            + render_path_refs(diagram_id, contained_shape_ids)
            + "\n\t);\n"
        )
    parent = f"\t_parent=<{diagram_id}:{parent_shape_id}>;\n" if parent_shape_id else ""
    return (
        f'{shape_id}:"{quote(name)}":SysMLBlock {{\n'
        "\tparentConnectorHeaderLength=40;\n"
        "\t_fillColor=(\n"
        "\t\t@gradientStyle=1;, \n"
        "\t\t@transparency=0;, \n"
        "\t\t@type=1;, \n"
        "\t\t@color1=(\n"
        "\t\t\t122, \n"
        "\t\t\t207, \n"
        "\t\t\t245, \n"
        "\t\t\t255\n"
        "\t\t);\n"
        "\t);\n"
        "\tbackground=(\n\t\t122, \n\t\t207, \n\t\t245, \n\t\t255\n\t);\n"
        f"\twidth={width};\n"
        "\t_captionUIModel=(\n"
        "\t\t@x=0;, \n"
        "\t\t@y=0;, \n"
        f"\t\t@width={width};, \n"
        "\t\t@height=30;, \n"
        "\t\t@side=8;, \n"
        "\t\t@visible=T;, \n"
        "\t\t@internalWidth=-2147483648;, \n"
        "\t\t@internalHeight=-2147483648;\n"
        "\t);\n"
        f"{parent}"
        "\t_elementFont=(\n"
        '\t\t@name="Dialog";, \n'
        "\t\t@color=(\n\t\t\t0, \n\t\t\t0, \n\t\t\t0, \n\t\t\t255\n\t\t);, \n"
        "\t\t@size=11;, \n"
        "\t\t@style=0;\n"
        "\t);\n"
        f"{contained}"
        f"\tmetaModelElement=<{model_address_value}>;\n"
        "\tforeground=(\n\t\t0, \n\t\t0, \n\t\t0, \n\t\t255\n\t);\n"
        "\tconnectToPoint=T;\n"
        f"\ty={y};\n"
        "\toverrideAppearanceWithStereotypeIcon=T;\n"
        f"\tx={x};\n"
        "\t_lineModel=(\n"
        "\t\t@cap=0;, \n"
        "\t\t@transparency=0;, \n"
        "\t\t@weight=1.0;, \n"
        "\t\t@color=(\n\t\t\t0, \n\t\t\t0, \n\t\t\t0, \n\t\t\t255\n\t\t);, \n"
        "\t\t@hasStroke=T;\n"
        "\t);\n"
        f"\theight={height};\n"
        "\tparentConnectorLineLength=10;\n"
        "}\n"
    )


def render_association_model_definition(
    relationship_container_id: str,
    association_container_id: str,
    diagram_id: str,
    association_id: str,
    shape_id: str,
    view_ref_id: str,
    label: str,
    from_address: str,
    to_address: str,
    from_end_id: str,
    from_qualifier_id: str,
    to_end_id: str,
    to_qualifier_id: str,
    created_at: int,
    modified_at: int,
) -> str:
    return (
        f"{association_id}:{name_literal(label)}:Association {{\n"
        "\t_modelEditable=T;\n"
        f'\t_masterViewId="{shape_id}";\n'
        f'\tpmAuthor="{AUTHOR}";\n'
        f"\tlastModifiedTime={modified_at};\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\t_modelViews=(\n"
        f'\t\t{{{view_ref_id}:"View":ModelView {{\n'
        f"\t\t\tcontainer=<{diagram_id}>;\n"
        f'\t\t\tview="{shape_id}";\n'
        "\t\t}}\n"
        "\t);\n"
        f"\tfrom={{{from_end_id}:NULL:AssociationEnd {{\n"
        "\t\tvisibility=65;\n"
        "\t\t_modelEditable=T;\n"
        f'\t\tpmAuthor="{AUTHOR}";\n'
        "\t\tnavigable=1;\n"
        f"\t\tlastModifiedTime={modified_at};\n"
        f'\t\tpmCreateDateTime="{created_at}";\n'
        "\t\t_modelViews=NULL;\n"
        f'\t\tqualifier={{{from_qualifier_id}:"":Qualifier {{\n'
        f'\t\t\tpmAuthor="{AUTHOR}";\n'
        f'\t\t\tpmCreateDateTime="{created_at}";\n'
        "\t\t\t_modelViews=NULL;\n"
        f"\t\t\tlastModifiedTime={modified_at};\n"
        "\t\t\t_modelEditable=T;\n"
        "\t\t}};\n"
        "\t\taggregationKind=67;\n"
        f"\t\ttype=<{from_address}>;\n"
        f"\t\tEndModelElement=<{from_address}>;\n"
        "\t\tDirection=0;\n"
        "\t}};\n"
        f"\tto={{{to_end_id}:NULL:AssociationEnd {{\n"
        "\t\tvisibility=65;\n"
        "\t\t_modelEditable=T;\n"
        f'\t\tpmAuthor="{AUTHOR}";\n'
        f"\t\tlastModifiedTime={modified_at};\n"
        f'\t\tpmCreateDateTime="{created_at}";\n'
        "\t\t_modelViews=NULL;\n"
        f'\t\tqualifier={{{to_qualifier_id}:"":Qualifier {{\n'
        f'\t\t\tpmAuthor="{AUTHOR}";\n'
        f'\t\t\tpmCreateDateTime="{created_at}";\n'
        "\t\t\t_modelViews=NULL;\n"
        f"\t\t\tlastModifiedTime={modified_at};\n"
        "\t\t\t_modelEditable=T;\n"
        "\t\t}};\n"
        f"\t\ttype=<{to_address}>;\n"
        f"\t\tEndModelElement=<{to_address}>;\n"
        "\t\tDirection=1;\n"
        "\t}};\n"
        f'\tpmLastModified="{modified_at}";\n'
        "}\n"
    )


def render_association_shape_definition(
    relationship_container_id: str,
    association_container_id: str,
    diagram_id: str,
    association_id: str,
    shape_id: str,
    from_shape_id: str,
    to_shape_id: str,
    label: str,
    points: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    label_width = max(20, min(260, len(label) * 7 + 12))
    return (
        f"{shape_id}:{name_literal(label)}:Association {{\n"
        "\tforeground=(\n\t\t0, \n\t\t0, \n\t\t0, \n\t\t255\n\t);\n"
        "\tfromPinType=1;\n"
        f'\t_points="{points}";\n'
        "\tshowUniqueMultiplicityConstraint=T;\n"
        "\tshowStereotypes=T;\n"
        "\ttoPinType=1;\n"
        "\tshowToRoleName=T;\n"
        "\tuseToShapeCenter=T;\n"
        "\tshowFromRoleVisibility=T;\n"
        f"\t_fromShape=<{diagram_id}:{from_shape_id}>;\n"
        "\tshowOrderedMultiplicityConstraint=T;\n"
        "\tuseFromShapeCenter=T;\n"
        f"\ty={y};\n"
        f"\tx={x};\n"
        f"\tmetaModelElement=<{relationship_container_id}:{association_container_id}:{association_id}>;\n"
        "\tshowToRoleVisibility=T;\n"
        "\tshowToMultiplicity=T;\n"
        "\tshowFromRoleName=T;\n"
        "\t0SwDr=F;\n"
        f"\theight={height};\n"
        f"\twidth={width};\n"
        "\tbackground=(\n\t\t122, \n\t\t207, \n\t\t245, \n\t\t255\n\t);\n"
        "\t_elementFont=(\n"
        '\t\t@name="Dialog";, \n'
        "\t\t@color=(\n\t\t\t0, \n\t\t\t0, \n\t\t\t0, \n\t\t\t255\n\t\t);, \n"
        "\t\t@size=11;, \n"
        "\t\t@style=0;\n"
        "\t);\n"
        "\t_captionUIModel=(\n"
        "\t\t@x=1;, \n"
        "\t\t@y=21;, \n"
        f"\t\t@width={label_width};, \n"
        "\t\t@height=15;, \n"
        "\t\t@side=1;, \n"
        "\t\t@visible=T;, \n"
        "\t\t@internalWidth=-2147483648;, \n"
        "\t\t@internalHeight=-2147483648;\n"
        "\t);\n"
        f"\t_toShape=<{diagram_id}:{to_shape_id}>;\n"
        "\t_lineModel=(\n"
        "\t\t@cap=0;, \n"
        "\t\t@transparency=0;, \n"
        "\t\t@weight=1.0;, \n"
        "\t\t@color=(\n\t\t\t0, \n\t\t\t0, \n\t\t\t0, \n\t\t\t255\n\t\t);, \n"
        "\t\t@hasStroke=T;\n"
        "\t);\n"
        "\tshowFromMultiplicity=T;\n"
        "\tshowMultiplicityConstraints=F;\n"
        "}\n"
    )


def render_block_diagram_definition(
    root_model_id: str,
    parent_model_id: str,
    diagram_name: str,
    diagram_id: str,
    preview_id: str,
    shape_ids: list[str],
    created_at: int,
    modified_at: int,
) -> str:
    quoted_ids = ", \n".join(f'\t\t"{shape_id}"' for shape_id in shape_ids)
    child_refs = ", \n".join(f"\t\t<{diagram_id}:{shape_id}>" for shape_id in shape_ids)
    return (
        f'{diagram_id}:"{quote(diagram_name)}":BlockDefinitionDiagram {{\n'
        "\tpaintConnectorThroughLabel=1;\n"
        "\t_shapeGroups=NULL;\n"
        "\tdiagramBackground=(\n\t\t255, \n\t\t255, \n\t\t255, \n\t\t255\n\t);\n"
        "\tconnectorLabelOrientation=0;\n"
        "\tshowLinkRoleNames=2;\n"
        "\tshowPackageNameStyle=0;\n"
        "\tshowDefaultPackage=F;\n"
        "\tpointConnectorEndToCompartmentMember=T;\n"
        "\tautoFitShapesSize=F;\n"
        "\tshowDiagramFrame=T;\n"
        "\tconnectorStyle=1;\n"
        "\tdiagramPreviewData_name=NULL;\n"
        "\t_globalPaletteOption=T;\n"
        "\tconnectionPointStyle=0;\n"
        "\tgridWidth=10;\n"
        f'\tpmCreateDateTime="{created_at}";\n'
        "\tcustomizedSortDiagramElementIds=(\n"
        f"{quoted_ids}\n"
        "\t);\n"
        "\talignToGrid=F;\n"
        f"\tparentModel=<{root_model_id}:{parent_model_id}>;\n"
        f'\tdiagramPreviewData_id="{preview_id}";\n'
        f'\tpmLastModified="{modified_at}";\n'
        "\thiddenDiagramElementIds=NULL;\n"
        "\tgridVisible=F;\n"
        f"\tcreationTime={created_at};\n"
        "\tshowPortMultiplicityOption=3;\n"
        "\tzoomRatio=0.8;\n"
        f'\tpmAuthor="{AUTHOR}";\n'
        f"\tlastModified={modified_at};\n"
        "\tconnectorLineJumpsSize=0;\n"
        "\tshowStereotypes=T;\n"
        "\tshapePresentationOption=0;\n"
        "\tconnectorModelElementNameAlignment=4;\n"
        "\tvoiceIds=NULL;\n"
        "\tinitializeDiagramForCreate=T;\n"
        "\treferenceMappingReferencedElementIds=NULL;\n"
        "\tChild=(\n"
        f"{child_refs}\n"
        "\t);\n"
        "\treferenceMappingElementIds=NULL;\n"
        "\tmodelElementNameAlignment=4;\n"
        "\tshowActivityStateNodeCaption=524287;\n"
        "\tconnectorLineJumps=0;\n"
        "\tshowLinkNavigability=2;\n"
        "\tgridHeight=10;\n"
        "\tgridColor=(\n\t\t192, \n\t\t192, \n\t\t192, \n\t\t255\n\t);\n"
        "\tshowModelElementIdModelTypes=NULL;\n"
        "}\n"
    )


def make_png(width: int = 360, height: int = 220) -> bytes:
    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    background = bytes((255, 255, 255, 255))
    stripe = bytes((220, 235, 246, 255))
    rows = []
    for row_index in range(height):
        pixel = stripe if row_index < 40 else background
        rows.append(b"\x00" + pixel * width)
    raw = b"".join(rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def select_template_details(cursor: sqlite3.Cursor, diagram_type: str) -> bytes:
    row = cursor.execute(
        """
        select pf.CONTENT
        from DIAGRAM d
        join PROJECT_FILE pf on pf.PATH = 'vpdiagramshapes/' || d.ID || '.vps/details.xml'
        where d.DIAGRAM_TYPE = ?
        order by d.rowid
        limit 1
        """,
        (diagram_type,),
    ).fetchone()
    if row:
        return row[0]
    row = cursor.execute(
        "select CONTENT from PROJECT_FILE where PATH like ? order by PATH limit 1",
        ("vpdiagramshapes/%.vps/details.xml",),
    ).fetchone()
    if not row:
        raise RuntimeError("No details.xml template found in PROJECT_FILE")
    return row[0]


def upsert_project_file(cursor: sqlite3.Cursor, path: str, content: bytes) -> None:
    cursor.execute(
        """
        insert into PROJECT_FILE(PATH, CONTENT, STATUS)
        values (?, ?, 'c')
        on conflict(PATH) do update set CONTENT=excluded.CONTENT, STATUS='c'
        """,
        (path, content),
    )


def collect_descendant_ids(cursor: sqlite3.Cursor, parent_id: str) -> list[str]:
    descendants: list[str] = []
    pending = [parent_id]
    while pending:
        current = pending.pop()
        children = [row[0] for row in cursor.execute("select ID from MODEL_ELEMENT where PARENT_ID=?", (current,))]
        descendants.extend(children)
        pending.extend(children)
    return descendants


def ids_for_relationships_in_diagram(cursor: sqlite3.Cursor, model_type: str, diagram_id: str) -> list[str]:
    marker = f"container=<{diagram_id}>"
    return [
        row[0]
        for row in cursor.execute("select ID, DEFINITION from MODEL_ELEMENT where MODEL_TYPE=?", (model_type,))
        if marker in blob_to_text(row[1])
    ]


def find_or_create_model(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    model_type: str,
    name: str,
    parent_id: str,
) -> str:
    row = cursor.execute(
        "select ID from MODEL_ELEMENT where MODEL_TYPE=? and NAME=? and PARENT_ID=?",
        (model_type, name, parent_id),
    ).fetchone()
    if row:
        existing_ids.add(row[0])
        return row[0]
    return generate_id(existing_ids)


def find_or_create_diagram(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    name: str,
    diagram_type: str,
) -> tuple[str, str]:
    row = cursor.execute(
        "select ID, DEFINITION from DIAGRAM where NAME=? and DIAGRAM_TYPE=?",
        (name, diagram_type),
    ).fetchone()
    if row:
        diagram_id = row[0]
        existing_ids.add(diagram_id)
        preview_id = extract_preview_id(blob_to_text(row[1])) or generate_id(existing_ids)
        return diagram_id, preview_id
    return generate_id(existing_ids), generate_id(existing_ids)


def lane_x(index: int) -> int:
    return 40 + index * 245


def build_activity_specs() -> tuple[list[ActivityNodeSpec], list[EdgeSpec]]:
    nodes: list[ActivityNodeSpec] = []
    for index, lane in enumerate(ACTIVITY_LANES):
        nodes.append(ActivityNodeSpec(f"lane_{index}", "ActivityAction", lane, lane_x(index), 30, 220, 55))

    nodes.extend(
        [
            ActivityNodeSpec("start", "InitialNode", "Início da compilação", lane_x(0) + 100, 130, 20, 20),
            ActivityNodeSpec("receive", "ActivityAction", "Receber código-fonte C-", lane_x(0) + 10, 190, 210, 55),
            ActivityNodeSpec("lex", "ActivityAction", "Realizar análise léxica", lane_x(1) + 10, 285, 210, 55),
            ActivityNodeSpec("tokens_ok", "DecisionNode", "Tokens válidos?", lane_x(1) + 100, 370, 20, 40),
            ActivityNodeSpec("lex_error", "ActivityAction", "Gerar relatório de erro léxico", lane_x(1) + 10, 455, 210, 55),
            ActivityNodeSpec("parse", "ActivityAction", "Realizar análise sintática", lane_x(2) + 10, 455, 210, 55),
            ActivityNodeSpec("syntax_ok", "DecisionNode", "Sintaxe válida?", lane_x(2) + 100, 540, 20, 40),
            ActivityNodeSpec("syntax_error", "ActivityAction", "Gerar relatório de erro sintático", lane_x(2) + 10, 625, 210, 55),
            ActivityNodeSpec("semantic", "ActivityAction", "Realizar análise semântica", lane_x(3) + 10, 625, 210, 55),
            ActivityNodeSpec("symbols_semantic", "ActivityAction", "Consultar/atualizar tabela de símbolos", lane_x(4) + 10, 710, 210, 55),
            ActivityNodeSpec("semantic_ok", "DecisionNode", "Semântica válida?", lane_x(3) + 100, 795, 20, 40),
            ActivityNodeSpec("semantic_error", "ActivityAction", "Gerar relatório de erro semântico", lane_x(3) + 10, 880, 210, 55),
            ActivityNodeSpec("symbols_ir", "ActivityAction", "Consultar tabela para geração de IR", lane_x(4) + 10, 880, 210, 55),
            ActivityNodeSpec("ir", "ActivityAction", "Gerar código intermediário", lane_x(5) + 10, 965, 210, 55),
            ActivityNodeSpec("symbols_alloc", "ActivityAction", "Consultar tabela para alocação", lane_x(4) + 10, 1050, 210, 55),
            ActivityNodeSpec("alloc", "ActivityAction", "Mapear variáveis e temporários para registradores", lane_x(6) + 10, 1135, 210, 70),
            ActivityNodeSpec("asm", "ActivityAction", "Gerar assembly ARM simplificado", lane_x(7) + 10, 1235, 210, 55),
            ActivityNodeSpec("labels", "ActivityAction", "Resolver rótulos e desvios", lane_x(8) + 10, 1320, 210, 55),
            ActivityNodeSpec(
                "encode",
                "ActivityAction",
                "Codificar instruções em binário de 32 bits - Cond[31:28], Type[27:26], Supp[25:24], Funct[23:20], Rd[19:15], Rh[14:10], Operand2[9:0]",
                lane_x(9) + 5,
                1405,
                230,
                85,
            ),
            ActivityNodeSpec("validate", "ActivityAction", "Validar instruções binárias", lane_x(10) + 10, 1515, 210, 55),
            ActivityNodeSpec("binary_ok", "DecisionNode", "Binário válido?", lane_x(10) + 100, 1600, 20, 40),
            ActivityNodeSpec("coding_error", "ActivityAction", "Gerar relatório de erro de codificação", lane_x(10) + 10, 1685, 210, 55),
            ActivityNodeSpec("file", "ActivityAction", "Gerar arquivo de código de máquina", lane_x(10) + 10, 1770, 210, 55),
            ActivityNodeSpec("error_report", "ActivityAction", "Gerar relatório de erro", lane_x(10) + 10, 1855, 210, 55),
            ActivityNodeSpec("final", "ActivityFinalNode", "Fim da compilação", lane_x(10) + 100, 1970, 20, 20),
        ]
    )

    edges = [
        EdgeSpec("a01", "start", "receive"),
        EdgeSpec("a02", "receive", "lex", "Código C- / texto bruto do programa"),
        EdgeSpec("a03", "lex", "tokens_ok", "Lista de tokens"),
        EdgeSpec("a04", "tokens_ok", "parse", "sim: lista de tokens"),
        EdgeSpec("a05", "tokens_ok", "lex_error", "não"),
        EdgeSpec("a06", "lex_error", "error_report", "Erro léxico"),
        EdgeSpec("a07", "parse", "syntax_ok", "Árvore sintática"),
        EdgeSpec("a08", "syntax_ok", "semantic", "sim: árvore sintática"),
        EdgeSpec("a09", "syntax_ok", "syntax_error", "não"),
        EdgeSpec("a10", "syntax_error", "error_report", "Erro sintático"),
        EdgeSpec("a11", "semantic", "symbols_semantic", "consulta e atualização de símbolos"),
        EdgeSpec("a12", "symbols_semantic", "semantic_ok", "Tabela de símbolos"),
        EdgeSpec("a13", "semantic_ok", "symbols_ir", "sim: árvore validada"),
        EdgeSpec("a14", "semantic_ok", "semantic_error", "não"),
        EdgeSpec("a15", "semantic_error", "error_report", "Erro semântico"),
        EdgeSpec("a16", "symbols_ir", "ir", "Árvore validada + tabela de símbolos"),
        EdgeSpec("a17", "ir", "symbols_alloc", "Código intermediário"),
        EdgeSpec("a18", "symbols_alloc", "alloc", "temporários e símbolos"),
        EdgeSpec("a19", "alloc", "asm", "Código intermediário com registradores definidos"),
        EdgeSpec("a20", "asm", "labels", "Assembly ARM simplificado"),
        EdgeSpec("a21", "labels", "encode", "Assembly com rótulos resolvidos"),
        EdgeSpec("a22", "encode", "validate", "Instruções binárias de 32 bits"),
        EdgeSpec("a23", "validate", "binary_ok", "Código binário validado"),
        EdgeSpec("a24", "binary_ok", "file", "sim: código binário validado"),
        EdgeSpec("a25", "binary_ok", "coding_error", "não"),
        EdgeSpec("a26", "coding_error", "error_report", "Erro de codificação"),
        EdgeSpec("a27", "file", "final", "Arquivo final .txt"),
        EdgeSpec("a28", "error_report", "final"),
    ]
    return nodes, edges


def build_block_specs() -> tuple[list[BlockSpec], list[AssociationSpec]]:
    blocks = [
        BlockSpec("compiler", MAIN_BLOCK_NAME, 40, 70, 2260, 1360),
        BlockSpec("manager", "Gerenciador de Compilação", 80, 120, 260, 100, "compiler"),
        BlockSpec("lexer", "Analisador Léxico", 390, 120, 240, 100, "compiler"),
        BlockSpec("parser", "Analisador Sintático", 680, 120, 240, 100, "compiler"),
        BlockSpec("semantic", "Analisador Semântico", 970, 120, 250, 100, "compiler"),
        BlockSpec("symbols", "Tabela de Símbolos", 1270, 105, 310, 130, "compiler"),
        BlockSpec("ir", "Gerador de Código Intermediário", 80, 360, 310, 110, "compiler"),
        BlockSpec("allocator", "Alocador de Registradores", 440, 360, 300, 110, "compiler"),
        BlockSpec("assembly", "Gerador de Assembly ARM Simplificado", 790, 360, 330, 110, "compiler"),
        BlockSpec("labels", "Resolvedor de Rótulos", 1170, 360, 280, 110, "compiler"),
        BlockSpec(
            "binary",
            "Codificador Binário - recebe assemblyResolvido; gera instrucoesBinarias; formato Cond[31:28], Type[27:26], Supp[25:24], Funct[23:20], Rd[19:15], Rh[14:10], Operand2[9:0]",
            80,
            650,
            1270,
            650,
            "compiler",
        ),
        BlockSpec(
            "cond",
            "CondEncoder - Cond[31:28]: do/sem condição=0000, eq=0001, neq=0010, gt=0011, gteq=0100, lt=0101, lteq=0110",
            110,
            735,
            580,
            70,
            "binary",
        ),
        BlockSpec(
            "type",
            "TypeEncoder - Type[27:26]: 00 processamento de dados, 01 load/store, 11 branch",
            720,
            735,
            580,
            70,
            "binary",
        ),
        BlockSpec(
            "supp",
            "SuppEncoder - Supp[25:24]: 00 normal, 10 imediato, 01 atualiza CPSR, 11 imediato e CPSR",
            110,
            835,
            580,
            70,
            "binary",
        ),
        BlockSpec(
            "funct",
            "FunctEncoder - Funct[23:20]: add=0000, sub=0001, mul=0010, div=0011, and=0100, or=0101, xor=0110, not=0111, mov=1000",
            720,
            835,
            580,
            85,
            "binary",
        ),
        BlockSpec(
            "register",
            "RegisterEncoder - Rd[19:15] e Rh[14:10]: r0=00000, r1=00001, r2=00010, r31=11111",
            110,
            950,
            580,
            70,
            "binary",
        ),
        BlockSpec(
            "operand2",
            "Operand2Encoder - Operand2[9:0]: imediato de 10 bits com sinal ou Ro em [9:5] e [4:0]=00000",
            720,
            950,
            580,
            70,
            "binary",
        ),
        BlockSpec("validator", "Validador de Código Binário", 1450, 850, 330, 120, "compiler"),
        BlockSpec("file", "Gerador de Arquivo de Saída", 1880, 850, 330, 120, "compiler"),
    ]

    associations = [
        AssociationSpec("b01", "manager", "lexer", "codigoFonte"),
        AssociationSpec("b02", "lexer", "parser", "listaTokens"),
        AssociationSpec("b03", "parser", "semantic", "arvoreSintatica"),
        AssociationSpec("b04", "semantic", "symbols", "declarações, tipos, escopos, chamadas, temporários e registradores"),
        AssociationSpec("b05", "semantic", "ir", "arvoreValidada"),
        AssociationSpec("b06", "symbols", "ir", "tabelaSimbolos"),
        AssociationSpec("b07", "ir", "allocator", "codigoIntermediario"),
        AssociationSpec("b08", "symbols", "allocator", "tabelaSimbolos com estado de uso"),
        AssociationSpec("b09", "allocator", "assembly", "codigoRegistrado"),
        AssociationSpec(
            "b10",
            "assembly",
            "labels",
            "codigoAssembly com mov, add, sub, subs, mul, div, and, or, xor, not, load, store, b, bl, bgt, blt, beq e bneq",
        ),
        AssociationSpec("b11", "labels", "binary", "assemblyResolvido"),
        AssociationSpec("b12", "binary", "validator", "instrucoesBinarias"),
        AssociationSpec("b13", "validator", "file", "codigoBinarioValidado"),
        AssociationSpec("b14", "file", "manager", "single_port_rom_init.txt ou arquivoBinario .txt"),
        AssociationSpec("b15", "lexer", "manager", "erroLexico"),
        AssociationSpec("b16", "parser", "manager", "erroSintatico"),
        AssociationSpec("b17", "semantic", "manager", "erroSemantico"),
        AssociationSpec("b18", "validator", "manager", "erroCodificacao"),
    ]
    return blocks, associations


def update_project_diagram_refs(cursor: sqlite3.Cursor, diagram_ids: list[str]) -> None:
    project_info_id, diagrams_definition = find_one(cursor, "select ID, DIAGRAMS_DEFINITION from PROJECT_INFO limit 1")
    cursor.execute(
        "update PROJECT_INFO set DIAGRAMS_DEFINITION=? where ID=?",
        (render_root_diagrams_definition(diagram_ids), project_info_id),
    )


def cleanup_legacy_content(
    cursor: sqlite3.Cursor,
    root_model_id: str,
    root_child_ids: list[str],
    controlflow_child_ids: list[str],
    association_child_ids: list[str],
) -> tuple[list[str], list[str]]:
    removed_diagram_names: list[str] = []
    removed_model_names: list[str] = []

    diagrams_to_delete = [
        (diagram_id, name, blob_to_text(definition))
        for diagram_id, name, definition in cursor.execute(
            "select ID, NAME, DEFINITION from DIAGRAM where NAME not in ({})".format(
                ",".join("?" for _ in CURRENT_DIAGRAM_NAMES)
            ),
            tuple(CURRENT_DIAGRAM_NAMES),
        )
    ]

    removed_controlflow_ids: list[str] = []
    removed_association_ids: list[str] = []
    for diagram_id, name, definition in diagrams_to_delete:
        removed_diagram_names.append(name)
        removed_controlflow_ids.extend(ids_for_relationships_in_diagram(cursor, "ControlFlow", diagram_id))
        removed_association_ids.extend(ids_for_relationships_in_diagram(cursor, "Association", diagram_id))
        preview_id = extract_preview_id(definition)
        cursor.execute("delete from DIAGRAM_ELEMENT where DIAGRAM_ID=?", (diagram_id,))
        cursor.execute("delete from DIAGRAM where ID=?", (diagram_id,))
        cursor.execute("delete from PROJECT_FILE where PATH=?", (f"vpdiagramshapes/{diagram_id}.vps/details.xml",))
        if preview_id:
            cursor.execute("delete from PROJECT_FILE where PATH=?", (f"diagramPreviewData/{preview_id}",))

    if removed_controlflow_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in removed_controlflow_ids))
        controlflow_child_ids[:] = [item for item in controlflow_child_ids if item not in removed_controlflow_ids]
    if removed_association_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in removed_association_ids))
        association_child_ids[:] = [item for item in association_child_ids if item not in removed_association_ids]

    legacy_roots = [
        (model_id, name)
        for model_id, name in cursor.execute(
            """
            select ID, NAME
            from MODEL_ELEMENT
            where PARENT_ID=? and MODEL_TYPE in ('Model', 'Activity', 'SysMLBlock') and NAME not in ({})
            """.format(",".join("?" for _ in CURRENT_ROOT_MODEL_NAMES)),
            (root_model_id, *CURRENT_ROOT_MODEL_NAMES),
        )
    ]
    ids_to_delete: list[str] = []
    for model_id, name in legacy_roots:
        removed_model_names.append(name)
        ids_to_delete.append(model_id)
        ids_to_delete.extend(collect_descendant_ids(cursor, model_id))
    if ids_to_delete:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in ids_to_delete))
        root_child_ids[:] = [item for item in root_child_ids if item not in ids_to_delete]

    return removed_diagram_names, removed_model_names


def cleanup_orphan_project_files(cursor: sqlite3.Cursor) -> None:
    diagram_ids = {row[0] for row in cursor.execute("select ID from DIAGRAM")}
    preview_ids = {
        preview_id
        for (definition,) in cursor.execute("select DEFINITION from DIAGRAM")
        if (preview_id := extract_preview_id(blob_to_text(definition)))
    }

    shape_paths = [row[0] for row in cursor.execute("select PATH from PROJECT_FILE where PATH like 'vpdiagramshapes/%.vps/details.xml'")]
    for path in shape_paths:
        match = re.fullmatch(r"vpdiagramshapes/(.+)\.vps/details\.xml", path)
        if match and match.group(1) not in diagram_ids:
            cursor.execute("delete from PROJECT_FILE where PATH=?", (path,))

    preview_paths = [row[0] for row in cursor.execute("select PATH from PROJECT_FILE where PATH like 'diagramPreviewData/%'")]
    for path in preview_paths:
        preview_id = path.removeprefix("diagramPreviewData/")
        if preview_id not in preview_ids:
            cursor.execute("delete from PROJECT_FILE where PATH=?", (path,))


def generate_activity_diagram(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    root_model_id: str,
    relationship_container_id: str,
    controlflow_container_id: str,
    root_child_ids: list[str],
    controlflow_child_ids: list[str],
    created_at_ms: int,
    created_at_s: int,
) -> tuple[str, str, list[str], list[str]]:
    parent_activity_id = find_or_create_model(cursor, existing_ids, "Activity", ACTIVITY_PARENT_NAME, root_model_id)
    diagram_id, diagram_preview_id = find_or_create_diagram(cursor, existing_ids, ACTIVITY_DIAGRAM_NAME, "ActivityDiagram")

    old_child_ids = collect_descendant_ids(cursor, parent_activity_id)
    old_controlflow_ids = ids_for_relationships_in_diagram(cursor, "ControlFlow", diagram_id)

    if old_child_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_child_ids))
    if old_controlflow_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_controlflow_ids))
    cursor.execute("delete from DIAGRAM_ELEMENT where DIAGRAM_ID=?", (diagram_id,))

    controlflow_child_ids[:] = [item for item in controlflow_child_ids if item not in old_controlflow_ids]
    if parent_activity_id not in root_child_ids:
        root_child_ids.append(parent_activity_id)

    nodes, edges = build_activity_specs()
    node_by_key = {node.key: node for node in nodes}
    node_ids = {node.key: generate_id(existing_ids) for node in nodes}
    node_shape_ids = {node.key: generate_id(existing_ids) for node in nodes}
    node_view_ref_ids = {node.key: generate_id(existing_ids) for node in nodes}
    edge_ids = {edge.key: generate_id(existing_ids) for edge in edges}
    edge_shape_ids = {edge.key: generate_id(existing_ids) for edge in edges}
    edge_view_ref_ids = {edge.key: generate_id(existing_ids) for edge in edges}

    incoming_edges: dict[str, list[str]] = {node.key: [] for node in nodes}
    outgoing_edges: dict[str, list[str]] = {node.key: [] for node in nodes}
    for edge in edges:
        incoming_edges[edge.dst].append(edge_ids[edge.key])
        outgoing_edges[edge.src].append(edge_ids[edge.key])
        controlflow_child_ids.append(edge_ids[edge.key])

    parent_child_ids = [node_ids[node.key] for node in nodes]
    parent_activity_definition = render_parent_activity_definition(
        root_model_id,
        parent_activity_id,
        ACTIVITY_PARENT_NAME,
        parent_child_ids,
        diagram_id,
        created_at_ms,
        created_at_ms,
    )
    cursor.execute(
        """
        insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
        values (?, NULL, NULL, 'Activity', ?, ?, ?, NULL, ?, ?, ?)
        on conflict(ID) do update set
            MODEL_TYPE='Activity',
            PARENT_ID=excluded.PARENT_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION,
            AUTHOR=excluded.AUTHOR,
            LAST_MOD_AT=excluded.LAST_MOD_AT
        """,
        (
            parent_activity_id,
            root_model_id,
            ACTIVITY_PARENT_NAME,
            encode_text(parent_activity_definition),
            AUTHOR,
            created_at_s,
            created_at_s,
        ),
    )

    for node in nodes:
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, ?, ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                node_ids[node.key],
                node.model_type,
                parent_activity_id,
                node.name,
                encode_text(
                    render_activity_model_definition(
                        root_model_id,
                        parent_activity_id,
                        diagram_id,
                        node_ids[node.key],
                        node_shape_ids[node.key],
                        node_view_ref_ids[node.key],
                        node.model_type,
                        node.name,
                        incoming_edges[node.key],
                        outgoing_edges[node.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, ?, ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                node_shape_ids[node.key],
                node.model_type,
                diagram_id,
                node_ids[node.key],
                encode_text(
                    render_activity_node_shape_definition(
                        root_model_id,
                        parent_activity_id,
                        node_ids[node.key],
                        node_shape_ids[node.key],
                        node.model_type,
                        node.name,
                        node.x,
                        node.y,
                        node.width,
                        node.height,
                    )
                ),
            ),
        )

    for edge in edges:
        source = node_by_key[edge.src]
        target = node_by_key[edge.dst]
        points, x, y, width, height = compute_edge_geometry(
            source.x,
            source.y,
            source.width,
            source.height,
            target.x,
            target.y,
            target.width,
            target.height,
        )
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'ControlFlow', ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                edge_ids[edge.key],
                controlflow_container_id,
                edge.label,
                encode_text(
                    render_controlflow_model_definition(
                        root_model_id,
                        parent_activity_id,
                        diagram_id,
                        edge_ids[edge.key],
                        edge_shape_ids[edge.key],
                        edge_view_ref_ids[edge.key],
                        node_ids[edge.src],
                        node_ids[edge.dst],
                        edge.label,
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'ControlFlow', ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                edge_shape_ids[edge.key],
                diagram_id,
                edge_ids[edge.key],
                encode_text(
                    render_controlflow_shape_definition(
                        diagram_id,
                        edge_ids[edge.key],
                        edge_shape_ids[edge.key],
                        node_shape_ids[edge.src],
                        node_shape_ids[edge.dst],
                        edge.label,
                        points,
                        x,
                        y,
                        width,
                        height,
                    )
                ),
            ),
        )

    diagram_shape_ids = [node_shape_ids[node.key] for node in nodes] + [edge_shape_ids[edge.key] for edge in edges]
    cursor.execute(
        """
        insert into DIAGRAM(ID, DIAGRAM_TYPE, PARENT_MODEL_ID, NAME, DEFINITION)
        values (?, 'ActivityDiagram', ?, ?, ?)
        on conflict(ID) do update set
            DIAGRAM_TYPE='ActivityDiagram',
            PARENT_MODEL_ID=excluded.PARENT_MODEL_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION
        """,
        (
            diagram_id,
            parent_activity_id,
            ACTIVITY_DIAGRAM_NAME,
            encode_text(
                render_activity_diagram_definition(
                    root_model_id,
                    parent_activity_id,
                    ACTIVITY_DIAGRAM_NAME,
                    diagram_id,
                    diagram_preview_id,
                    diagram_shape_ids,
                    created_at_ms,
                    created_at_ms,
                )
            ),
        ),
    )
    upsert_project_file(cursor, f"vpdiagramshapes/{diagram_id}.vps/details.xml", select_template_details(cursor, "ActivityDiagram"))
    upsert_project_file(cursor, f"diagramPreviewData/{diagram_preview_id}", gzip.compress(make_png(), compresslevel=9))
    return diagram_id, parent_activity_id, parent_child_ids, old_controlflow_ids


def generate_block_diagram(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    root_model_id: str,
    relationship_container_id: str,
    association_container_id: str,
    root_child_ids: list[str],
    association_child_ids: list[str],
    created_at_ms: int,
    created_at_s: int,
) -> tuple[str, str, list[str], dict[str, str], dict[str, BlockSpec]]:
    main_block_id = find_or_create_model(cursor, existing_ids, "SysMLBlock", MAIN_BLOCK_NAME, root_model_id)
    diagram_id, diagram_preview_id = find_or_create_diagram(cursor, existing_ids, BLOCK_DIAGRAM_NAME, "BlockDefinitionDiagram")
    block_stereotype_id = find_one(
        cursor,
        "select ID from MODEL_ELEMENT where MODEL_TYPE='Stereotype' and NAME=?",
        (BLOCK_STEREOTYPE_NAME,),
    )[0]

    old_descendants = collect_descendant_ids(cursor, main_block_id)
    old_association_ids = ids_for_relationships_in_diagram(cursor, "Association", diagram_id)
    if old_descendants:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_descendants))
    if old_association_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_association_ids))
    cursor.execute("delete from DIAGRAM_ELEMENT where DIAGRAM_ID=?", (diagram_id,))

    association_child_ids[:] = [item for item in association_child_ids if item not in old_association_ids]
    if main_block_id not in root_child_ids:
        root_child_ids.append(main_block_id)

    blocks, associations = build_block_specs()
    block_specs = {block.key: block for block in blocks}
    block_ids = {block.key: (main_block_id if block.key == "compiler" else generate_id(existing_ids)) for block in blocks}
    block_shape_ids = {block.key: generate_id(existing_ids) for block in blocks}
    block_view_ref_ids = {block.key: generate_id(existing_ids) for block in blocks}

    association_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    association_shape_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    association_view_ref_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    from_end_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    from_qualifier_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    to_end_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    to_qualifier_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}

    children_by_parent: dict[str, list[str]] = {block.key: [] for block in blocks}
    for block in blocks:
        if block.parent_key:
            children_by_parent[block.parent_key].append(block.key)

    from_assoc_refs: dict[str, list[str]] = {block.key: [] for block in blocks}
    to_assoc_refs: dict[str, list[str]] = {block.key: [] for block in blocks}
    for assoc in associations:
        assoc_ref = f"<{relationship_container_id}:{association_container_id}:{association_ids[assoc.key]}"
        from_assoc_refs[assoc.src].append(f"{assoc_ref}${from_end_ids[assoc.key]}>")
        to_assoc_refs[assoc.dst].append(f"{assoc_ref}${to_end_ids[assoc.key]}>")
        association_child_ids.append(association_ids[assoc.key])

    addresses = {key: model_address(root_model_id, block_ids, block_specs, key) for key in block_specs}

    for block in blocks:
        parent_id = root_model_id if block.parent_key is None else block_ids[block.parent_key]
        child_ids = [block_ids[child_key] for child_key in children_by_parent[block.key]]
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'SysMLBlock', ?, ?, ?, NULL, ?, ?, ?)
            on conflict(ID) do update set
                MODEL_TYPE='SysMLBlock',
                PARENT_ID=excluded.PARENT_ID,
                NAME=excluded.NAME,
                DEFINITION=excluded.DEFINITION,
                AUTHOR=excluded.AUTHOR,
                LAST_MOD_AT=excluded.LAST_MOD_AT
            """,
            (
                block_ids[block.key],
                parent_id,
                block.name,
                encode_text(
                    render_sysml_block_definition(
                        root_model_id,
                        diagram_id,
                        block_stereotype_id,
                        block_ids[block.key],
                        block_shape_ids[block.key],
                        block_view_ref_ids[block.key],
                        addresses[block.key],
                        block.name,
                        child_ids,
                        from_assoc_refs[block.key],
                        to_assoc_refs[block.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )

    for block in blocks:
        parent_shape_id = block_shape_ids[block.parent_key] if block.parent_key else None
        if block.parent_key:
            parent = block_specs[block.parent_key]
            shape_x = block.x - parent.x
            shape_y = block.y - parent.y
        else:
            shape_x = block.x
            shape_y = block.y
        contained_shape_ids = [block_shape_ids[child_key] for child_key in children_by_parent[block.key]]
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'SysMLBlock', ?, ?, NULL, NULL, ?, ?)
            """,
            (
                block_shape_ids[block.key],
                diagram_id,
                block_ids[block.key],
                parent_shape_id,
                encode_text(
                    render_block_shape_definition(
                        diagram_id,
                        block_shape_ids[block.key],
                        addresses[block.key],
                        block.name,
                        shape_x,
                        shape_y,
                        block.width,
                        block.height,
                        parent_shape_id,
                        contained_shape_ids,
                    )
                ),
            ),
        )

    for assoc in associations:
        source = block_specs[assoc.src]
        target = block_specs[assoc.dst]
        points, x, y, width, height = compute_edge_geometry(
            source.x,
            source.y,
            source.width,
            source.height,
            target.x,
            target.y,
            target.width,
            target.height,
        )
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'Association', ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                association_ids[assoc.key],
                association_container_id,
                assoc.label,
                encode_text(
                    render_association_model_definition(
                        relationship_container_id,
                        association_container_id,
                        diagram_id,
                        association_ids[assoc.key],
                        association_shape_ids[assoc.key],
                        association_view_ref_ids[assoc.key],
                        assoc.label,
                        addresses[assoc.src],
                        addresses[assoc.dst],
                        from_end_ids[assoc.key],
                        from_qualifier_ids[assoc.key],
                        to_end_ids[assoc.key],
                        to_qualifier_ids[assoc.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'Association', ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                association_shape_ids[assoc.key],
                diagram_id,
                association_ids[assoc.key],
                encode_text(
                    render_association_shape_definition(
                        relationship_container_id,
                        association_container_id,
                        diagram_id,
                        association_ids[assoc.key],
                        association_shape_ids[assoc.key],
                        block_shape_ids[assoc.src],
                        block_shape_ids[assoc.dst],
                        assoc.label,
                        points,
                        x,
                        y,
                        width,
                        height,
                    )
                ),
            ),
        )

    diagram_shape_ids = [block_shape_ids[block.key] for block in blocks] + [
        association_shape_ids[assoc.key] for assoc in associations
    ]
    cursor.execute(
        """
        insert into DIAGRAM(ID, DIAGRAM_TYPE, PARENT_MODEL_ID, NAME, DEFINITION)
        values (?, 'BlockDefinitionDiagram', ?, ?, ?)
        on conflict(ID) do update set
            DIAGRAM_TYPE='BlockDefinitionDiagram',
            PARENT_MODEL_ID=excluded.PARENT_MODEL_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION
        """,
        (
            diagram_id,
            main_block_id,
            BLOCK_DIAGRAM_NAME,
            encode_text(
                render_block_diagram_definition(
                    root_model_id,
                    main_block_id,
                    BLOCK_DIAGRAM_NAME,
                    diagram_id,
                    diagram_preview_id,
                    diagram_shape_ids,
                    created_at_ms,
                    created_at_ms,
                )
            ),
        ),
    )
    upsert_project_file(
        cursor,
        f"vpdiagramshapes/{diagram_id}.vps/details.xml",
        select_template_details(cursor, "BlockDefinitionDiagram"),
    )
    upsert_project_file(cursor, f"diagramPreviewData/{diagram_preview_id}", gzip.compress(make_png(), compresslevel=9))
    return diagram_id, main_block_id, old_association_ids, block_ids, block_specs


def append_model_view(definition: str, diagram_id: str, shape_id: str, view_ref_id: str) -> str:
    marker = f'view="{shape_id}";'
    if marker in definition:
        return definition
    entry = (
        f'\t\t{{{view_ref_id}:"View":ModelView {{\n'
        f"\t\t\tcontainer=<{diagram_id}>;\n"
        f'\t\t\tview="{shape_id}";\n'
        "\t\t}}\n"
    )
    pattern = re.compile(r"(\t_modelViews=\(\n)(.*?)(\n\t\);)", re.S)
    match = pattern.search(definition)
    if not match:
        return definition
    body = match.group(2).rstrip()
    separator = ",\n" if body else ""
    rebuilt = match.group(1) + body + separator + entry + match.group(3)
    return definition[: match.start()] + rebuilt + definition[match.end() :]


def append_child_refs(definition: str, parent_address: str, child_ids: list[str]) -> str:
    refs = [f"<{parent_address}:{child_id}>" for child_id in child_ids]
    new_refs = [ref for ref in refs if ref not in definition]
    if not new_refs:
        return definition

    pattern = re.compile(r"(\tChild=\(\n)(.*?)(\n\t\);)", re.S)
    match = pattern.search(definition)
    if not match:
        return definition

    body = match.group(2).rstrip()
    rendered = ", \n".join(f"\t\t{ref}" for ref in new_refs)
    separator = ", \n" if body else ""
    rebuilt = match.group(1) + body + separator + rendered + match.group(3)
    return definition[: match.start()] + rebuilt + definition[match.end() :]


def generate_encoder_diagram(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    root_model_id: str,
    relationship_container_id: str,
    association_container_id: str,
    main_block_id: str,
    block_ids: dict[str, str],
    block_specs: dict[str, BlockSpec],
    association_child_ids: list[str],
    created_at_ms: int,
    created_at_s: int,
) -> str:
    diagram_id, diagram_preview_id = find_or_create_diagram(
        cursor,
        existing_ids,
        ENCODER_DIAGRAM_NAME,
        "BlockDefinitionDiagram",
    )
    old_association_ids = ids_for_relationships_in_diagram(cursor, "Association", diagram_id)
    if old_association_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_association_ids))
    cursor.execute("delete from DIAGRAM_ELEMENT where DIAGRAM_ID=?", (diagram_id,))
    association_child_ids[:] = [item for item in association_child_ids if item not in old_association_ids]

    view_specs = {
        "labels": BlockSpec("labels", block_specs["labels"].name, 80, 330, 280, 115),
        "binary": BlockSpec("binary", block_specs["binary"].name, 450, 80, 1220, 620),
        "cond": BlockSpec("cond", block_specs["cond"].name, 490, 180, 540, 70, "binary"),
        "type": BlockSpec("type", block_specs["type"].name, 1090, 180, 540, 70, "binary"),
        "supp": BlockSpec("supp", block_specs["supp"].name, 490, 290, 540, 70, "binary"),
        "funct": BlockSpec("funct", block_specs["funct"].name, 1090, 290, 540, 90, "binary"),
        "register": BlockSpec("register", block_specs["register"].name, 490, 420, 540, 75, "binary"),
        "operand2": BlockSpec("operand2", block_specs["operand2"].name, 1090, 420, 540, 75, "binary"),
        "validator": BlockSpec("validator", block_specs["validator"].name, 1770, 330, 330, 115),
    }
    shown_keys = ["labels", "binary", "cond", "type", "supp", "funct", "register", "operand2", "validator"]
    children_by_parent: dict[str, list[str]] = {key: [] for key in shown_keys}
    for key, spec in view_specs.items():
        if spec.parent_key:
            children_by_parent[spec.parent_key].append(key)

    block_shape_ids = {key: generate_id(existing_ids) for key in shown_keys}
    block_view_ref_ids = {key: generate_id(existing_ids) for key in shown_keys}
    addresses = {key: model_address(root_model_id, block_ids, block_specs, key) for key in shown_keys}

    for key in shown_keys:
        spec = view_specs[key]
        parent_shape_id = block_shape_ids[spec.parent_key] if spec.parent_key else None
        if spec.parent_key:
            parent = view_specs[spec.parent_key]
            shape_x = spec.x - parent.x
            shape_y = spec.y - parent.y
        else:
            shape_x = spec.x
            shape_y = spec.y
        contained_shape_ids = [block_shape_ids[child_key] for child_key in children_by_parent[key]]
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'SysMLBlock', ?, ?, NULL, NULL, ?, ?)
            """,
            (
                block_shape_ids[key],
                diagram_id,
                block_ids[key],
                parent_shape_id,
                encode_text(
                    render_block_shape_definition(
                        diagram_id,
                        block_shape_ids[key],
                        addresses[key],
                        spec.name,
                        shape_x,
                        shape_y,
                        spec.width,
                        spec.height,
                        parent_shape_id,
                        contained_shape_ids,
                    )
                ),
            ),
        )
        definition = blob_to_text(
            find_one(cursor, "select DEFINITION from MODEL_ELEMENT where ID=?", (block_ids[key],))[0]
        )
        cursor.execute(
            "update MODEL_ELEMENT set DEFINITION=?, LAST_MOD_AT=? where ID=?",
            (
                encode_text(append_model_view(definition, diagram_id, block_shape_ids[key], block_view_ref_ids[key])),
                created_at_s,
                block_ids[key],
            ),
        )

    associations = [
        AssociationSpec("e01", "labels", "binary", "assemblyResolvido"),
        AssociationSpec("e02", "binary", "validator", "instrucoesBinarias"),
    ]
    association_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    association_shape_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    association_view_ref_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    from_end_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    from_qualifier_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    to_end_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    to_qualifier_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}

    for assoc in associations:
        association_child_ids.append(association_ids[assoc.key])
        source = view_specs[assoc.src]
        target = view_specs[assoc.dst]
        points, x, y, width, height = compute_edge_geometry(
            source.x,
            source.y,
            source.width,
            source.height,
            target.x,
            target.y,
            target.width,
            target.height,
        )
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'Association', ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                association_ids[assoc.key],
                association_container_id,
                assoc.label,
                encode_text(
                    render_association_model_definition(
                        relationship_container_id,
                        association_container_id,
                        diagram_id,
                        association_ids[assoc.key],
                        association_shape_ids[assoc.key],
                        association_view_ref_ids[assoc.key],
                        assoc.label,
                        addresses[assoc.src],
                        addresses[assoc.dst],
                        from_end_ids[assoc.key],
                        from_qualifier_ids[assoc.key],
                        to_end_ids[assoc.key],
                        to_qualifier_ids[assoc.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'Association', ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                association_shape_ids[assoc.key],
                diagram_id,
                association_ids[assoc.key],
                encode_text(
                    render_association_shape_definition(
                        relationship_container_id,
                        association_container_id,
                        diagram_id,
                        association_ids[assoc.key],
                        association_shape_ids[assoc.key],
                        block_shape_ids[assoc.src],
                        block_shape_ids[assoc.dst],
                        assoc.label,
                        points,
                        x,
                        y,
                        width,
                        height,
                    )
                ),
            ),
        )

    diagram_shape_ids = [block_shape_ids[key] for key in shown_keys] + [
        association_shape_ids[assoc.key] for assoc in associations
    ]
    cursor.execute(
        """
        insert into DIAGRAM(ID, DIAGRAM_TYPE, PARENT_MODEL_ID, NAME, DEFINITION)
        values (?, 'BlockDefinitionDiagram', ?, ?, ?)
        on conflict(ID) do update set
            DIAGRAM_TYPE='BlockDefinitionDiagram',
            PARENT_MODEL_ID=excluded.PARENT_MODEL_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION
        """,
        (
            diagram_id,
            main_block_id,
            ENCODER_DIAGRAM_NAME,
            encode_text(
                render_block_diagram_definition(
                    root_model_id,
                    main_block_id,
                    ENCODER_DIAGRAM_NAME,
                    diagram_id,
                    diagram_preview_id,
                    diagram_shape_ids,
                    created_at_ms,
                    created_at_ms,
                )
            ),
        ),
    )
    upsert_project_file(
        cursor,
        f"vpdiagramshapes/{diagram_id}.vps/details.xml",
        select_template_details(cursor, "BlockDefinitionDiagram"),
    )
    upsert_project_file(cursor, f"diagramPreviewData/{diagram_preview_id}", gzip.compress(make_png(), compresslevel=9))
    return diagram_id


def build_module_hierarchy_specs() -> tuple[list[BlockSpec], list[AssociationSpec]]:
    blocks = [
        BlockSpec("compiler", MAIN_BLOCK_NAME, 30, 50, 2880, 2050),
        BlockSpec(
            "hierarchy",
            "Hierarquia real do código — pastas, arquivos e partes importantes",
            70,
            105,
            2800,
            1890,
            "compiler",
        ),
        BlockSpec("entry", "Controle principal — compiler/", 100, 160, 460, 330, "hierarchy"),
        BlockSpec("main_c", "compiler/main.c — abre entrada, chama parser, semântica e limpeza", 125, 215, 410, 220, "entry"),
        BlockSpec("main_func", "main()", 145, 285, 170, 60, "main_c"),
        BlockSpec("declare_builtins", "declareBuiltins(...)", 335, 285, 180, 60, "main_c"),
        BlockSpec("parser_dir", "compiler/parser/ — Flex e Bison", 590, 160, 700, 520, "hierarchy"),
        BlockSpec("lexer_l", "lexer.l — regras Flex da análise léxica", 620, 225, 310, 310, "parser_dir"),
        BlockSpec("lexer_tokens", "tokens: IF, ELSE, WHILE, RETURN, INT, VOID, ID, NUM, operadores e delimitadores", 640, 285, 270, 85, "lexer_l"),
        BlockSpec("ignore_comment", "ignore_comment()", 640, 390, 270, 60, "lexer_l"),
        BlockSpec("lexical_error", "recordLexicalError() quando encontra LEX_ERROR", 640, 465, 270, 50, "lexer_l"),
        BlockSpec("parser_y", "parser.y — gramática C- e ações semânticas do parser", 950, 225, 310, 390, "parser_dir"),
        BlockSpec("parser_tokens", "%token IF, WHILE, RETURN, INT, VOID, ID, NUM, LEX_ERROR, ...", 970, 285, 270, 70, "parser_y"),
        BlockSpec("grammar_actions", "ações: newNode(), addChild(), declareSymbol(), pushScope()", 970, 375, 270, 85, "parser_y"),
        BlockSpec("yyerror", "yyerror(...) e recordSyntaxError()", 970, 480, 270, 55, "parser_y"),
        BlockSpec("src_dir", "compiler/src/ — AST, escopos, semântica, símbolos e IR", 1320, 160, 1520, 900, "hierarchy"),
        BlockSpec("syntax_tree_file", "syntax_tree.c/h — árvore sintática genérica", 1350, 225, 460, 250, "src_dir"),
        BlockSpec("ast_structs", "AstNodeKind e struct AstNode", 1370, 285, 420, 55, "syntax_tree_file"),
        BlockSpec("ast_constructors", "newNode(), newIdNode(), newNumNode(), newOpNode()", 1370, 355, 420, 55, "syntax_tree_file"),
        BlockSpec("ast_utils", "addChild(), printAst(), freeAst()", 1370, 425, 420, 40, "syntax_tree_file"),
        BlockSpec("symbol_table_file", "symbol_table.c/h — tabela de símbolos do frontend", 1830, 225, 460, 250, "src_dir"),
        BlockSpec("symbol_structs", "SymbolKind, LineNode, Symbol e SymbolTable", 1850, 285, 420, 55, "symbol_table_file"),
        BlockSpec("symbol_declare", "declareSymbol(), registerSymbolUse(), setFunctionParams()", 1850, 355, 420, 55, "symbol_table_file"),
        BlockSpec("symbol_lookup", "getSymbol(), resolveSymbol(), printSymbolTable()", 1850, 425, 420, 40, "symbol_table_file"),
        BlockSpec("utils_file", "utils.c/h — pilha de escopos", 2310, 225, 500, 250, "src_dir"),
        BlockSpec("scope_state", "currentScope, scopeStack, blockCounter", 2330, 285, 460, 55, "utils_file"),
        BlockSpec("scope_ops", "initScopeStack(), pushScope(), pushBlockScope(), popScope()", 2330, 355, 460, 55, "utils_file"),
        BlockSpec("scope_query", "getScopeDepth(), getScopeNameAt(), isScopeActive()", 2330, 425, 460, 40, "utils_file"),
        BlockSpec("analysis_state_file", "analysis_state.c/h — estado de erros léxicos e sintáticos", 1350, 500, 460, 220, "src_dir"),
        BlockSpec("analysis_state_struct", "struct AnalysisState e gAnalysisState", 1370, 560, 420, 55, "analysis_state_file"),
        BlockSpec("analysis_state_ops", "resetAnalysisState(), recordLexicalError(), recordSyntaxError(), consumePendingLexicalError()", 1370, 630, 420, 65, "analysis_state_file"),
        BlockSpec("semantic_file", "semantic.c/h — análise semântica", 1830, 500, 460, 350, "src_dir"),
        BlockSpec("semantic_structs", "ExpType, SemanticReport e SemanticContext", 1850, 560, 420, 55, "semantic_file"),
        BlockSpec("semantic_analyze", "semanticAnalyze(AstNode *root, SymbolTable *symtab)", 1850, 630, 420, 60, "semantic_file"),
        BlockSpec("semantic_helpers", "analyzeProgram(), analyzeDeclaration(), analyzeBlock(), analyzeExpression()", 1850, 705, 420, 70, "semantic_file"),
        BlockSpec("semantic_errors", "semanticError(...) e verificação de main/return/tipos", 1850, 790, 420, 45, "semantic_file"),
        BlockSpec("ir_file", "ir.c/h — geração de código intermediário", 2310, 500, 500, 350, "src_dir"),
        BlockSpec("ir_structs", "OperandKind, Operand, IrOpcode, IRInstruction e IRList", 2330, 560, 460, 55, "ir_file"),
        BlockSpec("ir_generate", "generate_ir(...), generate_ir_for_node(), generate_ir_for_expr()", 2330, 630, 460, 60, "ir_file"),
        BlockSpec("ir_emit", "emit(), new_temp(), new_label(), remove_unreachable_code()", 2330, 705, 460, 65, "ir_file"),
        BlockSpec("ir_output", "print_ir(...), free_ir(...), compiler/docs/generated/intermediate/semantic/ir/generated_IR.txt", 2330, 790, 460, 45, "ir_file"),
        BlockSpec("backend_dir", "compiler/codegen/ — backend Python", 100, 720, 1190, 1100, "hierarchy"),
        BlockSpec("codegen_main", "main.py — orquestra o backend e escreve saídas", 130, 785, 340, 270, "backend_dir"),
        BlockSpec("main_read_ir", "lê compiler/docs/generated/intermediate/semantic/ir/generated_IR.txt", 150, 845, 300, 50, "codegen_main"),
        BlockSpec("main_write_outputs", "escreve generated_assembly.txt, generated_machine_code.txt e debug_*.txt", 150, 910, 300, 75, "codegen_main"),
        BlockSpec("main_fullcode", "chama generate_assembly(...) e FullCode(...)", 150, 1000, 300, 40, "codegen_main"),
        BlockSpec("codegen_py", "codegen.py — IR textual para assembly", 490, 785, 760, 500, "backend_dir"),
        BlockSpec("data_memory_manager", "class DataMemoryManager — endereços da seção .data", 520, 850, 330, 65, "codegen_py"),
        BlockSpec("register_allocator", "class RegisterAllocator — variáveis, temporários, registradores e spill", 875, 850, 340, 80, "codegen_py"),
        BlockSpec("function_context", "class FunctionContext — instruções, frame, labels e layout de pilha", 520, 950, 330, 80, "codegen_py"),
        BlockSpec("translate_instruction", "translate_instruction(), emit_call(), emit_pending_args()", 875, 955, 340, 75, "codegen_py"),
        BlockSpec("generate_assembly_fn", "generate_assembly(ir_list)", 520, 1055, 330, 60, "codegen_py"),
        BlockSpec("backend_maps", "IR_TO_ASSEMBLY_BRANCH, SPECIAL_REGS, ARG_REGS, IR_TEMP_RE", 875, 1055, 340, 60, "codegen_py"),
        BlockSpec("assembler_py", "assembler.py — assembler e codificador binário", 130, 1090, 1120, 420, "backend_dir"),
        BlockSpec("assembler_tables", "CONDITION_CODES, SUPPORT_BITS e INSTRUCTION_INFO", 160, 1155, 330, 60, "assembler_py"),
        BlockSpec("parsed_instruction", "dataclass ParsedInstruction", 510, 1155, 280, 60, "assembler_py"),
        BlockSpec("fullcode_class", "class FullCode", 810, 1155, 390, 60, "assembler_py"),
        BlockSpec("assembler_parse", "_parse_source(), _parse_instruction(), _parse_operands()", 160, 1240, 330, 65, "assembler_py"),
        BlockSpec("assembler_labels", "_stabilize_text_layout(), _rebuild_text_labels(), _plan_instruction(), _expand_instruction()", 510, 1240, 690, 80, "assembler_py"),
        BlockSpec("assembler_encode", "_encode(), _encode_concrete(), twos_complement(), register_bits()", 160, 1345, 520, 70, "assembler_py"),
        BlockSpec("assembler_decode", "decode_machine_code() e response='Error: ...'", 710, 1345, 490, 70, "assembler_py"),
        BlockSpec("backend_symbol_table", "symbol_table.py — símbolos usados pelo backend", 130, 1540, 360, 230, "backend_dir"),
        BlockSpec("backend_types", "Type, IntegerType e ArrayType", 150, 1600, 320, 55, "backend_symbol_table"),
        BlockSpec("backend_symbols", "Symbol e SymbolTable.add_symbol()/get_symbol()", 150, 1670, 320, 65, "backend_symbol_table"),
        BlockSpec("constants_py", "constants.py — constantes de memória", 510, 1540, 300, 160, "backend_dir"),
        BlockSpec("constants_values", "STACK_WORDS, INITIAL_SP, DATA_SECTION_BASE", 530, 1605, 260, 65, "constants_py"),
        BlockSpec("assembler_regressions", "assembler_regressions.py — testes do assembler", 830, 1540, 420, 160, "backend_dir"),
        BlockSpec("assembler_tests", "run_conditional_parse_regression() e run_long_branch_regression()", 850, 1605, 380, 65, "assembler_regressions"),
        BlockSpec("docs_aux", "Documentação, testes e artefatos auxiliares", 1320, 1100, 1520, 720, "hierarchy"),
        BlockSpec("test_files", "compiler/docs/input/cminus/ — amostras e fixtures válidas/inválidas", 1350, 1165, 450, 160, "docs_aux"),
        BlockSpec("output_files", "compiler/docs/generated/ — IR, assembly, binário, debug e logs gerados", 1820, 1165, 450, 200, "docs_aux"),
        BlockSpec("vpp_generator", "tools/generate_vpp_analysis_diagram.py — gera os diagramas SysML do projeto", 2290, 1165, 500, 200, "docs_aux"),
        BlockSpec("vpp_file", "vpp/cminus-compiler-expanded.vpp — artefato Visual Paradigm", 1350, 1375, 450, 150, "docs_aux"),
        BlockSpec("makefile", "compiler/Makefile — build, run, run_all, test_analysis e generate_*_vpp", 1820, 1405, 450, 160, "docs_aux"),
        BlockSpec("readme", "compiler/README.md — documentação do pipeline", 2290, 1405, 500, 160, "docs_aux"),
        BlockSpec("target", TARGET_BLOCK_NAME, 2940, 1640, 430, 180),
    ]

    associations = [
        AssociationSpec("h01", "makefile", "main_c", "make run compila e executa bin/c-c"),
        AssociationSpec("h02", "main_c", "parser_y", "main() chama yyparse()"),
        AssociationSpec("h03", "parser_y", "lexer_l", "yyparse() usa yylex()"),
        AssociationSpec("h04", "lexer_l", "analysis_state_file", "erro léxico chama recordLexicalError()"),
        AssociationSpec("h05", "parser_y", "analysis_state_file", "yyerror() chama recordSyntaxError()"),
        AssociationSpec("h06", "parser_y", "syntax_tree_file", "ações da gramática montam AstNode"),
        AssociationSpec("h07", "parser_y", "symbol_table_file", "declareSymbol() e setFunctionParams()"),
        AssociationSpec("h08", "parser_y", "utils_file", "pushScope(), pushBlockScope() e popScope()"),
        AssociationSpec("h09", "main_c", "semantic_file", "semanticAnalyze(syntax_tree, &symtab)"),
        AssociationSpec("h10", "semantic_file", "syntax_tree_file", "percorre AstNode"),
        AssociationSpec("h11", "semantic_file", "symbol_table_file", "consulta e registra uso de símbolos"),
        AssociationSpec("h12", "semantic_file", "utils_file", "reproduz cadeia de escopos"),
        AssociationSpec("h13", "semantic_file", "ir_file", "sem erros chama generate_ir()"),
        AssociationSpec("h14", "ir_file", "syntax_tree_file", "gera IR a partir da AST"),
        AssociationSpec("h15", "ir_file", "symbol_table_file", "usa símbolos para arrays e nomes"),
        AssociationSpec("h16", "ir_file", "output_files", "print_ir() cria generated_IR.txt"),
        AssociationSpec("h17", "codegen_main", "output_files", "lê generated_IR.txt e escreve saídas"),
        AssociationSpec("h18", "codegen_main", "codegen_py", "chama generate_assembly()"),
        AssociationSpec("h19", "codegen_py", "backend_symbol_table", "usa SymbolTable do backend para .data"),
        AssociationSpec("h20", "codegen_py", "constants_py", "usa STACK_WORDS, INITIAL_SP e DATA_SECTION_BASE"),
        AssociationSpec("h21", "codegen_main", "assembler_py", "instancia FullCode(assembly_lines)"),
        AssociationSpec("h22", "assembler_py", "constants_py", "usa STACK_WORDS nos testes/listagens"),
        AssociationSpec("h23", "assembler_regressions", "assembler_py", "testa parsing condicional e branch longo"),
        AssociationSpec("h24", "assembler_py", "output_files", "gera binário e debug_machine_code.txt"),
        AssociationSpec("h25", "output_files", "target", "binário de 32 bits é destino da arquitetura alvo"),
        AssociationSpec("h26", "vpp_generator", "vpp_file", "atualiza o arquivo .vpp"),
        AssociationSpec("h27", "readme", "vpp_file", "documenta os diagramas SysML"),
        AssociationSpec("h28", "test_files", "makefile", "fixtures usados por make run e run_all"),
    ]
    return blocks, associations


def generate_module_hierarchy_diagram(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    root_model_id: str,
    relationship_container_id: str,
    association_container_id: str,
    main_block_id: str,
    root_child_ids: list[str],
    association_child_ids: list[str],
    created_at_ms: int,
    created_at_s: int,
) -> str:
    diagram_id, diagram_preview_id = find_or_create_diagram(
        cursor,
        existing_ids,
        MODULE_HIERARCHY_DIAGRAM_NAME,
        "BlockDefinitionDiagram",
    )
    block_stereotype_id = find_one(
        cursor,
        "select ID from MODEL_ELEMENT where MODEL_TYPE='Stereotype' and NAME=?",
        (BLOCK_STEREOTYPE_NAME,),
    )[0]

    old_association_ids = ids_for_relationships_in_diagram(cursor, "Association", diagram_id)
    if old_association_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_association_ids))
    cursor.execute("delete from DIAGRAM_ELEMENT where DIAGRAM_ID=?", (diagram_id,))
    association_child_ids[:] = [item for item in association_child_ids if item not in old_association_ids]

    blocks, associations = build_module_hierarchy_specs()
    block_specs = {block.key: block for block in blocks}
    target_block_id = find_or_create_model(cursor, existing_ids, "SysMLBlock", TARGET_BLOCK_NAME, root_model_id)
    block_ids = {
        block.key: (
            main_block_id
            if block.key == "compiler"
            else target_block_id
            if block.key == "target"
            else generate_id(existing_ids)
        )
        for block in blocks
    }
    block_shape_ids = {block.key: generate_id(existing_ids) for block in blocks}
    block_view_ref_ids = {block.key: generate_id(existing_ids) for block in blocks}

    association_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    association_shape_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    association_view_ref_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    from_end_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    from_qualifier_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    to_end_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}
    to_qualifier_ids = {assoc.key: generate_id(existing_ids) for assoc in associations}

    if target_block_id not in root_child_ids:
        root_child_ids.append(target_block_id)

    children_by_parent: dict[str, list[str]] = {block.key: [] for block in blocks}
    for block in blocks:
        if block.parent_key:
            children_by_parent[block.parent_key].append(block.key)

    from_assoc_refs: dict[str, list[str]] = {block.key: [] for block in blocks}
    to_assoc_refs: dict[str, list[str]] = {block.key: [] for block in blocks}
    for assoc in associations:
        assoc_ref = f"<{relationship_container_id}:{association_container_id}:{association_ids[assoc.key]}"
        from_assoc_refs[assoc.src].append(f"{assoc_ref}${from_end_ids[assoc.key]}>")
        to_assoc_refs[assoc.dst].append(f"{assoc_ref}${to_end_ids[assoc.key]}>")
        association_child_ids.append(association_ids[assoc.key])

    addresses = {key: model_address(root_model_id, block_ids, block_specs, key) for key in block_specs}

    for block in blocks:
        if block.key == "compiler":
            continue
        parent_id = root_model_id if block.parent_key is None else block_ids[block.parent_key]
        child_ids = [block_ids[child_key] for child_key in children_by_parent[block.key]]
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'SysMLBlock', ?, ?, ?, NULL, ?, ?, ?)
            on conflict(ID) do update set
                MODEL_TYPE='SysMLBlock',
                PARENT_ID=excluded.PARENT_ID,
                NAME=excluded.NAME,
                DEFINITION=excluded.DEFINITION,
                AUTHOR=excluded.AUTHOR,
                LAST_MOD_AT=excluded.LAST_MOD_AT
            """,
            (
                block_ids[block.key],
                parent_id,
                block.name,
                encode_text(
                    render_sysml_block_definition(
                        root_model_id,
                        diagram_id,
                        block_stereotype_id,
                        block_ids[block.key],
                        block_shape_ids[block.key],
                        block_view_ref_ids[block.key],
                        addresses[block.key],
                        block.name,
                        child_ids,
                        from_assoc_refs[block.key],
                        to_assoc_refs[block.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )

    compiler_definition = blob_to_text(
        find_one(cursor, "select DEFINITION from MODEL_ELEMENT where ID=?", (main_block_id,))[0]
    )
    compiler_definition = append_child_refs(
        compiler_definition,
        addresses["compiler"],
        [block_ids[child_key] for child_key in children_by_parent["compiler"]],
    )
    compiler_definition = append_model_view(
        compiler_definition,
        diagram_id,
        block_shape_ids["compiler"],
        block_view_ref_ids["compiler"],
    )
    cursor.execute(
        "update MODEL_ELEMENT set DEFINITION=?, AUTHOR=?, LAST_MOD_AT=? where ID=?",
        (encode_text(compiler_definition), AUTHOR, created_at_s, main_block_id),
    )

    for block in blocks:
        parent_shape_id = block_shape_ids[block.parent_key] if block.parent_key else None
        if block.parent_key:
            parent = block_specs[block.parent_key]
            shape_x = block.x - parent.x
            shape_y = block.y - parent.y
        else:
            shape_x = block.x
            shape_y = block.y
        contained_shape_ids = [block_shape_ids[child_key] for child_key in children_by_parent[block.key]]
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'SysMLBlock', ?, ?, NULL, NULL, ?, ?)
            """,
            (
                block_shape_ids[block.key],
                diagram_id,
                block_ids[block.key],
                parent_shape_id,
                encode_text(
                    render_block_shape_definition(
                        diagram_id,
                        block_shape_ids[block.key],
                        addresses[block.key],
                        block.name,
                        shape_x,
                        shape_y,
                        block.width,
                        block.height,
                        parent_shape_id,
                        contained_shape_ids,
                    )
                ),
            ),
        )

    for assoc in associations:
        source = block_specs[assoc.src]
        target = block_specs[assoc.dst]
        points, x, y, width, height = compute_edge_geometry(
            source.x,
            source.y,
            source.width,
            source.height,
            target.x,
            target.y,
            target.width,
            target.height,
        )
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'Association', ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                association_ids[assoc.key],
                association_container_id,
                assoc.label,
                encode_text(
                    render_association_model_definition(
                        relationship_container_id,
                        association_container_id,
                        diagram_id,
                        association_ids[assoc.key],
                        association_shape_ids[assoc.key],
                        association_view_ref_ids[assoc.key],
                        assoc.label,
                        addresses[assoc.src],
                        addresses[assoc.dst],
                        from_end_ids[assoc.key],
                        from_qualifier_ids[assoc.key],
                        to_end_ids[assoc.key],
                        to_qualifier_ids[assoc.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'Association', ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                association_shape_ids[assoc.key],
                diagram_id,
                association_ids[assoc.key],
                encode_text(
                    render_association_shape_definition(
                        relationship_container_id,
                        association_container_id,
                        diagram_id,
                        association_ids[assoc.key],
                        association_shape_ids[assoc.key],
                        block_shape_ids[assoc.src],
                        block_shape_ids[assoc.dst],
                        assoc.label,
                        points,
                        x,
                        y,
                        width,
                        height,
                    )
                ),
            ),
        )

    diagram_shape_ids = [block_shape_ids[block.key] for block in blocks] + [
        association_shape_ids[assoc.key] for assoc in associations
    ]
    cursor.execute(
        """
        insert into DIAGRAM(ID, DIAGRAM_TYPE, PARENT_MODEL_ID, NAME, DEFINITION)
        values (?, 'BlockDefinitionDiagram', ?, ?, ?)
        on conflict(ID) do update set
            DIAGRAM_TYPE='BlockDefinitionDiagram',
            PARENT_MODEL_ID=excluded.PARENT_MODEL_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION
        """,
        (
            diagram_id,
            main_block_id,
            MODULE_HIERARCHY_DIAGRAM_NAME,
            encode_text(
                render_block_diagram_definition(
                    root_model_id,
                    main_block_id,
                    MODULE_HIERARCHY_DIAGRAM_NAME,
                    diagram_id,
                    diagram_preview_id,
                    diagram_shape_ids,
                    created_at_ms,
                    created_at_ms,
                )
            ),
        ),
    )
    upsert_project_file(
        cursor,
        f"vpdiagramshapes/{diagram_id}.vps/details.xml",
        select_template_details(cursor, "BlockDefinitionDiagram"),
    )
    upsert_project_file(cursor, f"diagramPreviewData/{diagram_preview_id}", gzip.compress(make_png(), compresslevel=9))
    return diagram_id


def build_traceability_specs() -> tuple[list[ActivityNodeSpec], list[EdgeSpec]]:
    cminus = (
        "Código C-: void main(void) { int x; int y; x = input(); y = input(); "
        "if (x > y) output(x); else output(y); }"
    )
    ir = (
        "Código intermediário: t0 = CALL input(); r1 = t0; t1 = CALL input(); r2 = t1; "
        "t2 = r1 - r2; IF t2 > 0 GOTO L1; CALL output(r2); GOTO L2; L1: CALL output(r1); L2:"
    )
    assembly = (
        "Assembly: bl input; mov r1, r0; bl input; mov r2, r0; subs r3, r1, r2; "
        "bgt L1; mov r0, r2; bl output; b L2; L1: mov r0, r1; bl output; L2:"
    )
    binary = (
        "Binário conceitual: 0000111010000000000000xxxxxxxxxx; "
        "00000000100000001000000000000000; 0000111010000000000000xxxxxxxxxx; "
        "00000000100000010000000000000000; 00000001000100011000010001000000; "
        "0011110000000000000000xxxxxxxxxx; 00000000100000000000000001000000; "
        "0000111010000000000000xxxxxxxxxx; 0000110000000000000000xxxxxxxxxx; "
        "00000000100000000000000000100000; 0000111010000000000000xxxxxxxxxx. "
        "O x marca campos que dependem da resolução de rótulo ou da posição final."
    )

    nodes = [
        ActivityNodeSpec("start", "InitialNode", "Início do mapeamento", 60, 215, 20, 20),
        ActivityNodeSpec("cminus", "ActivityAction", cminus, 130, 120, 420, 220),
        ActivityNodeSpec("ir", "ActivityAction", ir, 630, 120, 480, 220),
        ActivityNodeSpec("assembly", "ActivityAction", assembly, 1190, 120, 480, 220),
        ActivityNodeSpec("binary", "ActivityAction", binary, 1750, 80, 560, 300),
        ActivityNodeSpec("final", "ActivityFinalNode", "Fim do mapeamento", 2390, 215, 20, 20),
    ]
    edges = [
        EdgeSpec("t01", "start", "cminus"),
        EdgeSpec("t02", "cminus", "ir", "gera representação intermediária"),
        EdgeSpec("t03", "ir", "assembly", "mapeia registradores e instruções"),
        EdgeSpec("t04", "assembly", "binary", "resolve rótulos e codifica 32 bits"),
        EdgeSpec("t05", "binary", "final"),
    ]
    return nodes, edges


def generate_traceability_diagram(
    cursor: sqlite3.Cursor,
    existing_ids: set[str],
    root_model_id: str,
    relationship_container_id: str,
    controlflow_container_id: str,
    root_child_ids: list[str],
    controlflow_child_ids: list[str],
    created_at_ms: int,
    created_at_s: int,
) -> str:
    parent_activity_id = find_or_create_model(
        cursor,
        existing_ids,
        "Activity",
        TRACEABILITY_PARENT_NAME,
        root_model_id,
    )
    diagram_id, diagram_preview_id = find_or_create_diagram(
        cursor,
        existing_ids,
        TRACEABILITY_DIAGRAM_NAME,
        "ActivityDiagram",
    )

    old_child_ids = collect_descendant_ids(cursor, parent_activity_id)
    old_controlflow_ids = ids_for_relationships_in_diagram(cursor, "ControlFlow", diagram_id)
    if old_child_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_child_ids))
    if old_controlflow_ids:
        cursor.executemany("delete from MODEL_ELEMENT where ID=?", ((item,) for item in old_controlflow_ids))
    cursor.execute("delete from DIAGRAM_ELEMENT where DIAGRAM_ID=?", (diagram_id,))

    controlflow_child_ids[:] = [item for item in controlflow_child_ids if item not in old_controlflow_ids]
    if parent_activity_id not in root_child_ids:
        root_child_ids.append(parent_activity_id)

    nodes, edges = build_traceability_specs()
    node_by_key = {node.key: node for node in nodes}
    node_ids = {node.key: generate_id(existing_ids) for node in nodes}
    node_shape_ids = {node.key: generate_id(existing_ids) for node in nodes}
    node_view_ref_ids = {node.key: generate_id(existing_ids) for node in nodes}
    edge_ids = {edge.key: generate_id(existing_ids) for edge in edges}
    edge_shape_ids = {edge.key: generate_id(existing_ids) for edge in edges}
    edge_view_ref_ids = {edge.key: generate_id(existing_ids) for edge in edges}

    incoming_edges: dict[str, list[str]] = {node.key: [] for node in nodes}
    outgoing_edges: dict[str, list[str]] = {node.key: [] for node in nodes}
    for edge in edges:
        incoming_edges[edge.dst].append(edge_ids[edge.key])
        outgoing_edges[edge.src].append(edge_ids[edge.key])
        controlflow_child_ids.append(edge_ids[edge.key])

    parent_child_ids = [node_ids[node.key] for node in nodes]
    cursor.execute(
        """
        insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
        values (?, NULL, NULL, 'Activity', ?, ?, ?, NULL, ?, ?, ?)
        on conflict(ID) do update set
            MODEL_TYPE='Activity',
            PARENT_ID=excluded.PARENT_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION,
            AUTHOR=excluded.AUTHOR,
            LAST_MOD_AT=excluded.LAST_MOD_AT
        """,
        (
            parent_activity_id,
            root_model_id,
            TRACEABILITY_PARENT_NAME,
            encode_text(
                render_parent_activity_definition(
                    root_model_id,
                    parent_activity_id,
                    TRACEABILITY_PARENT_NAME,
                    parent_child_ids,
                    diagram_id,
                    created_at_ms,
                    created_at_ms,
                )
            ),
            AUTHOR,
            created_at_s,
            created_at_s,
        ),
    )

    for node in nodes:
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, ?, ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                node_ids[node.key],
                node.model_type,
                parent_activity_id,
                node.name,
                encode_text(
                    render_activity_model_definition(
                        root_model_id,
                        parent_activity_id,
                        diagram_id,
                        node_ids[node.key],
                        node_shape_ids[node.key],
                        node_view_ref_ids[node.key],
                        node.model_type,
                        node.name,
                        incoming_edges[node.key],
                        outgoing_edges[node.key],
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, ?, ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                node_shape_ids[node.key],
                node.model_type,
                diagram_id,
                node_ids[node.key],
                encode_text(
                    render_activity_node_shape_definition(
                        root_model_id,
                        parent_activity_id,
                        node_ids[node.key],
                        node_shape_ids[node.key],
                        node.model_type,
                        node.name,
                        node.x,
                        node.y,
                        node.width,
                        node.height,
                    )
                ),
            ),
        )

    for edge in edges:
        source = node_by_key[edge.src]
        target = node_by_key[edge.dst]
        points, x, y, width, height = compute_edge_geometry(
            source.x,
            source.y,
            source.width,
            source.height,
            target.x,
            target.y,
            target.width,
            target.height,
        )
        cursor.execute(
            """
            insert into MODEL_ELEMENT(ID, USER_ID, USER_ID_PARENT, MODEL_TYPE, PARENT_ID, NAME, DEFINITION, MIRROR_SOURCE, AUTHOR, CREATE_AT, LAST_MOD_AT)
            values (?, NULL, NULL, 'ControlFlow', ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                edge_ids[edge.key],
                controlflow_container_id,
                edge.label,
                encode_text(
                    render_controlflow_model_definition(
                        root_model_id,
                        parent_activity_id,
                        diagram_id,
                        edge_ids[edge.key],
                        edge_shape_ids[edge.key],
                        edge_view_ref_ids[edge.key],
                        node_ids[edge.src],
                        node_ids[edge.dst],
                        edge.label,
                        created_at_ms,
                        created_at_ms,
                    )
                ),
                AUTHOR,
                created_at_s,
                created_at_s,
            ),
        )
        cursor.execute(
            """
            insert into DIAGRAM_ELEMENT(ID, SHAPE_TYPE, DIAGRAM_ID, MODEL_ELEMENT_ID, COMPOSITE_MODEL_ELEMENT_ADDRESS, REF_MODEL_ELEMENT_ADDRESS, PARENT_ID, DEFINITION)
            values (?, 'ControlFlow', ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                edge_shape_ids[edge.key],
                diagram_id,
                edge_ids[edge.key],
                encode_text(
                    render_controlflow_shape_definition(
                        diagram_id,
                        edge_ids[edge.key],
                        edge_shape_ids[edge.key],
                        node_shape_ids[edge.src],
                        node_shape_ids[edge.dst],
                        edge.label,
                        points,
                        x,
                        y,
                        width,
                        height,
                    )
                ),
            ),
        )

    diagram_shape_ids = [node_shape_ids[node.key] for node in nodes] + [edge_shape_ids[edge.key] for edge in edges]
    cursor.execute(
        """
        insert into DIAGRAM(ID, DIAGRAM_TYPE, PARENT_MODEL_ID, NAME, DEFINITION)
        values (?, 'ActivityDiagram', ?, ?, ?)
        on conflict(ID) do update set
            DIAGRAM_TYPE='ActivityDiagram',
            PARENT_MODEL_ID=excluded.PARENT_MODEL_ID,
            NAME=excluded.NAME,
            DEFINITION=excluded.DEFINITION
        """,
        (
            diagram_id,
            parent_activity_id,
            TRACEABILITY_DIAGRAM_NAME,
            encode_text(
                render_activity_diagram_definition(
                    root_model_id,
                    parent_activity_id,
                    TRACEABILITY_DIAGRAM_NAME,
                    diagram_id,
                    diagram_preview_id,
                    diagram_shape_ids,
                    created_at_ms,
                    created_at_ms,
                )
            ),
        ),
    )
    upsert_project_file(cursor, f"vpdiagramshapes/{diagram_id}.vps/details.xml", select_template_details(cursor, "ActivityDiagram"))
    upsert_project_file(cursor, f"diagramPreviewData/{diagram_preview_id}", gzip.compress(make_png(), compresslevel=9))
    return diagram_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SysML Visual Paradigm diagrams for the C- compiler.")
    parser.add_argument(
        "vpp_path",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1] / "vpp" / "cminus-compiler-expanded.vpp"),
        help="Path to the .vpp SQLite file to update",
    )
    args = parser.parse_args()

    vpp_path = Path(args.vpp_path).resolve()
    if not vpp_path.exists():
        raise SystemExit(f"VPP file not found: {vpp_path}")

    connection = sqlite3.connect(vpp_path)
    cursor = connection.cursor()

    try:
        existing_ids = fetch_existing_ids(cursor)
        root_model_id = find_one(
            cursor,
            "select ID from MODEL_ELEMENT where MODEL_TYPE='Model' and NAME=?",
            (ROOT_MODEL_NAME,),
        )[0]
        relationship_container_id = find_one(
            cursor,
            "select ID from MODEL_ELEMENT where MODEL_TYPE='ModelRelationshipContainer' and NAME='relationships' and PARENT_ID is null",
        )[0]
        controlflow_container_id = find_one(
            cursor,
            "select ID from MODEL_ELEMENT where MODEL_TYPE='ModelRelationshipContainer' and NAME='ControlFlow' and PARENT_ID=?",
            (relationship_container_id,),
        )[0]
        association_container_id = find_one(
            cursor,
            "select ID from MODEL_ELEMENT where MODEL_TYPE='ModelRelationshipContainer' and NAME='Association' and PARENT_ID=?",
            (relationship_container_id,),
        )[0]

        root_model_definition = blob_to_text(
            find_one(cursor, "select DEFINITION from MODEL_ELEMENT where ID=?", (root_model_id,))[0]
        )
        root_child_ids = extract_child_ids(root_model_definition)

        controlflow_definition = blob_to_text(
            find_one(cursor, "select DEFINITION from MODEL_ELEMENT where ID=?", (controlflow_container_id,))[0]
        )
        controlflow_child_ids = extract_child_ids(controlflow_definition)

        association_definition = blob_to_text(
            find_one(cursor, "select DEFINITION from MODEL_ELEMENT where ID=?", (association_container_id,))[0]
        )
        association_child_ids = extract_child_ids(association_definition)

        created_at_ms = now_ms()
        created_at_s = now_s()

        with connection:
            removed_diagrams, removed_models = cleanup_legacy_content(
                cursor,
                root_model_id,
                root_child_ids,
                controlflow_child_ids,
                association_child_ids,
            )
            activity_diagram_id, _, _, _ = generate_activity_diagram(
                cursor,
                existing_ids,
                root_model_id,
                relationship_container_id,
                controlflow_container_id,
                root_child_ids,
                controlflow_child_ids,
                created_at_ms,
                created_at_s,
            )
            block_diagram_id, main_block_id, _, block_ids, block_specs = generate_block_diagram(
                cursor,
                existing_ids,
                root_model_id,
                relationship_container_id,
                association_container_id,
                root_child_ids,
                association_child_ids,
                created_at_ms,
                created_at_s,
            )
            encoder_diagram_id = generate_encoder_diagram(
                cursor,
                existing_ids,
                root_model_id,
                relationship_container_id,
                association_container_id,
                main_block_id,
                block_ids,
                block_specs,
                association_child_ids,
                created_at_ms,
                created_at_s,
            )
            module_hierarchy_diagram_id = generate_module_hierarchy_diagram(
                cursor,
                existing_ids,
                root_model_id,
                relationship_container_id,
                association_container_id,
                main_block_id,
                root_child_ids,
                association_child_ids,
                created_at_ms,
                created_at_s,
            )
            traceability_diagram_id = generate_traceability_diagram(
                cursor,
                existing_ids,
                root_model_id,
                relationship_container_id,
                controlflow_container_id,
                root_child_ids,
                controlflow_child_ids,
                created_at_ms,
                created_at_s,
            )

            cursor.execute(
                "update MODEL_ELEMENT set DEFINITION=?, AUTHOR=?, LAST_MOD_AT=? where ID=?",
                (
                    encode_text(render_root_model_definition(root_model_id, root_child_ids, created_at_ms, created_at_ms)),
                    AUTHOR,
                    created_at_s,
                    root_model_id,
                ),
            )
            cursor.execute(
                "update MODEL_ELEMENT set DEFINITION=?, AUTHOR=?, LAST_MOD_AT=? where ID=?",
                (
                    encode_text(
                        render_relationship_container_definition(
                            relationship_container_id,
                            controlflow_container_id,
                            "ControlFlow",
                            controlflow_child_ids,
                            created_at_ms,
                            created_at_ms,
                        )
                    ),
                    AUTHOR,
                    created_at_s,
                    controlflow_container_id,
                ),
            )
            cursor.execute(
                "update MODEL_ELEMENT set DEFINITION=?, AUTHOR=?, LAST_MOD_AT=? where ID=?",
                (
                    encode_text(
                        render_relationship_container_definition(
                            relationship_container_id,
                            association_container_id,
                            "Association",
                            association_child_ids,
                            created_at_ms,
                            created_at_ms,
                        )
                    ),
                    AUTHOR,
                    created_at_s,
                    association_container_id,
                ),
            )
            update_project_diagram_refs(
                cursor,
                [
                    activity_diagram_id,
                    block_diagram_id,
                    encoder_diagram_id,
                    module_hierarchy_diagram_id,
                    traceability_diagram_id,
                ],
            )
            cleanup_orphan_project_files(cursor)

        integrity = cursor.execute("pragma integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"SQLite integrity_check failed: {integrity}")
    finally:
        connection.close()

    print(f"Updated SysML diagrams in {vpp_path}")
    if removed_diagrams:
        print("Removed legacy diagrams:")
        for name in removed_diagrams:
            print(f"- {name}")
    if removed_models:
        print("Removed legacy model roots:")
        for name in removed_models:
            print(f"- {name}")
    print(f"Activity diagram: {ACTIVITY_DIAGRAM_NAME}")
    print(f"Block diagram: {BLOCK_DIAGRAM_NAME}")
    print(f"Encoder diagram: {ENCODER_DIAGRAM_NAME}")
    print(f"Module hierarchy diagram: {MODULE_HIERARCHY_DIAGRAM_NAME}")
    print(f"Traceability diagram: {TRACEABILITY_DIAGRAM_NAME}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
