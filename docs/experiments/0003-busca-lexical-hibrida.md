# 0003: Busca lexical e híbrida

**Data:** 2026-10-19 · **Status:** concluído (só retrieval) · **Tempo limite:** 1 dia

## Hipótese
A busca lexical acerta identificadores exatos (códigos de rejeição, IDs de regra) que a vetorial erra; a vetorial
acerta paráfrases. A híbrida soma as duas.

## Setup
- **Baseline:** 0001 (vetorial, `bge-m3`, chunks de 1500 caracteres). Todas as variantes usam o mesmo índice
  (`tamanho-fixo-1500-374d73788e62`); só muda a seção `[busca]` da config.
- **Variáveis:**
  - método lexical: ranking nativo do Postgres (`ts_rank_cd`, configs `fts-*`) e BM25 (k1 = 1,2, b = 0,75) calculado
    sobre os termos do Postgres (configs `bm25-*`);
  - dicionário do Postgres: `simple` (sem radical), `portuguese` (radical, sem stopwords) e `pt_unaccent`
    (`portuguese` + `unaccent`, porque a SEFAZ manda as mensagens sem acento);
  - híbrida: vetorial + BM25 fundidas por Reciprocal Rank Fusion, 50 candidatos de cada lista, `rrf_k` 60, 20 e 5.
- **Golden set:** `dev`, 20 perguntas revisadas (18 com citação). Latência medida por pergunta, depois de aquecer.

## Resultados
| Config | Método | recall@5 | MRR | reais | sintéticas | p50 | p95 |
|---|---|---|---|---|---|---|---|
| `fts-simple` | ts_rank_cd | 0,06 | 0,03 | 0,07 | 0,00 | 24 ms | 102 ms |
| `fts-portuguese` | ts_rank_cd | 0,11 | 0,03 | 0,14 | 0,00 | 9 ms | 21 ms |
| `fts-pt-unaccent` | ts_rank_cd | 0,06 | 0,01 | 0,07 | 0,00 | 11 ms | 21 ms |
| `bm25-simple` | BM25 | 0,56 | 0,44 | 0,64 | 0,25 | 4 ms | 5 ms |
| **`bm25-portuguese`** | BM25 | **0,67** | **0,50** | 0,71 | 0,50 | 3 ms | 4 ms |
| `bm25-pt-unaccent` | BM25 | 0,56 | 0,49 | 0,64 | 0,25 | 3 ms | 5 ms |
| `baseline` | vetorial | 0,61 | 0,45 | 0,71 | 0,25 | 14 ms | 151 ms |
| `hibrida-portuguese` | RRF, k 60 | 0,61 | 0,45 | 0,71 | 0,25 | 19 ms | 151 ms |
| `hibrida-pt-unaccent` | RRF, k 60 | 0,61 | 0,49 | 0,71 | 0,25 | 19 ms | 141 ms |
| `hibrida-portuguese-rrf20` | RRF, k 20 | 0,61 | 0,45 | 0,71 | 0,25 | 18 ms | 147 ms |
| **`hibrida-portuguese-rrf5`** | RRF, k 5 | **0,67** | 0,48 | 0,71 | 0,50 | 19 ms | 148 ms |

Posição do acerto por pergunta (`-` é falha no top-5):

| Pergunta | vetorial | BM25 portuguese | híbrida (k 60) |
|---|---|---|---|
| `temporal-01` (rejeição 1115) | - | 5 | - |
| `regra-01` (mensagem da SEFAZ sem acento) | 5 | - | - |
| `regra-03` (rejeição 1201) | - | 1 | 5 |
| `regra-05` (paráfrase da base de cálculo) | 2 | - | 3 |
| `regra-06` (rejeição 1011) | - | 1 | - |
| `diff-01`, `diff-02`, `campo-01`, `multihop-02` | - | - | - |

## Análise
- **`ts_rank_cd` não é BM25.** O ranking nativo do Postgres não tem IDF: "nota" e "grupo" pesam tanto quanto "1115".
  Sobre os mesmos termos, o BM25 sai de 0,06-0,11 para 0,56-0,67 de recall. Usar o full-text do Postgres como
  "busca lexical" de um RAG sem trocar o ranking é o erro mais caro deste experimento.
- **Lexical e vetorial são complementares.** O BM25 acerta os códigos de rejeição (1115, 1201, 1011) que a vetorial
  erra; a vetorial acerta a mensagem sem acento e a paráfrase. A união dos acertos daria 14 de 18 (0,78).
- **A fusão RRF desperdiça essa complementaridade.** Com `rrf_k` 60, um chunk em 1º lugar só no BM25 soma 1/61 e perde
  para chunks medianos nas duas listas (2/70). Com `rrf_k` 5 a híbrida empata com o BM25 sozinho (0,67), ainda longe
  de 0,78. Ressalva: `rrf_k` foi ajustado no split `dev` com 18 perguntas; risco de sobreajuste.
- **`unaccent` é faca de dois gumes.** Ajuda a mensagem da SEFAZ sem acento (na híbrida, `regra-01` passa a acertar),
  mas piora o BM25 sozinho (0,67 para 0,56). Hipótese a testar: juntar formas com e sem acento muda o IDF dos termos.
- **Latência não é problema:** BM25 em memória responde em 3 a 5 ms; o p95 de ~150 ms da vetorial e da híbrida vem do
  embedding da pergunta na GPU.
- **Continuam falhando em todos os métodos:** os dois diffs, a linha de leiaute (`campo-01`) e a `multihop-02`.
  Precisam de estrutura no chunk, não de outro método de busca.

## Decisão
- Novo baseline de busca: **híbrida com BM25 `portuguese` e `rrf_k` 5** (`configs/hibrida-portuguese-rrf5.toml`):
  mesmo recall do BM25 sozinho e mantém os acertos de paráfrase da vetorial.
- Próximos: fusão que preserve os acertos exatos (pesos por lista ou roteamento quando a pergunta tem código) e
  chunk estrutural com cabeçalho de NT, versão e página, que ataca diffs e leiaute.
