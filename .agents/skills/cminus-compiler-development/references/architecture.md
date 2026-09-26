# Arquitetura e contratos

## Pipeline

1. `compiler/main.c` coordena o front-end.
2. `compiler/parser/lexer.l` produz tokens; `compiler/parser/parser.y` reconhece
   a gramática e constrói a AST.
3. `compiler/src/` mantém AST, estado de análise, tabela de símbolos, escopos,
   análise semântica e geração de IR.
4. `compiler/docs/generated/intermediate/semantic/ir/generated_IR.txt` é o
   contrato textual entre o front-end C e o back-end Python.
5. `compiler/codegen/codegen.py` e auxiliares transformam IR em assembly.
6. `compiler/codegen/assembler.py` resolve rótulos, codifica instruções e gera
   palavras de máquina.
7. `tools/run_machine_code.py` simula o comportamento atual do processador para
   diagnóstico; o RTL real fica sob `processor/`.

## Donos por tipo de mudança

- Tokens, comentários e literais: `compiler/parser/lexer.l`.
- Gramática, precedência e construção inicial da AST:
  `compiler/parser/parser.y`.
- Forma e impressão da AST: `compiler/src/syntax_tree.c` e `.h`.
- Declarações, escopos, tipos e chamadas: `compiler/src/semantic.c`, tabela de
  símbolos e estado de análise em `compiler/src/`.
- Forma e emissão de IR: `compiler/src/ir.c`, `.h` e pontos emissores na análise
  semântica.
- Lowering, registradores e assembly: `compiler/codegen/`.
- Campos binários, labels e validação de instrução:
  `compiler/codegen/assembler.py` e `compiler/codegen/constants.py`.
- Semântica executável de código de máquina: `tools/run_machine_code.py` e RTL
  correspondente sob `processor/`.
- Geração/seleção de ROM: `tools/generate_mif.py`, alvos no
  `compiler/Makefile` e arquivos MIF do processador.

## Interfaces que exigem mudança coordenada

- Alterar a sintaxe pode exigir lexer, parser, AST, semântica e fixtures.
- Alterar uma operação de IR pode exigir emissor C, parser/lowering Python e
  testes ponta a ponta.
- Alterar assembly ou encoding pode exigir gerador, assembler, simulador,
  documentação de campos e RTL.
- Alterar caminhos de artefatos requer revisar `compiler/Makefile`, scripts em
  `tools/`, documentação e configurações do editor.

## Fontes e produtos

São fontes: arquivos sob `compiler/parser/`, `compiler/src/`,
`compiler/codegen/`, scripts em `tools/`, fixtures em
`compiler/docs/input/cminus/` e RTL mantido em `processor/`.

São produtos ou diagnósticos: `compiler/build/`, `compiler/bin/`,
`compiler/parser.output`, `compiler/parser.gv` e
`compiler/docs/generated/`. Use-os para observar resultados, não como local
primário de correção.
