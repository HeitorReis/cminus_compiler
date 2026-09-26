# Relatório inicial do próximo Lab

Este diretório contém o relatório central que consolida o estado atual do
processador ARM-like e do compilador C-. A formatação segue
`reports/compiladores/Relatorio_AOC.tex`.

## Arquivos

- `main.tex`: documento principal.
- `referencias.bib`: referências efetivamente citadas.
- `COMPARACAO.md`: matriz de rastreabilidade entre os relatórios antigos e a
  implementação atual.
- `figuras/de2-115.png`: imagem histórica reutilizada após confirmação de
  compatibilidade com a placa e o dispositivo configurados no QSF.
- `figuras/fluxo-compilacao-cminus.jpg`: fluxo ponta a ponta do compilador,
  validado como visão de responsabilidades lógicas.
- `figuras/hierarquia-modulos-compilador.jpg`: hierarquia de arquivos e
  estruturas do front-end C e do back-end Python.
- `figuras/codificador-binario.jpg`: decomposição funcional dos campos
  codificados pelo montador atual.
- `figuras/harvard-vs-von-neumann.jpg`: comparação conceitual das organizações
  de memória.
- `figuras/ula-control-waveform.png`: waveform histórica da ULA, conferida
  contra a semântica combinacional atual e usada apenas como ilustração.
- `figuras/exemplo-assembly.png` e `figuras/exemplo-codigo-maquina.png`: par
  cuja tradução foi reproduzida com o montador atual.

As 35 imagens encontradas nas duas pastas do relatório de compiladores foram
avaliadas individualmente; oito foram incorporadas. A decisão e a justificativa
para cada arquivo estão em `COMPARACAO.md`. Diagramas históricos de ISA e
datapath continuam excluídos por divergirem da implementação atual. A ausência
de um diagrama atual do datapath permanece registrada como lacuna.

## Compilação

Com TeX Live, `abntex2`, `abntex2cite` e `latexmk` instalados:

```sh
cd reports/SO
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Alternativa manual:

```sh
cd reports/SO
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Em 2026-09-26, o documento foi compilado e validado com o TeX Live 2026
instalado em `D:\ProgramFiles\texlive\2026`. A saída gerada é `main.pdf`.
