# 0006: Cabeçalho de contexto no chunk

**Data:** 2026-10-20 · **Status:** concluído (só retrieval) · **Tempo limite:** 1 hora

## Hipótese
As perguntas de diff falham em todos os métodos de busca (0003 a 0005) porque o chunk não diz de qual NT e versão ele
é: "o que mudou na v1.52 da NT 2025.002?" recupera o histórico de outras NTs. Prefixar cada chunk com NT, versão,
data, páginas e descrição do documento resolve isso sem LLM (uma versão barata do contextual retrieval).

## Setup
- **Baseline:** 0005, `configs/rerank-20.toml`, e também `fusao-rota` sem reranker.
- **Variável:** `cabecalho = true` na seção `[chunking]`: cada chunk começa com uma linha como
  `[NT 2025.002 versão 1.52 (v1.52) · publicada em 01/10/2026 · p. 6 · Nota técnica de adequação dos leiautes...]`.
  O cabeçalho entra no texto indexado (embedding e BM25) e no texto enviado ao LLM. Índice novo:
  `tamanho-fixo-1500-c6238fcdbc25`, mesmos 1325 chunks.
- **Configs:** `cabecalho-rerank-20.toml`, `cabecalho-fusao-rota.toml`. Busca idêntica às dos baselines.
- **Golden set:** `dev`, 18 perguntas com citação.

## Resultados
| Config | recall@5 | MRR | reais | sintéticas | diff | p50 |
|---|---|---|---|---|---|---|
| `fusao-rota` | 0,67 | 0,55 | 0,71 | 0,50 | 0,00 | 21 ms |
| `cabecalho-fusao-rota` | 0,67 | 0,54 | 0,71 | 0,50 | 0,50 | 18 ms |
| `rerank-20` | 0,83 | 0,69 | 0,86 | 0,75 | 0,00 | 330 ms |
| **`cabecalho-rerank-20`** | **0,89** | **0,71** | **0,93** | 0,75 | 0,50 | 348 ms |

## Análise
- **`diff-01` passa a acertar** (3º lugar) com e sem reranker: o cabeçalho faz "v1.52" e "NT 2025.002" casarem com o
  chunk certo do Histórico de Alterações.
- **Com reranker, o cabeçalho soma:** 0,83 para 0,89 de recall e 0,69 para 0,71 de MRR, sem custo de latência
  relevante. Sem reranker, ganha o diff e perde outra posição: recall igual.
- **`diff-02` continua falhando, e o motivo é de corpus:** a pergunta é sobre a v1.51, que só existe como linha do
  histórico dentro da v1.52; o cabeçalho de todos os chunks diz "v1.52". Resolve na fase 2, com todas as versões
  ingeridas e o cabeçalho de cada uma.
- **`campo-01` (linha de leiaute) segue frágil:** acerta com 50 candidatos (0005), não com 20. Candidato a chunk
  estrutural (uma linha de leiaute por chunk).

## Decisão
Novo baseline: `configs/cabecalho-rerank-20.toml` (cabeçalho no chunk + híbrida com roteamento + reranker sobre 20
candidatos). recall@5 0,89, MRR 0,71, p50 ~350 ms.
