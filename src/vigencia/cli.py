"""Linha de comando: `vigencia <comando>`."""

from __future__ import annotations

import argparse
import logging
import os
from datetime import date
from pathlib import Path

from vigencia import baixar


def _pasta_dados() -> Path:
    return Path(os.environ.get("VIGENCIA_DADOS", "data"))


def _cmd_baixar(args: argparse.Namespace) -> int:
    cliente = baixar.ClienteHttp(intervalo=args.intervalo)
    itens = baixar.selecionar(baixar.listar(cliente), args.desde, not args.todos)
    logging.info("%d documentos selecionados", len(itens))
    resumo = baixar.baixar(itens, _pasta_dados(), cliente)
    logging.info("novos: %d · já baixados: %d", resumo.novos, resumo.ja_baixados)
    for falha in resumo.falhas:
        logging.error("falhou: %s", falha)
    return 1 if resumo.falhas else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vigencia", description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("baixar", help="baixa NTs do portal e atualiza o manifesto")
    p.add_argument("--desde", type=date.fromisoformat, default=date(2025, 1, 1))
    p.add_argument("--todos", action="store_true", help="inclui documentos não vigentes")
    p.add_argument("--intervalo", type=float, default=2.0, help="segundos entre requisições")
    p.set_defaults(func=_cmd_baixar)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    resultado: int = args.func(args)
    return resultado
