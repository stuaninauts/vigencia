.DEFAULT_GOAL := help
.PHONY: help setup db fmt lint typecheck test test-all hooks-test check ci eval eval-test

help: ## lista os alvos
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-11s %s\n", $$1, $$2}'

setup: ## instala dependências e git hooks (uma vez após clonar)
	uv sync
	uv run pre-commit install

db: ## sobe o Postgres com pgvector (docker compose)
	docker compose up -d --wait

fmt: ## formata e corrige o que o ruff consegue
	uv run ruff format
	uv run ruff check --fix

lint: ## lint e formatação sem alterar arquivos
	uv run ruff check
	uv run ruff format --check

typecheck: ## mypy strict
	uv run mypy

test: ## testes rápidos (sem rede, LLM nem banco)
	uv run pytest -m "not network and not eval and not db"

test-all: ## todos os testes, inclusive rede, LLM e banco (rode make db antes)
	uv run pytest

hooks-test: ## testes dos guardrails do Claude Code e dos scripts de hook
	bash .claude/hooks/test-guard-bash.sh
	bash scripts/test-hooks.sh

check: lint typecheck test hooks-test ## tudo que precisa passar antes de concluir

CONFIG ?= configs/cabecalho-rerank-20.toml
eval: ## avaliação ponta a ponta no split dev: estima o custo; CONFIRMAR=1 faz as chamadas pagas
	uv run vigencia avaliar --config $(CONFIG) $(if $(CONFIRMAR),--confirmar,)

eval-test: ## mesma avaliação no split test (só para o número final de um experimento)
	uv run vigencia avaliar --config $(CONFIG) --golden evals/golden/test/perguntas.jsonl $(if $(CONFIRMAR),--confirmar,)

ci: check ## alias usado pelo GitHub Actions
