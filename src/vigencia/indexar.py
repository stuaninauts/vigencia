"""Indexação: manifesto → texto → chunks → embeddings → índice textual."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from vigencia import chunking, extracao, indice, manifesto
from vigencia.config import Config
from vigencia.embeddings import Embedder
from vigencia.indice import Conexao

log = logging.getLogger(__name__)


def nome_indice(config: Config) -> str:
    """Nome da config no índice: muda quando o arquivo de config muda."""
    return f"{config.nome}-{config.impressao}"


@dataclass(frozen=True)
class Resumo:
    indexados: int
    pulados: int
    chunks: int


def indexar(
    pasta_dados: Path,
    config: Config,
    conn: Conexao,
    embedder: Embedder,
) -> Resumo:
    """Indexa os documentos do manifesto que mudaram ou faltam nesta config."""
    if config.chunking.estrategia != "tamanho-fixo":
        raise ValueError(f"estratégia de chunking desconhecida: {config.chunking.estrategia}")
    nome = nome_indice(config)
    docs = manifesto.ler(pasta_dados / "manifesto.jsonl")
    indexados = pulados = total = 0
    for doc in sorted(docs.values(), key=lambda d: (d.publicado_em, d.chave)):
        if indice.ja_indexado(conn, nome, doc.conteudo_id, doc.sha256):
            pulados += 1
            continue
        paginas = extracao.extrair(pasta_dados / doc.arquivo)
        chunks = chunking.tamanho_fixo(
            paginas, config.chunking.tamanho, config.chunking.sobreposicao
        )
        vetores = embedder.embutir([c.texto for c in chunks])
        indice.substituir(conn, nome, doc, chunks, vetores)
        indexados += 1
        total += len(chunks)
        log.info(
            "indexado %s v%s: %d páginas, %d chunks",
            doc.chave,
            doc.versao,
            len(paginas),
            len(chunks),
        )
    return Resumo(indexados=indexados, pulados=pulados, chunks=total)
