from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from vigencia import manifesto
from vigencia.baixar import ClienteHttp, baixar, nome_arquivo, selecionar
from vigencia.portal import ItemLista

AGORA = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def item(numero: str, versao: str | None, publicado: date, vigente: bool = True) -> ItemLista:
    return ItemLista(
        conteudo_id=f"id+{numero}/{versao}=",
        titulo=f"Nota Técnica {numero} v.{versao} - Publicada em {publicado:%d/%m/%Y}",
        descricao="",
        vigente_no_portal=vigente,
        tipo="NT",
        numero=numero,
        versao=versao,
        publicado_em=publicado,
        rt=False,
        substituida_por=None,
    )


class ClienteFalso:
    def __init__(self, corpo: bytes = b"%PDF-1.7 conteudo") -> None:
        self.corpo = corpo
        self.urls: list[str] = []

    def obter(self, url: str) -> bytes:
        self.urls.append(url)
        return self.corpo


ITENS = [
    item("2025.002", "1.52", date(2026, 10, 1)),
    item("2026.010", "1.00", date(2026, 10, 1)),
]


def test_segunda_rodada_nao_baixa_de_novo(tmp_path: Path) -> None:
    cliente = ClienteFalso()
    primeira = baixar(ITENS, tmp_path, cliente, agora=lambda: AGORA)
    segunda = baixar(ITENS, tmp_path, cliente, agora=lambda: AGORA)
    assert (primeira.novos, primeira.ja_baixados) == (2, 0)
    assert (segunda.novos, segunda.ja_baixados) == (0, 2)
    assert len(cliente.urls) == 2


def test_arquivo_corrompido_e_baixado_de_novo(tmp_path: Path) -> None:
    cliente = ClienteFalso()
    baixar(ITENS[:1], tmp_path, cliente, agora=lambda: AGORA)
    (tmp_path / "raw" / nome_arquivo(ITENS[0])).write_bytes(b"%PDF truncado")
    resumo = baixar(ITENS[:1], tmp_path, cliente, agora=lambda: AGORA)
    assert resumo.novos == 1


def test_manifesto_registra_hash_e_caminho(tmp_path: Path) -> None:
    baixar(ITENS, tmp_path, ClienteFalso(), agora=lambda: AGORA)
    docs = manifesto.ler(tmp_path / "manifesto.jsonl")
    doc = docs[ITENS[0].conteudo_id]
    assert doc.chave == "NT 2025.002"
    assert (tmp_path / doc.arquivo).exists()
    assert len(doc.sha256) == 64
    assert doc.baixado_em == AGORA


def test_manifesto_ida_e_volta_sem_perda(tmp_path: Path) -> None:
    baixar(ITENS, tmp_path, ClienteFalso(), agora=lambda: AGORA)
    caminho = tmp_path / "manifesto.jsonl"
    lido = manifesto.ler(caminho)
    manifesto.gravar(caminho, lido)
    assert manifesto.ler(caminho) == lido


def test_resposta_que_nao_e_pdf_vira_falha_sem_abortar(tmp_path: Path) -> None:
    resumo = baixar(ITENS, tmp_path, ClienteFalso(b"<html>erro</html>"), agora=lambda: AGORA)
    assert resumo.novos == 0
    assert len(resumo.falhas) == 2
    assert "não é PDF" in resumo.falhas[0]
    assert manifesto.ler(tmp_path / "manifesto.jsonl") == {}


def test_selecionar_por_data_e_vigencia() -> None:
    antigos = item("2024.003", "1.00", date(2024, 5, 1))
    nao_vigente = item("2025.002", "1.51", date(2026, 8, 4), vigente=False)
    todos = [*ITENS, antigos, nao_vigente]
    assert selecionar(todos, date(2025, 1, 1)) == ITENS
    assert nao_vigente in selecionar(todos, date(2025, 1, 1), somente_vigentes=False)


def test_nome_de_arquivo_distingue_nt_conjunta() -> None:
    nt = item("2025.001", None, date(2025, 5, 8))
    conjunta = ItemLista(**{**nt.__dict__, "tipo": "NT Conjunta", "conteudo_id": "outro="})
    assert nome_arquivo(nt) != nome_arquivo(conjunta)
    assert nome_arquivo(conjunta).startswith("nt-conjunta-2025.001-vsem-versao-")


def test_cliente_respeita_intervalo_entre_requisicoes(monkeypatch: pytest.MonkeyPatch) -> None:
    esperas: list[float] = []
    cliente = ClienteHttp(intervalo=2.0, relogio=lambda: 100.0, dormir=esperas.append)

    def abrir(url: str, timeout: float) -> _Resposta:
        return _Resposta()

    monkeypatch.setattr(cliente._abridor, "open", abrir)
    cliente.obter("https://exemplo.invalid/a")
    cliente.obter("https://exemplo.invalid/b")
    assert esperas == [2.0]


class _Resposta:
    def __enter__(self) -> "_Resposta":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return b"%PDF"
