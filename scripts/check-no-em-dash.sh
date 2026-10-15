#!/usr/bin/env bash
# Falha se algum arquivo recebido tiver o travessão longo (U+2014). Usado pelo pre-commit.
set -uo pipefail
status=0
for f in "$@"; do
  if grep -n $'\xe2\x80\x94' -- "$f" 2>/dev/null; then
    echo "  ↳ $f: troque o travessão longo por vírgula, dois-pontos, parênteses ou ponto." >&2
    status=1
  fi
done
exit $status
