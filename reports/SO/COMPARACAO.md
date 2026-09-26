# Matriz de comparação e rastreabilidade

Data da auditoria técnica: 2026-09-23. Auditoria completa das imagens atualizada
em 2026-09-26.

Verificações executadas nesta data:

- `make -C compiler test_analysis`: aprovado; seis grupos de casos passaram e o
  artefato VPP opcional foi ignorado por ausência.
- `python3 compiler/codegen/assembler_regressions.py`: aprovado.
- `make -C compiler run_selected_10_diagnostics`: aprovado, 10/10 programas com
  saídas esperadas.

## Fontes comparadas

- Processador: `reports/processador/processadorARM_2024_2.pdf` (71 páginas,
  setembro de 2024).
- Complemento da ISA:
  `reports/processador/ImportantAdditionalText-ProcessorInformation.txt`.
- Compilador e modelo de formatação:
  `reports/compiladores/Relatorio_AOC.tex` (julho de 2025).
- Implementação corrente: `processor/Processor/`, `compiler/` e `tools/`.

Os relatórios antigos são evidência histórica. A coluna “Decisão” abaixo foi
determinada pela implementação corrente e não pela preferência entre autores.

## Matriz técnica

| Tema | Relatório do processador | Relatório de compiladores | Evidência atual | Classificação | Decisão no relatório central |
| --- | --- | --- | --- | --- | --- |
| Organização Harvard | Fundamenta e afirma ROM/RAM separadas | Mantém a afirmação | `integrated.v` instancia `InstructionMemory` e `DataMemory` separadamente | confirmado | Manter |
| Inspiração ARM/RISC | Fundamentação extensa | Síntese da fundamentação | Campo Cond, CPSR simplificado e branch/link próprios; não há compatibilidade ARM | confirmado com ressalva | Descrever como ARM-like |
| Largura da instrução | 32 bits | 32 bits | `instruction[31:0]`, montador e simulador usam 32 bits | confirmado | Manter |
| Campos da instrução | Mostra evolução de formatos | Tabela Cond/Type/Supp/Funct/Rd/Rh/Operand2 | `ControlUnit.v`, `assembler.py`, `run_machine_code.py` | confirmado | Manter a versão corrente |
| Classes de instrução | Inclui tipos históricos e versão final | Dados, memória e branch | Type `00`, `01` e `11`; `10` sem uso | confirmado | Omitir o tipo histórico de registro de estados |
| Operações da ULA | ADD, SUB, MUL, DIV e lógicas | Acrescenta IN/OUT e integração | `alu.v` implementa opcodes `0000` a `1010` | confirmado | Manter |
| Condições | Imagem inclui ALWAYS, EQ, NEQ, GT, GTEQ, LT, LTEQ, NOT | Reutiliza a imagem, mas o texto fala em Z/N | Montador aceita sete condições; `FlagVerifier.v` trata outros códigos como falso | conflitante | Excluir NOT e rejeitar a imagem antiga |
| Flags | CPSR de 4 bits, com Z/N usados | Mesma interpretação | `FlagDecoder.v` força bits 3:2 a zero e produz Z/N | confirmado | Manter com limitação explícita |
| Atualização do CPSR | Texto antigo alterna bordas | Indica atualização por sufixo S | `CPSRegister.v` escreve na borda negativa se condição e S passam | atualizado | Descrever a borda negativa atual |
| Banco de registradores | 32 registradores de 32 bits | Acrescenta convenção do compilador | `registerBank.v` possui `regBank[31:0]` e link dedicado | confirmado | Manter e distinguir `r28` do link dedicado |
| Reset do banco e flags | Não delimita completamente | Pode sugerir estado inicial controlado | Entradas de reset não zeram banco, link ou CPSR | ausente | Registrar como lacuna crítica |
| PC sequencial | Diagrama usa incremento por 4; texto usa instruções em palavras | Relatório reutiliza o diagrama | `PC_main.v` faz `instruction_address + 1` | desatualizado | Rejeitar diagrama e documentar `PC+1` |
| Branch imediato | Deslocamento relativo | Descreve PC relativo | `PC_main.v`: `PC + branch_value` quando imediato | confirmado | Manter |
| Branch por registrador | Material antigo é ambíguo sobre soma/valor | Relatório afirma destino absoluto | `PC_main.v`: `PC := branch_value`; ULA encaminha `RoValue` | atualizado | Manter sem ambiguidade |
| Branch-and-link | Introduz bit de link | Descreve link e retorno | `registerBank.v` salva `PC+1`; `ControlUnit.v` usa Funct[23]/[22] | confirmado | Manter |
| Caminho de dados | Figura MIPS adaptada e referência externa ao desenho final | Reutiliza figura histórica | `integrated.v` contém conexões diferentes da figura | desatualizado | Não copiar; manter descrição textual e exigir novo diagrama |
| Endereço da RAM | Figura histórica encaminha resultado da ULA | Texto diz endereço por registrador | `DataMemory.mem_addr` e `write_addr` recebem `ro_value` | conflitante | Descrever endereço direto por Ro |
| Profundidade da RAM | Descrição genérica | 64 palavras de 32 bits | `ADDR_WIDTH=6`, portanto 64 posições | confirmado parcialmente | Manter profundidade |
| Largura da RAM | Material antigo sugere caminho de 32 bits | Afirma 32 bits | `DataMemory.v` declara `DATA_WIDTH=64`; software modela 32 | conflitante | Registrar incompatibilidade, sem normalizar |
| Mapa pilha/globais | Não define ABI C- atual | Pilha 0–63 e dados a partir de 64 | RTL possui endereço de 6 bits; simulador mascara por 63, fazendo 64→0 | conflitante | Registrar alias e exigir novo mapa de memória |
| ROM | Arquivo `.txt` carregado na compilação | Ainda menciona `single_port_rom_init.txt` em trecho | `InstructionMemory.v` e QSF usam `modules/program.mif` | desatualizado | Corrigir para MIF 1024 × 32 |
| Clock | Relatório antigo descreve ciclo em múltiplas bordas | Resume clock/fast clock | `freqDiv.v`, `Processor.v` e módulos usam dois pulsos derivados | confirmado com risco | Descrever e registrar revisão de CDC/temporização |
| Restrições temporais | Não demonstradas | Não demonstradas | Nenhum `.sdc` localizado no projeto atual | ausente | Registrar como lacuna |
| Entrada | Módulo periférico antigo | Descreve SW e espera | `ControlUnit.v` pausa em `in` e libera em 1→0 de SW15 | atualizado | Manter comportamento atual |
| Saída | Displays e módulos de saída | Descreve `out` | `output_manager.v` e `Processor.v` expõem valor em HEX6/HEX7 | confirmado | Manter |
| Assembler | Implementação Python inicial em duas etapas | Montador com labels/expansões | `assembler.py` possui estabilização, literais e branches longos | complementar | Usar descrição atual |
| Front-end C-/Flex/Bison | Não existe no relatório de 2024 | Léxico, parser, AST, símbolos e semântica | `compiler/parser/`, `compiler/src/`, regressões | complementar | Incorporar |
| IR | Não abordada | IR de três endereços | `ir.c/h` e arquivo intermediário textual | complementar | Incorporar |
| Back-end | Não abordado além do assembler | Python, alocação, frames e spills | `codegen.py`, `constants.py`, `symbol_table.py` | complementar | Incorporar com distinção de links |
| Simulador | Testes de waveform/bancada | Simulador de máquina | `tools/run_machine_code.py` modela ISA e diagnósticos | complementar | Incorporar sem equiparar a RTL/bancada |
| Resultados de bancada | Afirma sucesso em 2024 | Reaproveita contexto | Não foi executada nova programação de placa nesta auditoria | histórico | Não alegar validação atual de placa |
| Sistema Operacional | Não existe | Não existe | Nenhum kernel, ABI de syscall, scheduler ou troca de contexto identificado | não implementado | Citar apenas como trabalho futuro |
| “Carga de preempção” | Não existe | Não fundamenta SO | É apenas uma fixture/diagnóstico; não comprova preempção | não implementado | Evitar inferência pelo nome |

## Avaliação das imagens disponíveis

Foram encontrados 35 arquivos de imagem em `reports/compiladores/` e
`reports/compiladores/Imagens/`. Todos foram abertos e avaliados
individualmente contra o código atual. “Incluída” significa que a figura foi
copiada para `reports/SO/figuras/`, possui legenda/fonte e é referenciada no
texto. Oito imagens foram aprovadas; 27 foram rejeitadas.

| # | Imagem | Verificação individual | Decisão |
| ---: | --- | --- | --- |
| 1 | `Imagens/CPSRWF.png` | Waveform sem revisão, testbench ou critério de aprovação; reset do CPSR atual continua pendente. | rejeitada |
| 2 | `Imagens/DataPathPettHenn.png` | Datapath MIPS genérico com PC+4, imediato de 16 bits e shift-left de 2. | rejeitada |
| 3 | `Imagens/DataPathSingleCycle.png` | Usa PC+4, branch adder e endereço da RAM incompatível com `integrated.v`. | rejeitada |
| 4 | `Imagens/FPGA.png` | Placa DE2-115 compatível com o dispositivo e a pinagem do QSF. | incluída como `de2-115.png` |
| 5 | `Imagens/MIPS_dataPath.png` | Datapath MIPS genérico, não a ISA ARM-like customizada. | rejeitada |
| 6 | `Imagens/Op_processamentoDados.png` | Omite IN/OUT e chama `not` de porta lógica, embora `alu.v` execute `-A`. | rejeitada |
| 7 | `Imagens/Op_processamento_versao2.png` | Inclui IN, mas omite OUT e mantém semântica incorreta para `not`. | rejeitada |
| 8 | `Imagens/Op_ramo.png` | Códigos históricos de B/BL não correspondem a `Type=11` e `Funct` atuais. | rejeitada |
| 9 | `Imagens/Op_ramo_versao2.png` | Nomes Link/LL são ambíguos e não representam as formas atuais de destino e retorno. | rejeitada |
| 10 | `Imagens/Op_registro.png` | TST/TEQ/CMP/NEG e a classe de registro de estados não existem na ISA atual. | rejeitada |
| 11 | `Imagens/Op_transferencia_versao2.png` | Store é descrito de modo ambíguo; no RTL, Ro endereça e Rh fornece o dado. | rejeitada |
| 12 | `Imagens/PCWF.png` | Sinais truncados e ausência de testbench/revisão impedem validação reproduzível. | rejeitada |
| 13 | `Imagens/UCWF1.png` | Usa nomes de sinais antigos, distintos da interface atual de `ControlUnit.v`. | rejeitada |
| 14 | `Imagens/UCWF2.png` | Continuação sem nomes dos sinais e sem contexto independente. | rejeitada |
| 15 | `Imagens/ULAControlWF.png` | Resultados conferem com `alu.v`, inclusive opcode `0111` produzindo negação aritmética; usada apenas como ilustração arquivada. | incluída como `ula-control-waveform.png` |
| 16 | `Imagens/VanNeumannXHarvard.jpg` | Comparação conceitual correta e coerente com ROM/RAM separadas. | incluída como `harvard-vs-von-neumann.jpg` |
| 17 | `Imagens/assemblerCode.png` | As 12 linhas foram aceitas novamente por `FullCode`. | incluída como `exemplo-assembly.png` |
| 18 | `Imagens/cond_field_codes.png` | Inclui condição NOT/`0111`, ausente no montador e no verificador atuais. | rejeitada |
| 19 | `Imagens/dataMemWF.png` | Sinais truncados e incapacidade de resolver a divergência 64/32 bits da RAM. | rejeitada |
| 20 | `Imagens/instSet.png` | Possui classe `Type=10`, campos de memória e branch de uma revisão antiga. | rejeitada |
| 21 | `Imagens/instSetVersion2.png` | Sugere endereço imediato de RAM, mas `integrated.v` usa diretamente `RoValue`; retorno também fica ambíguo. | rejeitada |
| 22 | `Imagens/instrMemWF.png` | Mostra endereço de 5 bits, contra os 10 bits/1024 palavras da ROM atual. | rejeitada |
| 23 | `Imagens/instructionFormats.png` | Formato ARM comercial com classes inexistentes no processador didático. | rejeitada |
| 24 | `Imagens/machineCode.png` | As 12 palavras coincidem bit a bit com a saída atual para o assembly da imagem 17. | incluída como `exemplo-codigo-maquina.png` |
| 25 | `Imagens/new_datapath_full.png.png` | A visão completa herda o roteamento incorreto revelado na parte 3: resultado da ULA como endereço da RAM. | rejeitada |
| 26 | `Imagens/new_datapath_pt1.png` | Região PC/ROM/controle isoladamente plausível, mas é fragmento de um datapath global incorreto. | rejeitada |
| 27 | `Imagens/new_datapath_pt2.png` | Região banco/CPSR isoladamente plausível, mas é fragmento do mesmo datapath incorreto. | rejeitada |
| 28 | `Imagens/new_datapath_pt3.png` | Liga resultado da ULA a `Memory Address`; o RTL liga `mem_addr`/`write_addr` a `ro_value`. | rejeitada |
| 29 | `Imagens/regBankWF.png` | Não distingue adequadamente clock e fast clock e não possui teste autochecking associado. | rejeitada |
| 30 | `Imagens/registerBank_verilog.png` | Mostra leituras por `assign`; o RTL atual registra leituras em `posedge fast_clock`. | rejeitada |
| 31 | `Imagens/waveform.jpg` | Simulação salva em julho de 2025, sem programa, ROM e testbench reproduzíveis. | rejeitada |
| 32 | `Diagrama Interno - Codificador Binário.jpg` | Campos e condições conferem; encoders são conceituais e a lista de funções não é exaustiva. | incluída como `codificador-binario.jpg` |
| 33 | `Diagrama de Atividades - Fluxo de Compilação C- para Código Binário ARM Simplificado.jpg` | Pipeline ponta a ponta confere; raias são responsabilidades lógicas. | incluída como `fluxo-compilacao-cminus.jpg` |
| 34 | `Diagrama de Blocos - Arquitetura Interna do Compilador.jpg` | Modela blocos como módulos independentes e aponta saída antiga `single_port_rom_init.txt`. | rejeitada |
| 35 | `Diagrama de Blocos — Hierarquia dos Módulos do Compilador.jpg` | Arquivos, tipos, funções e constantes conferem com a árvore atual. | incluída como `hierarquia-modulos-compilador.jpg` |

## Lacunas prioritárias

1. Corrigir e validar a largura da RAM.
2. Criar um diagrama atual do datapath a partir de `integrated.v`.
3. Definir reset arquitetural completo.
4. Revisar clocks derivados, CDC e restrições SDC.
5. Criar testbenches autochecking do processador integrado.
6. Executar síntese Quartus e registrar inferência, recursos e timing.
7. Revalidar em placa antes de declarar resultados atuais de FPGA.
8. Especificar as primitivas arquiteturais necessárias ao SO antes de implementar
   kernel, escalonamento ou preempção.
