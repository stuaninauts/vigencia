"""Métodos de busca sobre o índice textual: vetorial, lexical (FTS e BM25) e híbrida (RRF)."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable
from dataclasses import replace

from vigencia import indice
from vigencia.config import ConfigBusca
from vigencia.indice import Conexao, Resultado

type IdChunk = tuple[str, int]


class Bm25:
    """BM25 clássico (k1, b) sobre a frequência de termos de cada chunk."""

    def __init__(
        self, frequencias: dict[IdChunk, dict[str, int]], k1: float = 1.2, b: float = 0.75
    ) -> None:
        self._frequencias = frequencias
        self._k1 = k1
        self._b = b
        self._tamanhos = {c: sum(f.values()) for c, f in frequencias.items()}
        n = len(frequencias)
        self._media = sum(self._tamanhos.values()) / n if n else 0.0
        df: Counter[str] = Counter()
        for termos in frequencias.values():
            df.update(termos.keys())
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def pontuar(self, termos_consulta: list[str], k: int) -> list[tuple[IdChunk, float]]:
        consulta = [t for t in dict.fromkeys(termos_consulta) if t in self._idf]
        pontos: dict[IdChunk, float] = {}
        for chunk, freqs in self._frequencias.items():
            normal = 1 - self._b + self._b * self._tamanhos[chunk] / self._media
            total = sum(
                self._idf[t] * freqs[t] * (self._k1 + 1) / (freqs[t] + self._k1 * normal)
                for t in consulta
                if t in freqs
            )
            if total > 0:
                pontos[chunk] = total
        return sorted(pontos.items(), key=lambda par: par[1], reverse=True)[:k]


def fundir_rrf(listas: list[list[IdChunk]], rrf_k: int, k: int) -> list[tuple[IdChunk, float]]:
    """Reciprocal Rank Fusion: soma 1 / (rrf_k + posição) de cada lista em que o chunk aparece."""
    pontos: dict[IdChunk, float] = {}
    for lista in listas:
        for posicao, chunk in enumerate(lista, start=1):
            pontos[chunk] = pontos.get(chunk, 0.0) + 1 / (rrf_k + posicao)
    return sorted(pontos.items(), key=lambda par: par[1], reverse=True)[:k]


class Buscador:
    """Executa o método de busca da config. Guarda o BM25 entre perguntas (carrega uma vez)."""

    def __init__(
        self,
        conn: Conexao,
        nome_indice: str,
        cfg: ConfigBusca,
        embutir: Callable[[str], list[float]] | None,
    ) -> None:
        if cfg.metodo in ("vetorial", "hibrida") and embutir is None:
            raise ValueError(f"o método {cfg.metodo!r} precisa de um modelo de embedding")
        self._conn = conn
        self._indice = nome_indice
        self._cfg = cfg
        self._embutir = embutir
        self._bm25: Bm25 | None = None

    def buscar(self, pergunta: str, k: int | None = None) -> list[Resultado]:
        k = k or self._cfg.top_k
        match self._cfg.metodo:
            case "vetorial":
                return self._vetorial(pergunta, k)
            case "fts":
                return indice.buscar_fts(
                    self._conn, self._indice, pergunta, self._cfg.dicionario, k
                )
            case "bm25":
                return self._carregar(self._bm25_ids(pergunta, k))
            case "hibrida":
                n = self._cfg.candidatos
                vetorial = [r.id_chunk for r in self._vetorial(pergunta, n)]
                lexical = [c for c, _ in self._bm25_ids(pergunta, n)]
                return self._carregar(fundir_rrf([vetorial, lexical], self._cfg.rrf_k, k))

    def _vetorial(self, pergunta: str, k: int) -> list[Resultado]:
        assert self._embutir is not None  # noqa: S101 (garantido no __init__)
        return indice.buscar_vetorial(self._conn, self._indice, self._embutir(pergunta), k)

    def _bm25_ids(self, pergunta: str, k: int) -> list[tuple[IdChunk, float]]:
        if self._bm25 is None:
            self._bm25 = Bm25(indice.frequencias(self._conn, self._indice, self._cfg.dicionario))
        termos = indice.termos(self._conn, self._cfg.dicionario, pergunta)
        return self._bm25.pontuar(termos, k)

    def _carregar(self, pontuados: list[tuple[IdChunk, float]]) -> list[Resultado]:
        chunks = indice.por_ids(self._conn, self._indice, [c for c, _ in pontuados])
        return [replace(chunks[c], pontuacao=p) for c, p in pontuados if c in chunks]
