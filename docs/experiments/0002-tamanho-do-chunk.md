# 0002: Tamanho do chunk

**Data:** 2026-10-19 · **Status:** concluído (só retrieval) · **Tempo limite:** 1 hora

## Hipótese
Chunks menores acertam regras de validação (uma linha de tabela por chunk); chunks maiores acertam perguntas que
dependem de contexto longo, como cronogramas. No geral, o tamanho não resolve as falhas estruturais do baseline.

## Setup
- **Baseline:** 0001 (`configs/baseline.toml`, 1500 caracteres, sobreposição 200).
- **Variável:** tamanho do chunk, com sobreposição proporcional (~13%): `configs/fixo-800.toml` e `configs/fixo-3000.toml`.
- **Golden set:** `dev`, 20 perguntas revisadas (18 com citação).
- **Comparação justa:** além do mesmo k, compara o mesmo volume de texto entregue ao LLM (~7,5 mil caracteres):
  800 com k=9, 1500 com k=5, 3000 com k=2 e k=3.

## Resultados
| Variante | Chunks | k | recall | MRR | reais (recall) | temporal | regra de validação |
|---|---|---|---|---|---|---|---|
| 800 | 2466 | 9 | 0,50 | 0,41 | 0,57 | 0,80 | 0,33 |
| **1500 (baseline)** | 1325 | 5 | **0,61** | 0,45 | **0,71** | 0,80 | **0,67** |
| 3000 | 663 | 3 | 0,56 | **0,47** | 0,64 | **1,00** | 0,33 |

Os resultados não mudam com k entre 2 e 9: cada pergunta acerta nas primeiras posições ou erra o documento inteiro.
Indexar cada variante leva cerca de 80 s na GPU; a avaliação não gasta API.

## Análise
- **Diferenças pequenas:** 9, 11 e 10 acertos em 18. Com este golden set, 1 pergunta vale 5,6 pontos de recall: nenhum
  tamanho é claramente melhor.
- **Trocas:** 3000 ganha `temporal-01` (a regra UB12-10 inteira, com as observações de cronograma, cabe num chunk) e perde
  `regra-01` e `regra-05`, que estavam no limite no baseline.
- **Falhas que nenhum tamanho resolve:** `regra-03` e `regra-06` (código de rejeição), `diff-01` e `diff-02` (histórico
  de outras NTs), `campo-01` (linha de leiaute) e `multihop-02`. São falhas de estrutura (o chunk não sabe de qual NT,
  versão e regra ele é) e de casamento lexical, não de tamanho.

## Decisão
Mantém 1500 como baseline. Próximos experimentos de chunking: chunk estrutural (uma regra de validação ou uma linha de
leiaute por chunk) e cabeçalho de contexto no chunk (NT, versão, página, grupo), os dois sem custo de API. Antes deles,
a busca lexical e híbrida, que ataca os códigos de rejeição.
