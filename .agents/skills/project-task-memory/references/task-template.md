# Modelo de tarefa persistente

Crie o arquivo com esta estrutura e remova seções sem utilidade real:

```markdown
---
title: Título curto
status: proposed
created: AAAA-MM-DD
last_updated: AAAA-MM-DD
---

# Título curto

## Objetivo

Resultado observável desejado.

## Critérios de aceite

- Critério verificável.

## Contexto confirmado

- Fato confirmado no código, teste ou documentação canônica.

## Decisões

- Decisão e motivo que precisa sobreviver à sessão.

## Progresso

- Entrega ou verificação concluída, com caminho/comando quando útil.

## Bloqueios

- Bloqueio concreto e o que é necessário para removê-lo.

## Próximo passo

Uma ação específica que permita retomar sem reconstruir todo o contexto.
```

Não armazene segredos, tokens, dados pessoais, grandes logs ou conteúdo que já
tenha uma fonte canônica no repositório.
