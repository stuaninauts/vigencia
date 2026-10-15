@AGENTS.md

## Específico do Claude Code
- `AGENTS.md` é a fonte das instruções (padrão aberto, lido por outros agentes). Aqui ficam só detalhes do Claude Code.
- Guardrails em `.claude/settings.json`: `deny` para `.env`, `~/.ssh` e `evals/golden/test/`; hook
  `.claude/hooks/guard-bash.sh` bloqueia comandos destrutivos, push na `main`, `--no-verify`, `pip install` e acesso
  ao split `test` do golden set. Testes do hook: `bash .claude/hooks/test-guard-bash.sh` (roda no `make check`).
- Depois de editar `.py`, o hook `format-python.sh` roda `ruff format` e `ruff check --fix` no arquivo.
- PR: skill `/pr` (gate `make check`, descrição a partir de `.github/pull_request_template.md`).
