---
title: Criar relatório técnico inicial do próximo Lab de SO
status: done
created: 2026-09-23
last_updated: 2026-09-26
---

# Criar relatório técnico inicial do próximo Lab de SO

## Objetivo

Produzir, em uma nova pasta `reports/SO/`, um relatório técnico-científico central
em LaTeX que sirva como ponto inicial do próximo Laboratório de Sistemas
Operacionais. O documento deve consolidar as informações úteis dos relatórios
anteriores do processador e do compilador, mas descrever a implementação atual
do repositório e não perpetuar dados antigos que ficaram incorretos após as
mudanças no processador.

O trabalho tem duas etapas obrigatórias:

1. comparar os relatórios anteriores entre si e contra o código atual, gerando
   um diagnóstico de conteúdo coincidente, complementar, conflitante,
   desatualizado e ausente;
2. criar o novo projeto LaTeX em `reports/SO/`, aproveitando o modelo e os recursos
   visuais antigos somente quando forem compatíveis com o estado atual.

## Fontes e precedência

- Relatório do processador a comparar:
  `reports/processador/processadorARM_2024_2.pdf`, apoiado pelo complemento
  `reports/processador/ImportantAdditionalText-ProcessorInformation.txt`.
- Relatório do compilador a comparar e modelo de formatação obrigatório:
  `reports/compiladores/Relatorio_AOC.tex` e seus recursos adjacentes.
- Modelo LaTeX histórico, bibliografia e imagens disponíveis:
  `reference/Relatório_Laboratório_de_compiladores/`.
- Outros anexos históricos potencialmente úteis:
  `reference/zRelatorios/`.
- Fontes de verdade técnicas: código, testes, configuração e artefatos atuais
  em `compiler/`, `processor/` e `tools/`.
- A pasta `reference/` pode ser consultada nesta tarefa porque o usuário pediu
  explicitamente a comparação e o reaproveitamento do modelo/imagens. Ela
  continua sendo material histórico, somente leitura, e nunca prevalece sobre
  o código atual.

Ordem de precedência em caso de divergência:

1. comportamento atual comprovado por código e testes;
2. configuração atual do processador e da pipeline;
3. documentação técnica atual compatível com o código;
4. relatórios e recursos históricos, usados apenas como evidência contextual ou
   referência de apresentação.

## Escopo da análise comparativa

- Inventariar a estrutura, capítulos, conceitos, diagramas, tabelas,
  experimentos e alegações técnicas dos dois relatórios.
- Construir uma matriz de comparação que classifique cada tópico como:
  `confirmado`, `complementar`, `conflitante`, `desatualizado`, `ausente no
  relatório novo` ou `não implementado`.
- Conferir no projeto atual, no mínimo:
  - arquitetura geral e integração compilador-processador;
  - conjunto e codificação de instruções;
  - registradores e convenções de uso;
  - unidade de controle;
  - caminho de dados;
  - memórias de instruções e dados;
  - entrada, saída e periféricos;
  - branches, chamadas, retorno e link;
  - interrupções, preempção ou mecanismos correlatos, se existirem;
  - fluxo do compilador: léxico, sintático, AST, semântica, IR, geração de
    assembly, montagem e código de máquina;
  - métodos de teste, simulação, síntese e validação existentes.
- Para cada informação do relatório antigo do processador, localizar evidência
  atual antes de aceitá-la. Ausência de evidência deve ser registrada como
  lacuna, não como confirmação.
- Identificar quais imagens antigas ainda representam o hardware atual. Imagens
  de arquitetura, caminho de dados, controle ou temporização não podem ser
  reutilizadas só por estarem disponíveis.
- Registrar lacunas estruturais e de fundamentação. Exemplo obrigatório: se o
  novo documento precisar de um caminho de dados e não existir diagrama atual
  válido, registrar a necessidade de produzir um novo diagrama; não copiar o
  caminho de dados histórico.

## Escopo do novo relatório

- Criar um projeto LaTeX autocontido dentro de `reports/SO/`, com arquivo raiz claro,
  bibliografia e subpastas organizadas para figuras e anexos.
- Reutilizar a mesma formatação de
  `reports/compiladores/Relatorio_AOC.tex`: classe `abntex2`, preâmbulo,
  tipografia, margens, capa, folha de rosto, sumário, hierarquia visual,
  figuras, tabelas e referências. Não criar um estilo paralelo, mas também não
  importar automaticamente texto técnico antigo.
- Consolidar toda informação dos dois relatórios que tenha sido validada contra
  o projeto atual.
- Quando um tópico antigo estiver desatualizado, substituí-lo por uma descrição
  fundamentada na implementação atual. Se não houver evidência suficiente,
  inserir uma lacuna/TODO explícita em vez de inventar ou copiar a versão antiga.
- Distinguir claramente arquitetura atual, método de implementação, resultados
  verificados e trabalho futuro.
- Não escrever seções factuais sobre o Sistema Operacional futuro. Conceitos,
  escalonamento, processos, chamadas de sistema, gerenciamento de memória,
  sistema de arquivos e demais funcionalidades de SO só podem aparecer como
  escopo futuro ou requisitos ainda não implementados, nunca como realizações.
- Não inventar citações, medições, resultados experimentais, diagramas,
  funcionalidades ou decisões arquiteturais.
- Copiar para `reports/SO/` apenas os recursos históricos realmente usados pelo novo
  `.tex`; não mover nem reorganizar a pasta `reference/`.

## Entregáveis

- `reports/SO/`: novo projeto do relatório, autocontido e compilável.
- Documento de comparação/rastreabilidade dentro de `reports/SO/` contendo, para cada
  tema relevante, a origem histórica, a evidência atual, a classificação e a
  decisão de incorporar, atualizar, omitir ou marcar como pendente.
- Fonte LaTeX principal e arquivos auxiliares autorais necessários.
- Bibliografia com apenas referências realmente citadas e verificáveis.
- Figuras antigas aprovadas após validação e, quando necessário, novas figuras
  produzidas a partir da arquitetura atual.
- PDF compilado do relatório, quando a toolchain LaTeX estiver disponível.
- Instruções curtas e reproduzíveis de compilação.

## Critérios de aceite

- A pasta `reports/SO/` existe sem retirar relatórios ou recursos de `reference/`.
- Os dois relatórios indicados foram comparados entre si e contra a
  implementação atual.
- Existe rastreabilidade explícita entre afirmações técnicas do novo relatório e
  suas evidências no repositório ou referências bibliográficas.
- Nenhuma descrição desatualizada do processador foi copiada como se fosse
  atual.
- Lacunas como um caminho de dados ausente são declaradas e não preenchidas com
  diagramas históricos incorretos.
- O relatório cobre compilador, ISA, processador, integração e validação no
  nível permitido pelas evidências atuais.
- Funcionalidades de SO ainda inexistentes não são apresentadas como
  implementadas.
- Todas as imagens incluídas foram individualmente verificadas contra o projeto
  atual e possuem legenda, fonte e referência no texto.
- O projeto LaTeX não depende de caminhos externos a `reports/SO/` para compilar.
- A formatação do novo documento corresponde à do relatório existente em
  `reports/compiladores/Relatorio_AOC.tex`, salvo alterações estritamente
  necessárias para metadados e conteúdo.
- A compilação é executada com a engine adequada ao modelo, quando disponível;
  o PDF abre corretamente e não possui referências ou citações não resolvidas.
- Se a toolchain necessária não estiver disponível, isso é documentado junto
  com o comando exato que deverá ser executado posteriormente.
- A documentação da estrutura do repositório é atualizada caso `reports/SO/` se torne
  uma parte canônica do projeto.

## Decisões

- O código atual é a fonte de verdade; relatórios antigos não são especificação.
- O acesso a `reference/` nesta tarefa é deliberado, limitado aos relatórios,
  modelo, bibliografia e imagens necessários e deve permanecer somente leitura.
- O novo relatório deve iniciar o próximo Lab sem alegar que o SO já existe.
- Reaproveitamento visual e reaproveitamento técnico são decisões separadas:
  uma imagem ou trecho só entra após validação semântica.
- Conteúdo ausente deve permanecer como lacuna explícita até que possa ser
  derivado ou produzido corretamente a partir da implementação atual.
- `reports/SO/` é uma pasta nova para a entrega; não é uma transferência dos relatórios de
  `reference/`.
- O relatório de compiladores em `reports/compiladores/Relatorio_AOC.tex` é o
  modelo autoritativo de formatação do novo documento.

## Plano de execução

1. Ler as skills aplicáveis de desenvolvimento do compilador, LaTeX e, quando
   necessário, FPGA/Verilog antes de iniciar mudanças.
2. Inspecionar o estado do Git e preservar alterações existentes.
3. Extrair texto e estrutura dos dois relatórios sem modificar `reference/`.
4. Mapear cada afirmação técnica para arquivos, módulos, testes ou configurações
   atuais.
5. Produzir a matriz de comparação e a lista priorizada de lacunas.
6. Definir o sumário do novo relatório a partir apenas dos tópicos confirmados e
   das lacunas explicitamente identificadas.
7. Criar `reports/SO/` e adaptar o modelo LaTeX, trazendo somente os recursos aprovados.
8. Redigir o relatório central com rastreabilidade e marcações de trabalho
   futuro para o SO ainda inexistente.
9. Compilar e revisar PDF, logs, referências, citações, figuras e
   autocontenção.
10. Executar uma revisão final contra o código atual e registrar as verificações
    nesta tarefa persistente.

## Progresso

- Tarefa criada e escopo inicial registrado em 2026-09-23.
- Execução iniciada em 2026-09-23.
- Relatório do processador (71 páginas), complemento da ISA e relatório LaTeX
  de compiladores comparados contra o RTL, QSF, compilador, montador e simulador
  atuais.
- Matriz de rastreabilidade criada em `reports/SO/COMPARACAO.md`, incluindo avaliação
  individual das imagens históricas e lacunas para o próximo Lab.
- Projeto autocontido criado em `reports/SO/`, com `main.tex`, `referencias.bib`,
  `README.md` e recursos aprovados em `figuras/`.
- Formatação de `reports/compiladores/Relatorio_AOC.tex` preservada: classe
  `abntex2`, preâmbulo, capa, folha de rosto, estilos, listas, sumário,
  referências e parâmetros de parágrafo.
- Divergências materiais documentadas: diagrama de datapath antigo, condição
  NOT não suportada, ROM MIF, largura 64/32 da RAM, alias entre pilha e globais,
  resets incompletos e ausência de restrições SDC.
- `make -C compiler test_analysis`: aprovado; casos válidos e de erro passaram,
  com VPP opcional ignorado por ausência.
- `python3 compiler/codegen/assembler_regressions.py`: aprovado.
- `make -C compiler run_selected_10_diagnostics`: aprovado, 10/10 saídas
  esperadas.
- Verificação estrutural local do LaTeX: ambientes balanceados, citações,
  referências e imagem resolvidas; `git diff --check` sem erros.
- Estrutura canônica atualizada em `AGENTS.md` e
  `compiler/docs/hierarquia.txt`.
- Localização corrigida por orientação do usuário: a entrega reside em
  `reports/SO/`; a pasta raiz `SO/` não existe mais.
- `main.pdf` compilado com sucesso em 2026-09-25 usando TeX Live 2026 em
  `D:\ProgramFiles\texlive\2026`; o documento final possui 20 páginas, com
  bibliografia, citações e referências resolvidas.
- Em 2026-09-26, o conteúdo do compilador foi ampliado com fundamentação sobre
  lexer, parser, AST, símbolos, semântica, IR, frames, alocação, montagem e
  codificação. Três diagramas do relatório de compiladores foram validados,
  incorporados e contextualizados; figuras antigas de datapath, ISA e waveform
  continuaram excluídas por incompatibilidade técnica.
- O PDF ampliado foi recompilado com sucesso, passou de 20 para 27 páginas e
  manteve citações, referências e margens resolvidas. As três novas figuras
  foram inspecionadas em suas páginas paisagem.
- Auditoria exaustiva concluída em 2026-09-26: os 35 arquivos de imagem em
  `reports/compiladores/` e `reports/compiladores/Imagens/` foram abertos e
  confrontados individualmente com o código atual. Oito foram aprovados e 27
  rejeitados, com decisão nominal registrada em `reports/SO/COMPARACAO.md`.
- Quatro recursos adicionais foram incorporados: comparação Harvard/von
  Neumann, waveform compatível da ULA e o par assembly/código de máquina cuja
  tradução foi reproduzida bit a bit pelo montador atual.
- O PDF resultante possui 30 páginas e oito imagens aprovadas, sem referências
  ou citações indefinidas e sem caixas ultrapassando as margens.

## Bloqueios

- Nenhum bloqueio.

## Próximo passo

Antes de implementar o Sistema Operacional, priorizar as lacunas listadas em
`reports/SO/COMPARACAO.md`: largura e mapa da RAM, reset arquitetural, novo diagrama de
datapath, clock/CDC/SDC e testbenches autochecking do processador integrado.
