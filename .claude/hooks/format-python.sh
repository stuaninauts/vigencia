#!/usr/bin/env bash
# PostToolUse(Edit|Write|MultiEdit): formata o .py recém-editado e aplica as correções automáticas do ruff.
# Nunca bloqueia: problemas que sobrarem aparecem no make check.
set -uo pipefail
FILE=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
[[ "$FILE" == *.py && -f "$FILE" ]] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
uv run --quiet ruff format --quiet "$FILE" >/dev/null 2>&1
uv run --quiet ruff check --fix --quiet "$FILE" >/dev/null 2>&1
exit 0
