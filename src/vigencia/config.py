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


@dataclass(frozen=True)
class ConfigEmbedding:
    modelo: str
    dimensao: int
    lote: int


@dataclass(frozen=True)
class ConfigBusca:
    top_k: int


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
