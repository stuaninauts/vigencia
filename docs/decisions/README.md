# Decisões (ADRs)

Um arquivo por decisão relevante de arquitetura, stack ou processo, no formato inspirado em
[MADR](https://adr.github.io/madr/) e no ADR de Michael Nygard. Decisões não são editadas depois de aceitas:
uma decisão nova substitui a antiga e as duas se referenciam.

- Nome: `NNNN-titulo-curto.md` (numeração sequencial, sem buracos).
- Status: `proposta` → `aceita` → (`substituída por NNNN` | `descontinuada`).
- Quando criar: escolha que alguém questionaria daqui a 3 meses ("por que pgvector e não X?").

## Modelo

```markdown
# NNNN: Título

**Data:** AAAA-MM-DD · **Status:** proposta

## Contexto
O problema e as forças em jogo (restrições, requisitos, o que foi medido).

## Decisão
O que foi decidido, no imperativo.

## Alternativas consideradas
- **Opção X:** por que não.

## Consequências
O que fica mais fácil, o que fica mais difícil, riscos e quando revisitar.
```

## Índice
- [0001: Domínio do laboratório](0001-dominio.md)
- [0002: Stack inicial](0002-stack-inicial.md)
- [0003: Harness de desenvolvimento e fluxo de trabalho](0003-harness-e-fluxo.md)
