---
name: cminus-compiler-development
description: Desenvolver, depurar, revisar e validar o compilador C-minus deste repositório, incluindo Flex/Bison, AST, análise semântica, IR, back-end Python, assembler, código de máquina e integração com o processador FPGA.
---

# Desenvolvimento do compilador C-minus

Trabalhe a partir da etapa responsável pelo comportamento observado e preserve
os contratos entre as etapas da pipeline.

## Contexto seletivo

- Leia [references/architecture.md](references/architecture.md) ao localizar a
  responsabilidade de uma mudança, atravessar módulos ou alterar formatos entre
  etapas.
- Leia [references/verification.md](references/verification.md) antes de escolher
  comandos de build, regressão ou validação.
- Não leia a pasta `reference/` da raiz. Ela é material legado/externo e só pode
  ser consultada nas condições restritas definidas no `AGENTS.md`.

## Fluxo de trabalho

1. Reproduza ou delimite o comportamento na menor etapa possível.
2. Identifique o contrato de entrada e saída afetado antes de editar.
3. Corrija a fonte editável; trate `build/`, `bin/`, `parser.output`, `parser.gv`
   e `compiler/docs/generated/` como produtos da pipeline.
4. Mantenha parsing, semântica, geração de IR, lowering e codificação separados;
   não esconda regra semântica no parser ou no assembler por conveniência.
5. Ao alterar uma instrução ou formato, verifique produtor e consumidor:
   gerador de IR, back-end, assembler, simulador e RTL conforme o alcance real.
6. Adicione ou ajuste um caso de regressão que falhe antes da correção e passe
   depois, quando o comportamento for testável.
7. Execute a matriz mínima de verificação e relate comandos, resultados e
   limitações.

## Invariantes

- Erros léxicos, sintáticos ou semânticos não devem produzir IR válido para o
  back-end.
- Diagnósticos devem manter localização e causa úteis sempre que a etapa tiver
  essa informação.
- A AST representa a semântica da linguagem; detalhes artificiais do parser não
  devem vazar sem necessidade.
- Propriedade e tempo de vida de nós, símbolos e strings precisam permanecer
  explícitos no código C.
- O formato textual de IR é uma interface entre processos. Mudanças incompatíveis
  exigem atualização coordenada e regressão ponta a ponta.
- A codificação binária deve concordar entre assembler, simulador e RTL, não
  apenas produzir uma palavra de 32 bits sintaticamente válida.
