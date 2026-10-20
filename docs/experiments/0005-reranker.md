# 0005: Reranker cross-encoder

**Data:** 2026-10-20 · **Status:** concluído (só retrieval) · **Tempo limite:** 2 horas

## Hipótese
Um cross-encoder lê pergunta e chunk juntos e ordena melhor que a pontuação de cada busca. Aplicado sobre mais
candidatos que o top-5, ele traz para cima chunks certos que a busca deixou em 6º, 15º ou 40º.

## Setup
- **Baseline:** 0004, `configs/fusao-rota.toml` (híbrida vetorial + BM25 `portuguese`, RRF k 60, roteamento por código).
- **Variável:** reranker `BAAI/bge-reranker-v2-m3` local (GPU, fp16) reordenando os N primeiros candidatos, N = 20 e 50
  (`rerank-20`, `rerank-50`).
- **Controles:** o mesmo reranker sobre 20 candidatos só da vetorial (`rerank-20-baseline`) e só do BM25
  (`rerank-20-bm25-portuguese`).
- **Golden set:** `dev`, 18 perguntas com citação. Latência por pergunta, depois de aquecer, inclui o reranker.

## Resultados
| Config | Candidatos | recall@5 | MRR | reais | sintéticas | p50 | p95 |
|---|---|---|---|---|---|---|---|
| `fusao-rota` (sem reranker) | - | 0,67 | 0,55 | 0,71 | 0,50 | ~20 ms | ~150 ms |
| `rerank-20-baseline` | vetorial 20 | 0,61 | 0,53 | 0,71 | 0,25 | 301 ms | 423 ms |
| `rerank-20-bm25-portuguese` | BM25 20 | 0,83 | 0,69 | 0,86 | 0,75 | 282 ms | 324 ms |
| **`rerank-20`** | híbrida 20 | **0,83** | **0,69** | 0,86 | 0,75 | 328 ms | 459 ms |
| `rerank-50` | híbrida 50 | 0,89 | 0,70 | 0,93 | 0,75 | 779 ms | 924 ms |

Recall dos candidatos (o teto do reranker):

| Método | recall@20 | recall@50 |
|---|---|---|
| vetorial | 0,67 | 0,78 |
| BM25 `portuguese` | 0,89 | 0,89 |
| híbrida com roteamento | 0,89 | 0,94 |

## Análise
- **Maior ganho do projeto até aqui:** de 0,67 para 0,83 de recall@5 e de 0,55 para 0,69 de MRR com 20 candidatos.
  Passa do teto de 0,78 da união vetorial + BM25 no top-5 (0003) porque olha mais fundo.
- **O reranker só reordena o que a busca traz.** A qualidade final acompanha o recall dos candidatos: a vetorial
  coloca 0,67 das respostas no top-20 e o reranker não tem o que salvar; BM25 e híbrida colocam 0,89.
- **Com reranker, o BM25 sozinho empata com a híbrida** (0,83 / 0,69) e é mais simples e mais rápido: não calcula
  embedding da pergunta. Neste golden set a vetorial não acrescenta nada depois do reranker; com mais perguntas
  parafraseadas isso pode mudar.
- **50 candidatos:** +1 pergunta (`campo-01`, a linha de leiaute) por 2,4 vezes a latência.
- **Continuam falhando:** os dois diffs (`diff-01`, `diff-02`), em todas as variantes. O chunk não diz de qual NT e
  versão ele é, e a pergunta é justamente sobre isso.
- Latência de 300 a 800 ms é pequena perto da geração com LLM (segundos), mas é o custo dominante da busca.

## Decisão
- Novo baseline de busca: `configs/rerank-20.toml` (híbrida com roteamento + reranker sobre 20 candidatos). Mesma
  qualidade do BM25 + reranker e mantém a vetorial para paráfrases, por ~50 ms a mais.
- Alternativa registrada para produção (E4): BM25 + reranker dispensa embedding na consulta; `rerank-50` quando a
  qualidade valer 2,4 vezes a latência.
- Próximo: cabeçalho de NT, versão e página no chunk, para os diffs.
