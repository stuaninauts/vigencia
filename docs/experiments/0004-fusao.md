# 0004: Fusão da busca híbrida

**Data:** 2026-10-20 · **Status:** concluído (só retrieval) · **Tempo limite:** 2 horas

## Hipótese
A RRF com pesos iguais enterra os acertos exatos do BM25 (0003). Dar mais peso ao BM25, ou mandar direto para o BM25
as perguntas que trazem código, recupera esses acertos sem perder os da vetorial.

## Setup
- **Baseline:** 0003, híbrida vetorial + BM25 `portuguese` (`configs/hibrida-portuguese.toml`, `rrf_k` 60).
- **Variáveis** (uma por config):
  - peso da lista do BM25 na RRF: 2 e 3 (`fusao-peso2`, `fusao-peso3`);
  - roteamento: pergunta com ID de regra, número de rejeição, versão, número de NT ou cClassTrib vai só para o BM25;
    as demais vão para a híbrida (`fusao-rota`, e `fusao-rota-rrf5` com `rrf_k` 5).
- Detector de código: regex em `busca.tem_codigo`, que ignora anos e datas (testado em `tests/test_busca.py`).
- **Golden set:** `dev`, 18 perguntas com citação.

## Resultados
| Config | recall@5 | MRR | reais | sintéticas |
|---|---|---|---|---|
| `hibrida-portuguese` (RRF k 60) | 0,61 | 0,45 | 0,71 | 0,25 |
| `fusao-peso2` | 0,61 | 0,48 | 0,71 | 0,25 |
| `fusao-peso3` | 0,61 | 0,46 | 0,71 | 0,25 |
| `hibrida-portuguese-rrf5` | 0,67 | 0,48 | 0,71 | 0,50 |
| **`fusao-rota`** | **0,67** | **0,55** | 0,71 | 0,50 |
| `fusao-rota-rrf5` | 0,67 | 0,55 | 0,71 | 0,50 |

Teto da união vetorial + BM25 (0003): 0,78.

## Análise
- **Peso não resolve:** com peso 2 ou 3, o acerto exato do BM25 sobe algumas posições, mas não entra no top-5.
- **Roteamento resolve o que se propõe:** as perguntas com código (`regra-03`, `regra-06`, `multihop-01`) passam a
  acertar em 1º lugar, e o MRR sobe de 0,48 para 0,55. Com roteamento, o `rrf_k` deixa de importar.
- **Distância até o teto (0,78):** sobram `temporal-01` e `regra-01`, que colam a mensagem da SEFAZ sem código
  numérico ("Grupo IBSCBS nao informado", "Aliquota da CBS invalida"); cada lista acerta uma delas só em 5º lugar, e a
  fusão perde as duas. Uma mensagem de rejeição colada também é um "código"; o detector ainda não a reconhece.
- Ressalva: decisões tomadas no split `dev` com 18 perguntas.

## Decisão
Novo baseline de busca: `configs/fusao-rota.toml` (híbrida RRF k 60 com roteamento por código). Mais simples que
ajustar `rrf_k` e com o melhor MRR. Próximos: reranker sobre os candidatos da híbrida e chunk com cabeçalho de NT,
versão e página.
