#!/usr/bin/env bash
# commit-msg: valida Conventional Commits no assunto e proíbe travessão longo na mensagem.
set -uo pipefail
msg_file="$1"
subject=$(grep -v '^#' "$msg_file" | head -n1)

# merges, reverts e fixups gerados pelo git passam
[[ "$subject" =~ ^(Merge|Revert|fixup!|squash!|amend!) ]] && exit 0

types='feat|fix|docs|refactor|perf|test|build|ci|chore|revert'
if ! [[ "$subject" =~ ^($types)(\([a-z0-9._/-]+\))?!?:\ [^[:space:]].*$ ]]; then
  echo "Assunto fora do padrão Conventional Commits: '$subject'" >&2
  echo "Use: tipo(escopo opcional): resumo  (tipos: ${types//|/, })" >&2
  exit 1
fi
if (( ${#subject} > 72 )); then
  echo "Assunto com ${#subject} caracteres (máximo 72)." >&2
  exit 1
fi
if grep -v '^#' "$msg_file" | grep -q $'\xe2\x80\x94'; then
  echo "Mensagem com travessão longo: use vírgula, dois-pontos, parênteses ou ponto." >&2
  exit 1
fi
exit 0
