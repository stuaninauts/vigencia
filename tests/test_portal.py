from datetime import date
from pathlib import Path

import pytest

from vigencia.portal import ItemLista, interpretar_titulo, ler_lista, normalizar_id

FIXTURE = Path(__file__).parent / "fixtures" / "lista_portal.html"


@pytest.fixture(scope="module")
def itens() -> dict[str, ItemLista]:
    lidos = ler_lista(FIXTURE.read_text("utf-8"))
    return {f"{i.chave} v{i.versao}": i for i in lidos}


def test_le_todos_os_itens_reais_da_fixture(itens: dict[str, ItemLista]) -> None:
    assert len(itens) == 12


def test_secao_do_portal_define_vigencia_do_documento(itens: dict[str, ItemLista]) -> None:
    assert itens["NT 2025.002 v1.52"].vigente_no_portal
    assert not itens["NT 2025.002 v1.51"].vigente_no_portal


def test_numero_sozinho_nao_e_chave(itens: dict[str, ItemLista]) -> None:
    assert itens["NT 2025.001 v1.03"].tipo == "NT"
    assert itens["NT Conjunta 2025.001 vNone"].tipo == "NT Conjunta"


def test_titulo_com_espaco_nao_separavel(itens: dict[str, ItemLista]) -> None:
    item = itens["NT 2025.001 v1.03"]
    assert item.titulo.startswith("Nota Técnica 2025.001.")
    assert item.publicado_em == date(2025, 9, 29)


def test_marca_reforma_tributaria_e_nfce(itens: dict[str, ItemLista]) -> None:
    assert itens["NT 2024.002 v1.10"].rt
    assert itens["NT 2024.002 vNone"].rt
    assert itens["NT NFC-e 2014.003 v1.02"].tipo == "NT NFC-e"


def test_descricao_vem_depois_do_link(itens: dict[str, ItemLista]) -> None:
    assert itens["NT 2025.001 v1.03"].descricao == "Alteração de regras de validação"


@pytest.mark.parametrize(
    ("titulo", "versao"),
    [
        ("Nota Técnica 2025.002 v.1.52 - Publicada em 01/10/2026", "1.52"),
        ("Nota Técnica 2025.002.v.1.20 - Publicada em 30/07/2025", "1.20"),
        ("Nota Técnica 2026.001 v.1.02b - Publicada em 31/07/2026", "1.02b"),
        ("Nota Técnica 2021.003 - v.1.50 - Publicada em 25/09/2026", "1.50"),
        ("Nota Técnica 2016.002 - v. 1.60 - Publicada em 01/02/2019", "1.60"),
        ("Nota Técnica 2015.003 - v.1.80 a 1.90 - Publicada em 10/10/2016", "1.80 a 1.90"),
        ("Nota Técnica Conjunta 2025.001 - Publicada em 08/05/2025", None),
    ],
)
def test_variacoes_de_versao(titulo: str, versao: str | None) -> None:
    dados = interpretar_titulo(titulo)
    assert dados is not None
    assert dados.versao == versao


def test_substituicao_explicita_no_titulo() -> None:
    dados = interpretar_titulo(
        "Nota Técnica 2009.005 (substituída pela NT 2009.006) - Publicada em 30/11/2010"
    )
    assert dados is not None
    assert dados.substituida_por == "2009.006"


def test_titulo_que_nao_e_nt() -> None:
    assert interpretar_titulo("Manual de Orientação do Contribuinte") is None


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [("9hgG  cH8gA=", "9hgG++cH8gA="), (" WTd7iuD21s=", "+WTd7iuD21s=")],
)
def test_id_com_espaco_vira_mais_do_base64(bruto: str, esperado: str) -> None:
    assert normalizar_id(bruto) == esperado


def test_url_codifica_o_id(itens: dict[str, ItemLista]) -> None:
    item = itens["NT 2025.002 v1.52"]
    assert item.url.endswith("exibirArquivo.aspx?conteudo=HXPO8VLbh4o%3D")
