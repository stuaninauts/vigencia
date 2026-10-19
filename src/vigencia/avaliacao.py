"""Avaliação contra o golden set. Por enquanto, só o retrieval (sem custo de API)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from vigencia.indice import Resultado


@dataclass(frozen=True)
class CitacaoEsperada:
    chave: str
    versao: str | None
    pagina: int


@dataclass(frozen=True)
class Pergunta:
    id: str
    tipo: str
    pergunta: str
    resposta_esperada: str
    citacoes: list[CitacaoEsperada]
    notas: str
    revisado: bool


def carregar_golden(caminho: Path) -> list[Pergunta]:
    perguntas = []
    for linha in caminho.read_text("utf-8").splitlines():
        if not linha.strip():
            continue
        dados = json.loads(linha)
        dados["citacoes"] = [CitacaoEsperada(**c) for c in dados["citacoes"]]
        perguntas.append(Pergunta(**dados))
    return perguntas


def cobre(resultado: Resultado, esperada: CitacaoEsperada) -> bool:
    return (
        resultado.chave == esperada.chave
        and resultado.versao == esperada.versao
        and resultado.pagina_inicio <= esperada.pagina <= resultado.pagina_fim
    )


def posicao_do_acerto(resultados: list[Resultado], esperadas: list[CitacaoEsperada]) -> int | None:
    """Posição (a partir de 1) do primeiro chunk que cobre alguma citação esperada."""
    for posicao, r in enumerate(resultados, start=1):
        if any(cobre(r, e) for e in esperadas):
            return posicao
    return None


@dataclass(frozen=True)
class Metricas:
    perguntas: int
    recall_at_k: float
    mrr: float


def metricas(posicoes: list[int | None]) -> Metricas:
    """Recall@k e MRR sobre as perguntas que têm citação esperada."""
    n = len(posicoes)
    if n == 0:
        return Metricas(0, 0.0, 0.0)
    acertos = [p for p in posicoes if p is not None]
    return Metricas(
        perguntas=n,
        recall_at_k=len(acertos) / n,
        mrr=sum(1 / p for p in acertos) / n,
    )
