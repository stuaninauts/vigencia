# Experimentos

Cada experimento muda **uma** variável em relação ao baseline e é medido no mesmo golden set. O vencedor vira o
baseline do próximo. Card a partir de [`TEMPLATE.md`](TEMPLATE.md), nome `NNNN-titulo-curto.md`.

- Rodar sempre no split `dev` enquanto ajusta; o split `test` só para o número final do experimento.
- Registrar config (arquivo ou hash do commit), métricas, latência e custo. Resultado negativo também é registrado.
- Experimento tem tempo limite declarado; ao estourar, registre o que se sabe e encerre.

## Índice
| # | Variável | Resultado | Decisão |
|---|---|---|---|
| [0001](0001-baseline-ingenuo.md) | baseline ingênuo (chunk fixo, só vetorial) | recall@5 0,61 · MRR 0,45 (retrieval, 20 perguntas) | geração pendente |
| [0002](0002-tamanho-do-chunk.md) | tamanho do chunk: 800, 1500, 3000 | recall 0,50 / 0,61 / 0,56 (mesmo volume de texto) | mantém 1500; falhas são estruturais |
