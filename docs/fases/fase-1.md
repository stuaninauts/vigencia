# Fase 1: esqueleto ponta a ponta

**Data:** 2026-10-17 · **Status:** aceita

## Objetivo
Construir um sistema simples de propósito, medi-lo e mostrar onde o RAG ingênuo falha neste corpus.
Não otimizar nada antes de existir número. Cada etapa deixa o sistema funcionando e um card em `docs/experiments/`.

## Corpus da fase
- Cerca de 20 NTs, última versão de cada: a NT 2025.002 (RTC) e as NTs publicadas em 2025 e 2026.
- Versões antigas e a LC 214 ficam para a fase 2 (ingestão versionada e base legal).

## Etapa 1.1: RAG ingênuo e onde ele quebra
**Entregáveis**
- `vigencia baixar`: lê a lista do portal, baixa os PDFs para `data/raw/` e grava o manifesto em
  `data/manifesto.jsonl` (NT, versão, data de publicação, URL, sha256). Idempotente: rodar duas vezes não baixa de novo.
  Intervalo entre requisições e cache local.
- `vigencia indexar`: extrai texto com `pdftotext -layout`, gera chunks de tamanho fixo (baseline ingênuo de propósito),
  calcula embeddings e grava no índice textual (Postgres + pgvector via `docker compose`).
- `vigencia perguntar "<pergunta>"`: busca vetorial top-k, gera a resposta com LLM e cita NT, versão e página.
- 10 perguntas em `evals/golden/dev/`, cobrindo os 7 tipos de pergunta, cada uma com resposta esperada e citação esperada.
- Tabela de falhas: para cada pergunta, a citação esperada apareceu no top-k (retrieval)? A resposta está correta
  (geração)? Classificação: ok, falha de retrieval, falha de geração, ambas.
- Card `docs/experiments/0001-baseline-ingenuo.md` e README com instruções para rodar do zero.

**Pronto quando:** `make check` passa; os três comandos rodam a partir de um clone limpo; a tabela de falhas está preenchida.

## Etapa 1.2: busca lexical x vetorial x híbrida
- Golden set `dev` com 30 ou mais perguntas, cada uma com a citação esperada (NT, versão, página).
- Busca lexical (full-text do Postgres; configuração `portuguese` x `simple`, porque a primeira pode quebrar códigos
  como `UB01-10`), vetorial, híbrida (Reciprocal Rank Fusion) e reranker ligado ou desligado.
- Métricas por tipo de pergunta: recall@k e MRR; latência p50 e p95 do retrieval.
- Card `0002`. Hipótese: a busca lexical ganha em consulta de campo e regra de validação (identificadores exatos);
  a vetorial ganha em perguntas parafraseadas; a híbrida com reranker ganha no geral.

## Etapa 1.3: avaliação automatizada
- `make eval`: roda o golden set `dev` e grava métricas de retrieval, avaliação da resposta, latência, custo e config.
- Juiz LLM com critérios pass/fail: resposta correta, citação sustenta a resposta, recusa quando não há resposta.
- Calibração do juiz contra cerca de 20 rótulos humanos, com a concordância medida e registrada.
- Split `test` criado pelo humano (o agente não lê nem escreve esse split).
- Card `0003`.

## Etapa 1.4: design doc de produção no GCP
- `docs/design/producao-gcp.md`: diagrama, volume estimado (NTs por mês, chunks, consultas), latência alvo, custo
  estimado, trade-offs e plano de falha. Parte da `docs/visao-macro.md` e dos números medidos nas etapas 1.1 a 1.3.

## Decisões
- **LLM de geração:** Claude via API da Anthropic. Chamadas pagas só depois de o autor autorizar cada rodada.
- **Embedding:** comparar `bge-m3` local (GPU) com um embedding por API (provedor a definir). Começa pelo local;
  a comparação é um experimento próprio (uma variável por vez), depois do card `0002`.
- **Reranker:** comparar `bge-reranker-v2-m3` local com o Jev (TypeSafe AI), na etapa 1.2. O Jev é um modelo não
  generativo de decisões tipadas, lançado em early access em 2026-09-15, acessado por API (modelo `jev`). Reranking é
  um caso de uso citado pelo fornecedor, não um produto dedicado, e não há benchmark independente dele como reranker:
  medir isso em português é um resultado em si. Depende de acesso ao early access e é chamada paga.
