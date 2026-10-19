"""Índice textual: chunks e embeddings no Postgres com pgvector."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.rows import TupleRow

from vigencia.chunking import Chunk
from vigencia.manifesto import Documento

URL_PADRAO = "postgresql://vigencia:vigencia@127.0.0.1:5433/vigencia"

type Conexao = psycopg.Connection[TupleRow]

_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS documento_indexado (
    config      text NOT NULL,
    conteudo_id text NOT NULL,
    sha256      text NOT NULL,
    indexado_em timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (config, conteudo_id)
);
CREATE TABLE IF NOT EXISTS chunk (
    config        text NOT NULL,
    conteudo_id   text NOT NULL,
    ordem         int  NOT NULL,
    chave         text NOT NULL,
    versao        text,
    publicado_em  date NOT NULL,
    pagina_inicio int  NOT NULL,
    pagina_fim    int  NOT NULL,
    texto         text NOT NULL,
    embedding     vector NOT NULL,
    PRIMARY KEY (config, conteudo_id, ordem)
);
"""


@dataclass(frozen=True)
class Resultado:
    conteudo_id: str
    chave: str
    versao: str | None
    publicado_em: date
    pagina_inicio: int
    pagina_fim: int
    texto: str
    distancia: float


def conectar(url: str | None = None) -> Conexao:
    conn = psycopg.connect(url or os.environ.get("VIGENCIA_DB", URL_PADRAO))
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    register_vector(conn)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def ja_indexado(conn: Conexao, config: str, conteudo_id: str, sha256: str) -> bool:
    linha = conn.execute(
        "SELECT sha256 FROM documento_indexado WHERE config = %s AND conteudo_id = %s",
        (config, conteudo_id),
    ).fetchone()
    return linha is not None and linha[0] == sha256


def substituir(
    conn: Conexao,
    config: str,
    doc: Documento,
    chunks: list[Chunk],
    vetores: list[list[float]],
) -> None:
    """Troca todos os chunks do documento nesta config numa transação só (idempotente)."""
    with conn.transaction():
        conn.execute(
            "DELETE FROM chunk WHERE config = %s AND conteudo_id = %s", (config, doc.conteudo_id)
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunk (config, conteudo_id, ordem, chave, versao, publicado_em,"
                " pagina_inicio, pagina_fim, texto, embedding)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    (
                        config,
                        doc.conteudo_id,
                        c.ordem,
                        doc.chave,
                        doc.versao,
                        doc.publicado_em,
                        c.pagina_inicio,
                        c.pagina_fim,
                        c.texto,
                        Vector(v),
                    )
                    for c, v in zip(chunks, vetores, strict=True)
                ],
            )
        conn.execute(
            "INSERT INTO documento_indexado (config, conteudo_id, sha256) VALUES (%s, %s, %s)"
            " ON CONFLICT (config, conteudo_id)"
            " DO UPDATE SET sha256 = EXCLUDED.sha256, indexado_em = now()",
            (config, doc.conteudo_id, doc.sha256),
        )


def buscar_vetorial(conn: Conexao, config: str, vetor: list[float], k: int) -> list[Resultado]:
    """Busca exata por distância de cosseno (o corpus da fase 1 dispensa índice aproximado)."""
    linhas = conn.execute(
        "SELECT conteudo_id, chave, versao, publicado_em, pagina_inicio, pagina_fim, texto,"
        " embedding <=> %s AS distancia"
        " FROM chunk WHERE config = %s ORDER BY distancia LIMIT %s",
        (Vector(vetor), config, k),
    ).fetchall()
    return [Resultado(*linha) for linha in linhas]


def contar(conn: Conexao, config: str) -> tuple[int, int]:
    """(documentos, chunks) indexados nesta config."""
    linha = conn.execute(
        "SELECT count(DISTINCT conteudo_id), count(*) FROM chunk WHERE config = %s", (config,)
    ).fetchone()
    if linha is None:
        return 0, 0
    return int(linha[0]), int(linha[1])
