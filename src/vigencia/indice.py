"""Índice textual: chunks e embeddings no Postgres com pgvector."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg import sql
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
CREATE EXTENSION IF NOT EXISTS unaccent;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'pt_unaccent') THEN
        CREATE TEXT SEARCH CONFIGURATION pt_unaccent (COPY = portuguese);
        ALTER TEXT SEARCH CONFIGURATION pt_unaccent
            ALTER MAPPING FOR hword, hword_part, word WITH unaccent, portuguese_stem;
    END IF;
END $$;
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS tsv_simple tsvector
    GENERATED ALWAYS AS (to_tsvector('simple', texto)) STORED;
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS tsv_portuguese tsvector
    GENERATED ALWAYS AS (to_tsvector('portuguese', texto)) STORED;
ALTER TABLE chunk ADD COLUMN IF NOT EXISTS tsv_pt_unaccent tsvector
    GENERATED ALWAYS AS (to_tsvector('pt_unaccent', texto)) STORED;
CREATE INDEX IF NOT EXISTS chunk_tsv_simple ON chunk USING gin (tsv_simple);
CREATE INDEX IF NOT EXISTS chunk_tsv_portuguese ON chunk USING gin (tsv_portuguese);
CREATE INDEX IF NOT EXISTS chunk_tsv_pt_unaccent ON chunk USING gin (tsv_pt_unaccent);
"""

# Dicionário de busca textual do Postgres -> coluna tsvector gerada a partir de `texto`.
COLUNAS_TSV = {
    "simple": "tsv_simple",
    "portuguese": "tsv_portuguese",
    "pt_unaccent": "tsv_pt_unaccent",
}

_CAMPOS = "conteudo_id, ordem, chave, versao, publicado_em, pagina_inicio, pagina_fim, texto"


@dataclass(frozen=True)
class Resultado:
    conteudo_id: str
    ordem: int
    chave: str
    versao: str | None
    publicado_em: date
    pagina_inicio: int
    pagina_fim: int
    texto: str
    pontuacao: float
    """Quanto maior, mais relevante. A escala depende do método de busca."""

    @property
    def id_chunk(self) -> tuple[str, int]:
        return (self.conteudo_id, self.ordem)


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
    """Busca exata por similaridade de cosseno (o corpus da fase 1 dispensa índice aproximado)."""
    linhas = conn.execute(
        f"SELECT {_CAMPOS}, 1 - (embedding <=> %s) AS pontuacao"  # noqa: S608 (campos fixos)
        " FROM chunk WHERE config = %s ORDER BY pontuacao DESC LIMIT %s",
        (Vector(vetor), config, k),
    ).fetchall()
    return [Resultado(*linha) for linha in linhas]


def termos(conn: Conexao, dicionario: str, texto: str) -> list[str]:
    """Os termos (lexemas) que o Postgres extrai do texto com este dicionário."""
    linhas = conn.execute(
        "SELECT lexeme FROM unnest(to_tsvector(%s::regconfig, %s))", (dicionario, texto)
    ).fetchall()
    return [str(linha[0]) for linha in linhas]


def consulta_ou(termos_: list[str]) -> str:
    """tsquery com OU entre os termos: qualquer termo da pergunta conta, como em BM25."""
    return " | ".join("'" + termo.replace("'", "''") + "'" for termo in termos_)


def buscar_fts(
    conn: Conexao, config: str, pergunta: str, dicionario: str, k: int
) -> list[Resultado]:
    """Ranking nativo do Postgres (ts_rank_cd). Não tem IDF: termos comuns pesam como raros."""
    lexemas = termos(conn, dicionario, pergunta)
    if not lexemas:
        return []
    coluna = sql.Identifier(COLUNAS_TSV[dicionario])
    consulta = sql.SQL(
        "SELECT {campos}, ts_rank_cd({col}, q) AS pontuacao"
        " FROM chunk, CAST(%s AS tsquery) AS q"
        " WHERE config = %s AND {col} @@ q ORDER BY pontuacao DESC LIMIT %s"
    ).format(campos=sql.SQL(_CAMPOS), col=coluna)
    linhas = conn.execute(consulta, (consulta_ou(lexemas), config, k)).fetchall()
    return [Resultado(*linha) for linha in linhas]


def frequencias(
    conn: Conexao, config: str, dicionario: str
) -> dict[tuple[str, int], dict[str, int]]:
    """Frequência de cada termo em cada chunk, lida das colunas tsvector (base do BM25)."""
    coluna = sql.Identifier(COLUNAS_TSV[dicionario])
    consulta = sql.SQL(
        "SELECT conteudo_id, ordem, (t).lexeme, coalesce(array_length((t).positions, 1), 1)"
        " FROM chunk, unnest({col}) AS t WHERE config = %s"
    ).format(col=coluna)
    saida: dict[tuple[str, int], dict[str, int]] = {}
    for conteudo_id, ordem, lexema, freq in conn.execute(consulta, (config,)):
        saida.setdefault((str(conteudo_id), int(ordem)), {})[str(lexema)] = int(freq)
    return saida


def por_ids(
    conn: Conexao, config: str, ids: list[tuple[str, int]]
) -> dict[tuple[str, int], Resultado]:
    """Carrega os chunks pelos ids, com pontuação zero (quem chama define a pontuação)."""
    if not ids:
        return {}
    linhas = conn.execute(
        f"SELECT {_CAMPOS}, 0.0 FROM chunk"  # noqa: S608 (campos fixos)
        " WHERE config = %s AND (conteudo_id, ordem) IN"
        " (SELECT * FROM unnest(%s::text[], %s::int[]))",
        (config, [i[0] for i in ids], [i[1] for i in ids]),
    ).fetchall()
    resultados = [Resultado(*linha) for linha in linhas]
    return {r.id_chunk: r for r in resultados}


def contar(conn: Conexao, config: str) -> tuple[int, int]:
    """(documentos, chunks) indexados nesta config."""
    linha = conn.execute(
        "SELECT count(DISTINCT conteudo_id), count(*) FROM chunk WHERE config = %s", (config,)
    ).fetchone()
    if linha is None:
        return 0, 0
    return int(linha[0]), int(linha[1])
