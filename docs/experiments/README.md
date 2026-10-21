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
| [0003](0003-busca-lexical-hibrida.md) | busca: ts_rank, BM25, híbrida (RRF) | BM25 0,67 · ts_rank 0,06-0,11 · híbrida 0,61-0,67 | híbrida BM25 + RRF k 5 vira baseline |
| [0004](0004-fusao.md) | fusão: peso do BM25, roteamento por código | roteamento 0,67 · MRR 0,55; peso não muda o recall | roteamento vira baseline |
| [0005](0005-reranker.md) | reranker bge-reranker-v2-m3 sobre 20 e 50 candidatos | 0,83 / 0,89 · MRR 0,69 / 0,70 · p50 328 / 779 ms | rerank-20 vira baseline |
| [0006](0006-cabecalho-no-chunk.md) | cabeçalho de NT, versão e página no chunk | com reranker 0,83 para 0,89 · MRR 0,71; diff 0 para 0,50 | cabecalho-rerank-20 vira baseline |
