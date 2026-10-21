#!/usr/bin/env bash
# Roda casos contra guard-bash.sh: bash .claude/hooks/test-guard-bash.sh
set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/guard-bash.sh"; fail=0
# Repos temporários: o resultado não depende do branch atual deste repo.
TMP=$(mktemp -d); trap 'rm -r "$TMP"' EXIT
novo_repo() { # $1 = diretório, $2 = branch
  git init -q -b "$2" "$1" && git -C "$1" -c core.hooksPath=/dev/null -c user.name=t -c user.email=t@t \
    commit -q --allow-empty -m init
}
novo_repo "$TMP/feat" feat/x; novo_repo "$TMP/main" main
CWD="$TMP/feat"
check() { # $1 = esperado (block|ask|allow), $2 = comando
  local out code; out=$(jq -n --arg c "$2" --arg d "$CWD" '{tool_name:"Bash",tool_input:{command:$c},cwd:$d}' | "$HOOK" 2>/dev/null); code=$?
  local got=allow; [[ $code -eq 2 ]] && got=block
  [[ $code -eq 0 && $out == *'"permissionDecision":"ask"'* ]] && got=ask
  [[ $got == "$1" ]] && echo "ok    $1  $2" || { echo "FALHA esperado=$1 obtido=$got  $2"; fail=1; }
}
check block 'rm -rf data'
check block 'rm -r -f data'
check block 'cd x && rm -fr y'
check block 'git reset --hard HEAD~1'
check block 'git clean -fd'
check block 'git commit --no-verify -m x'
check block 'git commit -nm x'
check block 'git commit -an -m x'
check block 'git push origin main'
check block 'git -C . push origin main'
check block 'git push origin HEAD:main'
check block 'git push -f origin feat/x'
check block 'git push --force-with-lease'
check block 'git push origin +feat/x'
check block 'git push --delete origin feat/x'
check block 'pip install requests'
check block 'uv pip install requests'
check block 'cd src && pip3 install x'
check block 'python -m pip install x'
check block 'cat evals/golden/test/perguntas.jsonl'
check block 'grep -r rejeição evals/golden/test'
check block 'docker volume rm vigencia_pg'
check block 'docker system prune -a'
check block 'docker compose down -v'
check allow 'make eval-test'
check allow 'cat evals/golden/dev/perguntas.jsonl'
check allow 'uv add httpx'
check allow 'git push -u origin feat/x'
check allow 'git push origin feat/main-page'
check allow 'git commit -m "feat: nova etapa"'
check allow 'git commit -am "fix: ajuste"'
check allow 'git commit --amend'
check allow 'rm data/cache/arquivo.pdf'
check allow 'docker compose down'
check allow 'make check'
check ask   'make eval CONFIRMAR=1'
check ask   'make eval CONFIG=configs/x.toml CONFIRMAR=sim'
check ask   'uv run vigencia avaliar --confirmar'
check ask   'uv run vigencia perguntar "o que causa a rejeição 1037?"'
check allow 'make eval'
check block 'rm -rf data && make eval CONFIRMAR=1'
check allow 'uv run vigencia avaliar --limite 3'
check allow 'uv run vigencia avaliar-busca'

CWD="$TMP/main"
check block 'git push'
check block 'git push -u origin minha-branch'
exit $fail
