# 0002: Stack inicial

**Data:** 2026-10-14 · **Status:** aceita (itens marcados "em avaliação" ainda serão decididos)

## Decisões
- **Python** como linguagem do pipeline e da API.
- **Postgres + pgvector local (Docker)** como índice textual: vetor e busca lexical no mesmo banco, simples de
  rodar e de migrar depois para Cloud SQL.
- **Python puro no início, sem framework de RAG:** as falhas ficam visíveis. LangChain e LangGraph entram quando a
  etapa pedir (agente, estado, human-in-the-loop), com o porquê registrado.
- **Neo4j Community (Docker), em avaliação:** grafo para aprendizado. Modela NT, versão (substitui), grupo e campo
  (coluna "Pai" do leiaute), regra (valida campo) e artigo da LC (citado por). Entra como experimento comparado contra
  SQL recursivo e contra só vetor em perguntas multi-hop, não como núcleo do sistema.
- **BigQuery, em avaliação:** catálogo analítico e tabela de resultados dos experimentos na fase de produção.
  O vector search do BigQuery fica como comparação de serving, não como índice principal.

## Sobre o vector search do BigQuery
Embeddings ficam numa coluna `ARRAY<FLOAT64>` (gerados fora ou por `ML.GENERATE_EMBEDDING` com modelos da Vertex AI).
`CREATE VECTOR INDEX` cria um índice aproximado, e a função `VECTOR_SEARCH` faz a busca dentro do SQL, podendo juntar
com tabelas estruturadas na mesma consulta. É pensado para volume grande e processamento analítico: cobra por dados
processados e tem latência de segundos, o que o torna fraco para servir perguntas interativas e bom para lotes
(por exemplo, deduplicação ou "achar chunks parecidos com cada regra nova").
