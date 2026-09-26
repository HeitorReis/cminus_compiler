# Verificação por alcance

Execute comandos a partir da raiz do repositório, salvo indicação contrária.
Antes e depois, observe `git status --short`, pois vários fluxos atualizam
artefatos em `compiler/docs/generated/`. Não descarte alterações do usuário para
limpar resultados.

## Seleção mínima

- Mudança em lexer, parser, AST, tabela de símbolos, semântica ou IR:
  `make -C compiler test_analysis`.
- Build isolado do front-end: `make -C compiler bin/c-c`.
- Mudança no assembler: `python3 compiler/codegen/assembler_regressions.py`.
- Mudança integrada no back-end: compile uma fixture focada com
  `make -C compiler run TEST=<nome>` e inspecione os diagnósticos relevantes.
- Mudança na codificação ou semântica de instruções: além do teste focado, rode
  o simulador com `python3 tools/run_machine_code.py <arquivo> --trace`.
- Mudança transversal na pipeline: `make -C compiler run_all complete`.
- Mudança nos dez programas usados no FPGA, ROM ou integração correspondente:
  `make -C compiler run_selected_10_diagnostics`.
- Mudança na geração de MIF: gere os casos com `make -C compiler generate_mif`
  e valide tamanho, largura e programa selecionado antes de envolver Quartus.

## Regras de escalonamento

- Comece por uma fixture pequena que isole o defeito.
- Rode regressão do estágio modificado antes da regressão ponta a ponta.
- Uma mudança de contrato só está validada quando pelo menos um produtor e um
  consumidor foram exercitados juntos.
- Compilação Quartus, programação da placa e interação física são validações
  próprias. Não alegue que foram executadas quando apenas o simulador Python foi
  usado.
- Se uma ferramenta opcional não existir, registre o teste como não executado e
  continue com as verificações independentes disponíveis.

## Evidência na entrega

Informe o comando exato, código de saída e resumo do que ele prova. Separe
falhas introduzidas pela mudança de falhas preexistentes ou limitações do
ambiente.
