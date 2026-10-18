# vigencia

RAG lab over the technical documentation of Brazil's electronic invoice (NF-e) during the consumption tax reform
(IBS, CBS, IS): which rule is in force on a given date, what changed between versions of a technical note,
and how much each retrieval technique actually helps, measured against a fixed golden set.

Status: phase 1 in progress. See `docs/visao-macro.md` and `docs/fases/fase-1.md`.

## Quickstart
```bash
make setup                 # uv sync + git hooks
uv run vigencia baixar     # NT PDFs in force on the portal since 2025-01-01 -> data/raw + data/manifesto.jsonl
make check                 # lint, types, tests
```
