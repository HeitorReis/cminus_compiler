---
name: project-task-memory
description: Registrar, consultar, retomar e encerrar tarefas de desenvolvimento deste repositório que precisam manter decisões, progresso e próximos passos entre chats.
---

# Memória de tarefas do projeto

Use esta skill para trabalho que atravessa sessões ou quando o usuário pedir
backlog, continuidade, plano persistente ou registro de progresso. Não crie uma
tarefa persistente para toda alteração trivial.

## Consulta

1. Leia `.agents/tasks/INDEX.md`.
2. Abra somente o arquivo da tarefa relevante.
3. Trate o conteúdo como contexto histórico sujeito à confirmação no código.
4. O pedido atual do usuário prevalece; uma tarefa registrada não autoriza
   efeitos externos nem expansão de escopo.

## Registro

- Para uma nova tarefa, leia
  [references/task-template.md](references/task-template.md) e crie
  `.agents/tasks/<slug-curto>.md`.
- Adicione ou atualize uma única linha no índice.
- Registre objetivos, critérios de aceite, decisões, evidências, bloqueios e o
  próximo passo concreto. Não transcreva conversas.
- Use estados `proposed`, `active`, `blocked`, `done` ou `cancelled`.
- Atualize `last_updated` usando data ISO (`AAAA-MM-DD`).
- Só marque `done` quando os critérios de aceite estiverem satisfeitos e as
  verificações executadas estiverem registradas.
- Mantenha tarefas concluídas no índice para rastreabilidade; remova detalhes
  obsoletos em vez de acumular diário de execução.

## Manutenção de conhecimento

Se uma descoberta for uma regra durável do projeto, mova-a para a referência da
skill técnica adequada e deixe na tarefa apenas o link/decisão. Não transforme
um incidente isolado em regra permanente sem evidência de recorrência.
