# Visão macro

**Data:** 2026-10-14 · **Status:** rascunho aprovado em linhas gerais; prazos e detalhes de cada fase a seguir.

## Por que este corpus é bom para aprender RAG
Observado na NT 2025.002 v1.52 (94 páginas, ~40 mil palavras):
- **Tabelas pesadas:** o leiaute é uma tabela (ID, Campo, Descrição, Ele, Pai, Tipo, Ocor., Tam., Observação)
  que atravessa páginas. Chunking ingênuo destrói a linha.
- **Identificadores exatos:** 307 menções a "Rejeição", IDs de regra de validação como `UB01-10`, IDs de campo e
  grupo como `AR03` e `W03`, códigos cClassTrib.
  Busca lexical tende a ganhar da vetorial aqui.
- **Duas datas por regra:** implantação em homologação e em produção (tabela "Histórico de Alterações / Cronograma").
- **Versões:** 15 versões da NT 2025.002 entre 28/03/2025 (v1.00) e 01/10/2026 (v1.52).
- **Referências cruzadas:** NTs citam outras NTs e a LC 214/2025.
- **Hierarquia:** a coluna "Pai" do leiaute forma uma árvore de grupos e campos.

## Arquitetura
```
Portal NF-e / LC 214
   │  crawler + manifesto (hash, documento, versão, datas)   ← incremental e idempotente
   ▼
Parsing (texto, tabelas de leiaute e de regras, histórico de alterações)
   ├──► Índice textual: chunks + BM25 + vetor, metadados de versão e vigência   (Postgres + pgvector)
   ├──► Catálogo estruturado: campos, regras, rejeições, vigências               (SQL; BigQuery na fase analítica)
   └──► Grafo (experimento): NT, versão, grupo, campo, regra, artigo da LC       (Neo4j Community)
            ▼
Roteador: texto → RAG | exata/agregada → SQL | relação → grafo | combinação
            ▼
Geração com citação (NT, versão, página, regra)
            ▼
API → servidor MCP → agente com aprovação humana ("radar de mudanças")

Transversal: avaliação · observabilidade · custo · CI
```

### Radar de mudanças (fio condutor do produto)
Quando sai uma versão nova de uma NT: o sistema ingere, calcula o diff contra a anterior, classifica o impacto,
redige um ticket "o que o emissor precisa mudar" e uma pessoa aprova antes de abrir. Liga ingestão, diff,
agente e human-in-the-loop num caso de uso único.

## Bancada de benchmark
### Golden set estratificado
| Tipo | Exemplo |
|---|---|
| Consulta de campo | Qual o tamanho e a ocorrência do campo X? |
| Regra de validação | O que causa a rejeição N? |
| Temporal | Em 01/11/2026 essa regra já vale em produção? |
| Diff | O que mudou da v1.51 para a v1.52? |
| Agregada | Quantas regras novas em 2026? |
| Multi-hop | Uma NT que remete a outra NT ou a um artigo da LC 214 |
| Sem resposta | Algo que nenhuma versão define (testa recusa) |

### Regras
- Golden set versionado, com divisão dev/teste (não ajustar o sistema às perguntas de teste).
- Cada experimento declara em quais tipos de pergunta espera ganho.
- Cada rodada registra config, métricas de retrieval e de resposta, latência e custo numa tabela de resultados.
- Uma variável por vez; o vencedor vira baseline; tempo limitado por experimento.

### Fila de experimentos (candidatos)
- **Parsing:** pdftotext, pdfplumber, Docling, modelo de visão.
- **Chunking:** tamanho fixo, por seção, linha de tabela como chunk, contextual retrieval.
- **Busca:** lexical, vetorial, híbrida, com e sem reranker; tokenização de códigos.
- **Embeddings:** abertos multilíngues x API.
- **Temporal:** filtro de vigência no retrieval x deixar o LLM decidir.
- **Estruturado:** roteamento para SQL x RAG puro em perguntas agregadas.
- **Grafo:** Cypher/GraphRAG x SQL recursivo x só vetor em perguntas multi-hop.
- **Extração:** parser determinístico x LLM para montar o catálogo.
- **Serving:** pgvector x BigQuery vector search (latência e custo).

## Fases
| Fase | O que o sistema ganha | Experimento principal |
|---|---|---|
| 1. Esqueleto | Ponta a ponta simples (~20 NTs, última versão), golden set inicial, design doc | Lexical x vetorial x híbrida com códigos exatos |
| 2. Sistema v1 | Ingestão versionada, parsing de tabelas, catálogo, retrieval temporal, citações; depois tracing, cache, evals no CI | Parsing e chunking de tabelas; temporal |
| 3. Agentes | Servidor MCP (`buscar_regra`, `diff_versoes`, `consultar_campo`), agente radar de mudanças, guardrails | Agente x pipeline fixo; grafo x SQL |
| 4. Produção | NT nova → Pub/Sub → workers no Cloud Run; carga e SLO; extração em lote para BigQuery | Extração LLM x determinística |
| 5. Fechamento | Documentação, demo, tabela final de evolução | |

## Escopo inicial
NF-e modelo 55, NT 2025.002 (RTC) e NTs correlatas de 2025-2026, mais a LC 214/2025. CT-e, NFS-e e regulamento do IBS
ficam para depois de o sistema v1 estar medido.
