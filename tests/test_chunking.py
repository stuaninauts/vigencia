from itertools import pairwise

import pytest

from vigencia.chunking import tamanho_fixo
from vigencia.extracao import Pagina, paginas


def test_paginas_separa_por_form_feed_e_ignora_o_ultimo_vazio() -> None:
    lidas = paginas("primeira\fsegunda\fterceira\f")
    assert [(p.numero, p.texto) for p in lidas] == [
        (1, "primeira"),
        (2, "segunda"),
        (3, "terceira"),
    ]


def test_chunks_cobrem_o_texto_inteiro_com_sobreposicao() -> None:
    texto = "".join(chr(ord("a") + i % 26) for i in range(1000))
    chunks = tamanho_fixo([Pagina(1, texto)], tamanho=300, sobreposicao=50)
    assert [len(c.texto) for c in chunks[:-1]] == [300] * (len(chunks) - 1)
    for anterior, atual in pairwise(chunks):
        assert anterior.texto[-50:] == atual.texto[:50]
    assert chunks[-1].texto.endswith(texto[-10:] + "\n")


def test_chunk_registra_a_faixa_de_paginas() -> None:
    pags = [Pagina(1, "a" * 100), Pagina(2, "b" * 100), Pagina(3, "c" * 100)]
    chunks = tamanho_fixo(pags, tamanho=150, sobreposicao=0)
    assert [(c.pagina_inicio, c.pagina_fim) for c in chunks] == [(1, 2), (2, 3), (3, 3)]


def test_documento_vazio_nao_gera_chunk() -> None:
    assert tamanho_fixo([Pagina(1, "   ")], tamanho=100, sobreposicao=10) == []


@pytest.mark.parametrize(("tamanho", "sobreposicao"), [(100, 100), (100, -1)])
def test_sobreposicao_invalida(tamanho: int, sobreposicao: int) -> None:
    with pytest.raises(ValueError, match="sobreposição"):
        tamanho_fixo([Pagina(1, "x")], tamanho=tamanho, sobreposicao=sobreposicao)
