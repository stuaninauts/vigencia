#!/usr/bin/env bash
# Testa scripts/check-commit-msg.sh e scripts/check-no-em-dash.sh: bash scripts/test-hooks.sh
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"; TMP=$(mktemp -d); trap 'rm -r "$TMP"' EXIT; fail=0
msg() { # $1 = esperado (ok|falha), $2 = mensagem
  printf '%s\n' "$2" > "$TMP/msg"; local got=ok
  "$DIR/check-commit-msg.sh" "$TMP/msg" 2>/dev/null || got=falha
  [[ $got == "$1" ]] && echo "ok    $1  $2" || { echo "FALHA esperado=$1 obtido=$got  $2"; fail=1; }
}
msg ok    'feat: adiciona crawler do portal'
msg ok    'fix(ingestao): não duplica versão já baixada'
msg ok    'feat!: muda schema do manifesto'
msg ok    'Merge branch main'
msg falha 'adiciona crawler'
msg falha 'feature: algo'
msg falha 'feat:sem espaço'
msg falha "feat: $(printf 'x%.0s' {1..70})"
msg falha $'feat: troca A \xe2\x80\x94 B'

printf 'texto limpo\n' > "$TMP/a.md"; printf 'com \xe2\x80\x94 travessão\n' > "$TMP/b.md"
"$DIR/check-no-em-dash.sh" "$TMP/a.md" >/dev/null 2>&1 && echo "ok    no-em-dash aceita texto limpo" || { echo "FALHA no-em-dash rejeitou texto limpo"; fail=1; }
"$DIR/check-no-em-dash.sh" "$TMP/b.md" >/dev/null 2>&1 && { echo "FALHA no-em-dash aceitou travessão"; fail=1; } || echo "ok    no-em-dash bloqueia travessão"
exit $fail
