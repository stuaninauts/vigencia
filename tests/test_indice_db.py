"""Integração com o Postgres do `docker compose` (rode `make db` antes)."""

from collections.abc import Iterator
from datetime import UTC, date, datetime

import psycopg
import pytest

from vigencia import indice
from vigencia.chunking import Chunk
from vigencia.manifesto import Documento

pytestmark = pytest.mark.db

CONFIG = "teste-indice"


@pytest.fixture
def conn() -> Iterator[indice.Conexao]:
    try:
        conexao = indice.conectar()
    except psycopg.OperationalError:
        pytest.skip("Postgres indisponível (rode make db)")
    conexao.execute("DELETE FROM chunk WHERE config = %s", (CONFIG,))
    conexao.execute("DELETE FROM documento_indexado WHERE config = %s", (CONFIG,))
    conexao.commit()
    yield conexao
    conexao.execute("DELETE FROM chunk WHERE config = %s", (CONFIG,))
    conexao.execute("DELETE FROM documento_indexado WHERE config = %s", (CONFIG,))
    conexao.commit()
    conexao.close()


def documento(sha: str = "a" * 64) -> Documento:
    return Documento(
        conteudo_id="id=",
        chave="NT 2025.002",
        tipo="NT",
        numero="2025.002",
        versao="1.52",
        publicado_em=date(2026, 10, 1),
        vigente_no_portal=True,
        rt=True,
        substituida_por=None,
        titulo="t",
        descricao="d",
        url="u",
        arquivo="raw/x.pdf",
        sha256=sha,
        baixado_em=datetime(2026, 10, 18, tzinfo=UTC),
    )


CHUNKS = [Chunk(0, "campo cClassTrib", 1, 1), Chunk(1, "rejeição 1011", 2, 3)]
VETORES = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


def test_substituir_e_idempotente(conn: indice.Conexao) -> None:
    indice.substituir(conn, CONFIG, documento(), CHUNKS, VETORES)
    indice.substituir(conn, CONFIG, documento(), CHUNKS, VETORES)
    assert indice.contar(conn, CONFIG) == (1, 2)


def test_ja_indexado_compara_o_hash(conn: indice.Conexao) -> None:
    indice.substituir(conn, CONFIG, documento(), CHUNKS, VETORES)
    assert indice.ja_indexado(conn, CONFIG, "id=", "a" * 64)
    assert not indice.ja_indexado(conn, CONFIG, "id=", "b" * 64)


def test_busca_vetorial_ordena_por_proximidade(conn: indice.Conexao) -> None:
    indice.substituir(conn, CONFIG, documento(), CHUNKS, VETORES)
    resultados = indice.buscar_vetorial(conn, CONFIG, [0.1, 0.9, 0.0], k=2)
    assert [r.texto for r in resultados] == ["rejeição 1011", "campo cClassTrib"]
    assert (resultados[0].pagina_inicio, resultados[0].pagina_fim) == (2, 3)
