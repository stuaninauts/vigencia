# vigencia

RAG lab over the technical documentation of Brazil's electronic invoice (NF-e) during the consumption tax reform
(IBS, CBS, IS): which rule is in force on a given date, what changed between versions of a technical note,
and how much each retrieval technique actually helps, measured against a fixed golden set.

Status: phase 1 in progress. See `docs/visao-macro.md` and `docs/fases/fase-1.md`.

## Quickstart
```bash
make setup                         # uv sync + git hooks
make db                            # Postgres + pgvector (docker compose)
uv run vigencia baixar             # NT PDFs in force on the portal since 2025-01-01 -> data/raw + data/manifesto.jsonl
uv run vigencia indexar            # pdftotext -> chunks -> bge-m3 embeddings (GPU if available) -> pgvector
uv run vigencia buscar "..."       # retrieved chunks only, no LLM
uv run vigencia avaliar-busca      # recall@k and MRR on the dev golden set, no LLM
uv run vigencia perguntar "..."    # answer with citations via the Anthropic API (paid call)
make check                         # lint, types, tests
```
