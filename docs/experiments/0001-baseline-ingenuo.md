# 0001: Baseline ingênuo

**Data:** 2026-10-18 · **Status:** rodando (retrieval medido; geração pendente de autorização de custo) · **Tempo limite:** 1 dia

## Hipótese
Um RAG ingênuo (chunk de tamanho fixo, só busca vetorial) acerta perguntas com vocabulário comum e falha em
identificadores exatos, em linhas de tabela, em perguntas sobre uma versão específica e em perguntas que precisam de
dois saltos.

## Setup
- **Baseline:** este é o primeiro.
- **Config:** `configs/baseline.toml` (índice `baseline-374d73788e62`): chunks de 1500 caracteres com 200 de
  sobreposição sobre o texto do `pdftotext -layout`; embedding `BAAI/bge-m3` local; busca vetorial exata, top-5.
- **Corpus:** 24 documentos vigentes no portal publicados desde 2025-01-01, 531 páginas, 1325 chunks.
- **Golden set:** `evals/golden/dev/perguntas.jsonl`, 10 perguntas (rascunho, `revisado: false`).

## Resultados: retrieval
Comando: `uv run vigencia avaliar-busca` (8 perguntas com citação esperada).

| Pergunta | Tipo | Top-5 |
|---|---|---|
| `campo-01` | consulta de campo | falha (NT certa, páginas erradas) |
| `regra-01` | regra de validação | falha (só outras NTs) |
| `regra-02` | regra de validação | acerto em 1 |
| `temporal-01` | temporal | acerto em 1 |
| `temporal-02` | temporal | acerto em 1 |
| `temporal-03` | temporal | acerto em 1 |
| `diff-01` | diff | falha (histórico de outras NTs) |
| `multihop-01` | multi-hop | falha |

**recall@5 0,50 · MRR 0,50.** Com top-10 o resultado não muda (recall@10 0,50).

## Resultados: geração
Pendente: `vigencia perguntar` chama a API paga e só roda com autorização do autor.

## Análise (parcial)
- **Identificador exato:** "rejeição 1011" não aproxima o chunk da regra `UB01-10` no espaço vetorial. Candidato
  natural à busca lexical (experimento 0002).
- **Identidade do documento:** "versão 1.52 da NT 2025.002" recupera o Histórico de Alterações de outras NTs, porque
  o texto do chunk não diz de qual NT e versão ele é. Candidatos: contextual retrieval e filtro por metadado.
- **Formatação perdida na extração:** na p. 69 da NT 2025.002 v1.52, as datas 01/09/2026 e 05/10/2026 estão riscadas
  e 03/11/2026 está realçada; o `pdftotext` devolve as três datas em sequência. O realce amarelo, que marca o que mudou
  na versão, também se perde. Isso afeta a geração mesmo quando o retrieval acerta (`temporal-01`).

## Decisão
Pendente da parte de geração.
