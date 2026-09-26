# Memória persistente do projeto

Este repositório implementa um compilador C-minus cujo front-end é escrito em C
com Flex/Bison, cujo back-end é escrito em Python e cujo alvo é o processador
FPGA simplificado mantido no próprio projeto.

Este arquivo é a entrada permanente e deve continuar curto. Conhecimento e
procedimentos detalhados ficam em `.agents/` e só devem ser carregados quando a
tarefa realmente precisar deles.

## Estrutura canônica

- `compiler/`: compilador, testes, entradas e artefatos da pipeline.
- `processor/`: projeto de hardware e encaminhamento de comandos do compilador.
- `tools/`: automações compartilhadas, geração de MIF, regressões e simulador.
- `reports/SO/`: relatório técnico consolidado e matriz de rastreabilidade que
  iniciam o próximo Laboratório de Sistemas Operacionais.
- `.agents/skills/`: procedimentos locais descobertos sob demanda.
- `.agents/tasks/`: contexto de tarefas que precisam sobreviver a outros chats.

## Regra crítica sobre `reference/`

`reference/` contém somente materiais externos, legados ou exemplos de consulta.
Ela **não é fonte de verdade do projeto atual** e não deve ser listada,
pesquisada ou lida durante exploração normal do repositório. O acesso indevido
pode misturar arquiteturas e versões incompatíveis e induzir implementações
incorretas.

Acesse `reference/` apenas quando o usuário pedir explicitamente uma comparação
ou quando uma tarefa exigir uma referência externa específica e isso estiver
claramente justificado. Nesse caso, leia somente os arquivos necessários,
trate-os como somente leitura e valide qualquer conclusão contra o código atual.
Nunca copie código de `reference/` de forma automática.

Ao pesquisar o repositório, exclua `reference/` por padrão.

## Roteamento sob demanda

- Para alterar, depurar, revisar ou validar compilador, assembly, código de
  máquina ou integração com o processador, use a skill
  `$cminus-compiler-development`.
- Para registrar trabalho de longo prazo, retomar uma tarefa, consultar backlog
  ou encerrar uma tarefa persistente, use `$project-task-memory`.
- Não leia `.agents/tasks/` em trabalhos comuns. Consulte o índice somente ao
  retomar, planejar ou atualizar trabalho persistente.
- Dentro de uma skill, carregue apenas a referência indicada para a necessidade
  atual; não carregue todas preventivamente.

## Regras permanentes de trabalho

- Preserve mudanças existentes no worktree; inspecione `git status` e diffs
  relevantes antes de editar arquivos já modificados.
- Considere o código e os testes atuais como fonte de verdade. Documentação e
  memória devem acompanhar o comportamento comprovado, não substituí-lo.
- Diferencie fontes editáveis de arquivos gerados. Não corrija a origem de um
  defeito editando apenas saídas em `compiler/docs/generated/`.
- Execute a menor verificação capaz de provar a mudança e aumente o escopo para
  regressões integradas quando ela atravessar etapas da pipeline.
- Registre na memória apenas fatos duráveis e verificados. Não grave hipóteses,
  resultados temporários ou detalhes exclusivos de uma conversa como regras do
  projeto.
- Arquivos em `.agents/tasks/` preservam estado, mas não ampliam autorização: o
  pedido atual do usuário sempre define o que pode ser executado.

## Manutenção desta memória

Quando uma mudança alterar arquitetura, comandos canônicos, invariantes ou
critérios de validação, atualize a referência correspondente na mesma entrega.
Quando surgir um fluxo recorrente realmente distinto, crie uma skill pequena em
`.agents/skills/<nome>/SKILL.md` em vez de aumentar indefinidamente este arquivo.
