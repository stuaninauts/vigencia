from datetime import UTC, date, datetime

from vigencia.chunking import Chunk
from vigencia.indexar import cabecalho
from vigencia.manifesto import Documento


def documento(versao: str | None) -> Documento:
    return Documento(
        conteudo_id="id=",
        chave="NT 2025.002",
        tipo="NT",
        numero="2025.002",
        versao=versao,
        publicado_em=date(2026, 10, 1),
        vigente_no_portal=True,
        rt=True,
        substituida_por=None,
        titulo="t",
        descricao="Adequação dos leiautes para IBS, CBS e IS",
        url="u",
        arquivo="raw/x.pdf",
        sha256="a" * 64,
        baixado_em=datetime(2026, 10, 18, tzinfo=UTC),
    )


def test_cabecalho_identifica_nt_versao_data_e_paginas() -> None:
    linha = cabecalho(documento("1.52"), Chunk(3, "texto", 5, 6))
    assert linha == (
        "[NT 2025.002 versão 1.52 (v1.52) · publicada em 01/10/2026 · p. 5-6"
        " · Adequação dos leiautes para IBS, CBS e IS]"
    )


def test_cabecalho_sem_versao() -> None:
    linha = cabecalho(documento(None), Chunk(0, "texto", 2, 2))
    assert linha.startswith("[NT 2025.002 · publicada em 01/10/2026 · p. 2 ·")
