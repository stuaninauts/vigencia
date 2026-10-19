"""Leitura da lista de Notas Técnicas do Portal NF-e."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

log = logging.getLogger(__name__)

URL_BASE = "https://www.nfe.fazenda.gov.br/portal/"
URL_LISTA = URL_BASE + "listaConteudo.aspx?tipoConteudo=04BIflQt1aY="

_SECAO = re.compile(r'<p class="tituloSessao">(?P<nome>.*?)</p>', re.S)
_ITEM = re.compile(
    r'<a[^>]*href="exibirArquivo\.aspx\?conteudo=(?P<id>[^"]+)"[^>]*>'
    r'<span class="tituloConteudo">(?P<titulo>.*?)</span></a>(?P<resto>.*?)</p>',
    re.S,
)
_TITULO = re.compile(
    r"^(?P<rt>RT\s*-?\s*)?Nota Técnica\s+(?P<conjunta>Conjunta\s+)?(?P<nfce>NFC-e\s+)?"
    r"(?P<numero>\d{4}\.\d{3})(?P<depois>.*)$"
)
_VERSAO = re.compile(r"v\.?\s?(\d+\.\d+[a-z]?(?:\s+a\s+\d+\.\d+[a-z]?)?)")
_PUBLICADA = re.compile(r"Publicada em (\d{2})/(\d{2})/(\d{4})")
_SUBSTITUIDA = re.compile(r"substituída pela NT (\d{4}\.\d{3})")
_TAGS = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class ItemLista:
    """Um documento listado no portal: uma versão de uma NT."""

    conteudo_id: str
    titulo: str
    descricao: str
    vigente_no_portal: bool
    tipo: str
    numero: str
    versao: str | None
    publicado_em: date
    rt: bool
    substituida_por: str | None

    @property
    def chave(self) -> str:
        """Identifica a NT. O número sozinho não basta: há NT e NT Conjunta com o mesmo número."""
        return f"{self.tipo} {self.numero}"

    @property
    def url(self) -> str:
        return url_documento(self.conteudo_id)


def url_documento(conteudo_id: str, pagina: int | None = None) -> str:
    """URL do PDF no portal; com `pagina`, abre o PDF na página (fragmento `#page=`)."""
    url = URL_BASE + "exibirArquivo.aspx?conteudo=" + quote(conteudo_id, safe="")
    return f"{url}#page={pagina}" if pagina else url


def normalizar(texto: str) -> str:
    """Decodifica entidades HTML e colapsa espaços (inclusive o não separável)."""
    return " ".join(html.unescape(texto).split())


def normalizar_id(conteudo_id: str) -> str:
    """O HTML do portal mostra o `+` do id em base64 como espaço, inclusive no início do id."""
    return html.unescape(conteudo_id).replace(" ", "+").strip()


@dataclass(frozen=True)
class Titulo:
    """Campos extraídos do título de um item da lista."""

    tipo: str
    numero: str
    versao: str | None
    publicado_em: date
    rt: bool
    substituida_por: str | None


def interpretar_titulo(titulo: str) -> Titulo | None:
    """Extrai tipo, número, versão, data e substituição do título. Devolve None se não for NT."""
    m = _TITULO.match(titulo)
    publicada = _PUBLICADA.search(titulo)
    if m is None or publicada is None:
        return None
    depois = m.group("depois")
    versao = _VERSAO.search(depois.split("Publicada")[0])
    substituida = _SUBSTITUIDA.search(depois)
    dia, mes, ano = (int(x) for x in publicada.groups())
    return Titulo(
        tipo="NT Conjunta" if m.group("conjunta") else "NT NFC-e" if m.group("nfce") else "NT",
        numero=m.group("numero"),
        versao=versao.group(1) if versao else None,
        publicado_em=date(ano, mes, dia),
        rt=m.group("rt") is not None,
        substituida_por=substituida.group(1) if substituida else None,
    )


def ler_lista(pagina: str) -> list[ItemLista]:
    """Lê os itens da página de lista, marcando se cada um está em "Documentos vigentes"."""
    secoes = [
        (m.start(), normalizar(_TAGS.sub("", m.group("nome")))) for m in _SECAO.finditer(pagina)
    ]
    itens: list[ItemLista] = []
    for m in _ITEM.finditer(pagina):
        titulo = normalizar(_TAGS.sub("", m.group("titulo")))
        dados = interpretar_titulo(titulo)
        if dados is None:
            log.warning("título fora do padrão, ignorado: %s", titulo)
            continue
        secao = next((nome for pos, nome in reversed(secoes) if pos < m.start()), "")
        itens.append(
            ItemLista(
                conteudo_id=normalizar_id(m.group("id")),
                titulo=titulo,
                descricao=normalizar(_TAGS.sub(" ", m.group("resto"))),
                vigente_no_portal=secao == "Documentos vigentes",
                tipo=dados.tipo,
                numero=dados.numero,
                versao=dados.versao,
                publicado_em=dados.publicado_em,
                rt=dados.rt,
                substituida_por=dados.substituida_por,
            )
        )
    return itens
