#!/usr/bin/env bash
# PreToolUse(Bash): bloqueia comandos destrutivos e atalhos que furam o fluxo do projeto. É guardrail, não
# fronteira de segurança: a proteção real da main é o ruleset do GitHub. Testes: .claude/hooks/test-guard-bash.sh
set -uo pipefail
command -v jq >/dev/null || { echo "guard-bash: jq ausente, bloqueando por segurança" >&2; exit 2; }
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')

block() { echo "Bloqueado por .claude/hooks/guard-bash.sh: $1. Se for intencional, o humano roda manualmente." >&2; exit 2; }
has() { printf '%s' "$CMD" | grep -Eq -- "$1"; }

# rm recursivo + forçado (-rf, -fr, -r -f, --recursive --force)
if has '(^|[;&|( ])rm[[:space:]]' && has '[[:space:]]-(-recursive|[a-zA-Z]*[rR])' && has '[[:space:]]-(-force|[a-zA-Z]*f)'; then
  block "rm recursivo forçado"
fi
has '\bgit\b.*\breset\b.*--hard' && block "git reset --hard"
has '\bgit\b.*\bclean\b.*[[:space:]]-[a-zA-Z]*f' && block "git clean -f"
has '\bgit\b.*--no-verify' && block "git --no-verify (pula gitleaks, lint e validação do commit)"
has '\bgit\b.*\bcommit\b.*[[:space:]]-[a-zA-Z]*n[a-zA-Z]*\b' && block "git commit -n (equivale a --no-verify)"
if has '\bgit\b.*\bpush\b'; then
  has '(--force|--force-with-lease|--mirror|--delete|[[:space:]]-[a-zA-Z]*[fd]\b|[[:space:]]\+[^[:space:]]+)' && block "git push forçado/destrutivo"
  has '([[:space:]:]|refs/heads/)(main|master)([[:space:]]|$)' && block "git push para main/master (use branch + PR)"
  BRANCH=$(git -C "${CWD:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]] && block "git push estando em $BRANCH (use branch + PR)"
fi
# dependências só pelo uv add (pip install fura o uv.lock)
has '(^|[;&|(][[:space:]]*|[[:space:]]&&[[:space:]]*)(uv[[:space:]]+)?pip3?[[:space:]]+install\b' && block "pip install (use uv add)"
has '\bpython3?[[:space:]]+-m[[:space:]]+pip[[:space:]]+install\b' && block "python -m pip install (use uv add)"
# split test do golden set: quem cura é o humano; o agente que o lê contamina os números. Rodar a avaliação via make é ok.
if has 'evals/golden/test' && ! has '^[[:space:]]*make[[:space:]]'; then
  block "acesso ao split test do golden set (use make eval-test quando existir)"
fi
# volumes do Docker guardam índice e banco; apagar é ação do humano
has '\bdocker\b.*\b(volume[[:space:]]+(rm|prune)|system[[:space:]]+prune)\b' && block "apagar volumes do Docker"
has '\bdocker\b.*\bcompose\b.*\bdown\b.*[[:space:]](-v|--volumes)\b' && block "docker compose down -v (apaga volumes)"
# Depois de todos os bloqueios: o que for perigoso já parou acima.
# chamada paga à API: sempre pede confirmação ao humano, mesmo que a permissão do comando esteja liberada
if has '(--confirmar\b|\bCONFIRMAR=[^[:space:]]+|\bvigencia[[:space:]]+perguntar\b)'; then
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"Chamada paga à API da Anthropic: confirme o custo antes de rodar."}}'
  exit 0
fi
exit 0
