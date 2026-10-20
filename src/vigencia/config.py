"""Config de experimento: um arquivo TOML em `configs/` por variante."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args

type Esforco = Literal["low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True)
class ConfigChunking:
    estrategia: str
    tamanho: int
    sobreposicao: int
    cabecalho: bool = False
    """Prefixa cada chunk com NT, versão, data, páginas e descrição do documento."""


@dataclass(frozen=True)
class ConfigEmbedding:
    modelo: str
    dimensao: int
    lote: int


type Metodo = Literal["vetorial", "fts", "bm25", "hibrida"]
type Dicionario = Literal["simple", "portuguese", "pt_unaccent"]
type Roteamento = Literal["nenhum", "codigo"]


@dataclass(frozen=True)
class ConfigBusca:
    top_k: int
    metodo: Metodo = "vetorial"
    """`fts`: ranking nativo do Postgres; `bm25`: BM25 sobre os termos do Postgres;
    `hibrida`: vetorial + bm25 fundidas por Reciprocal Rank Fusion."""
    dicionario: Dicionario = "pt_unaccent"
    """Dicionário de busca textual do Postgres, usado por `fts`, `bm25` e `hibrida`."""
    candidatos: int = 50
    """Quantos resultados de cada lista entram na fusão da busca híbrida."""
    rrf_k: int = 60
    """Constante do Reciprocal Rank Fusion: 1 / (rrf_k + posição)."""
    peso_lexical: float = 1.0
    """Peso da lista do BM25 na fusão (a vetorial tem peso 1)."""
    roteamento: Roteamento = "nenhum"
    """`codigo`: pergunta com código (ID de regra, rejeição, versão, número de NT) vai só para
    o BM25."""

    reranker: str | None = None
    """Modelo cross-encoder que reordena os candidatos (ex.: `BAAI/bge-reranker-v2-m3`)."""
    candidatos_reranker: int = 20
    """Quantos resultados do método de busca o reranker reordena."""

    def __post_init__(self) -> None:
        if self.metodo not in get_args(Metodo.__value__):
            raise ValueError(f"método de busca inválido: {self.metodo!r}")
        if self.dicionario not in get_args(Dicionario.__value__):
            raise ValueError(f"dicionário inválido: {self.dicionario!r}")
        if self.roteamento not in get_args(Roteamento.__value__):
            raise ValueError(f"roteamento inválido: {self.roteamento!r}")


@dataclass(frozen=True)
class ConfigGeracao:
    modelo: str
    esforco: Esforco
    max_tokens: int

    def __post_init__(self) -> None:
        if self.esforco not in get_args(Esforco.__value__):
            raise ValueError(f"esforço inválido: {self.esforco!r}")


@dataclass(frozen=True)
class Config:
    nome: str
    chunking: ConfigChunking
    embedding: ConfigEmbedding
    busca: ConfigBusca
    geracao: ConfigGeracao
    impressao: str
    """Hash das seções que definem o índice (chunking e embedding). Mudar a geração não reindexa."""


def carregar(caminho: Path) -> Config:
    dados = tomllib.loads(caminho.read_text("utf-8"))
    do_indice = json.dumps(
        {"chunking": dados["chunking"], "embedding": dados["embedding"]}, sort_keys=True
    )
    return Config(
        nome=dados["nome"],
        chunking=ConfigChunking(**dados["chunking"]),
        embedding=ConfigEmbedding(**dados["embedding"]),
        busca=ConfigBusca(**dados["busca"]),
        geracao=ConfigGeracao(**dados["geracao"]),
        impressao=hashlib.sha256(do_indice.encode()).hexdigest()[:12],
    )
