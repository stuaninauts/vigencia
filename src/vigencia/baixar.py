"""Download educado e idempotente dos documentos do portal."""

from __future__ import annotations

import hashlib
import http.cookiejar
import logging
import time
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Protocol

from vigencia import __version__, manifesto
from vigencia.manifesto import Documento
from vigencia.portal import URL_LISTA, ItemLista, ler_lista

log = logging.getLogger(__name__)

USER_AGENT = f"vigencia/{__version__} (+https://github.com/stuaninauts/vigencia)"


class Cliente(Protocol):
    def obter(self, url: str) -> bytes: ...


class ClienteHttp:
    """HTTP com cookies (o portal exige) e intervalo mínimo entre requisições."""

    def __init__(
        self,
        intervalo: float = 2.0,
        timeout: float = 60.0,
        relogio: Callable[[], float] = time.monotonic,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._abridor = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self._abridor.addheaders = [("User-Agent", USER_AGENT)]
        self._intervalo = intervalo
        self._timeout = timeout
        self._relogio = relogio
        self._dormir = dormir
        self._ultima: float | None = None

    def obter(self, url: str) -> bytes:
        if self._ultima is not None:
            espera = self._intervalo - (self._relogio() - self._ultima)
            if espera > 0:
                self._dormir(espera)
        try:
            with self._abridor.open(url, timeout=self._timeout) as resposta:
                corpo: bytes = resposta.read()
        finally:
            self._ultima = self._relogio()
        return corpo


def selecionar(
    itens: Iterable[ItemLista], desde: date, somente_vigentes: bool = True
) -> list[ItemLista]:
    """Documentos publicados a partir de `desde`, por padrão só os vigentes no portal."""
    return [
        i
        for i in itens
        if i.publicado_em >= desde and (i.vigente_no_portal or not somente_vigentes)
    ]


def nome_arquivo(item: ItemLista) -> str:
    """Nome estável e único: o número sozinho não é chave, então entra um hash do id."""
    tipo = item.tipo.replace(" ", "-").lower()
    versao = (item.versao or "sem-versao").replace(" ", "")
    sufixo = hashlib.sha256(item.conteudo_id.encode()).hexdigest()[:8]
    return f"{tipo}-{item.numero}-v{versao}-{sufixo}.pdf"


@dataclass(frozen=True)
class Resumo:
    novos: int
    ja_baixados: int
    falhas: tuple[str, ...] = ()


def baixar(
    itens: Iterable[ItemLista],
    pasta_dados: Path,
    cliente: Cliente,
    agora: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Resumo:
    """Baixa os itens que faltam e atualiza o manifesto. Rodar duas vezes não baixa de novo."""
    caminho_manifesto = pasta_dados / "manifesto.jsonl"
    pasta_raw = pasta_dados / "raw"
    pasta_raw.mkdir(parents=True, exist_ok=True)
    docs = manifesto.ler(caminho_manifesto)
    novos = ja_baixados = 0
    falhas: list[str] = []
    for item in itens:
        existente = docs.get(item.conteudo_id)
        if existente and _integro(pasta_dados / existente.arquivo, existente.sha256):
            ja_baixados += 1
            continue
        try:
            corpo = cliente.obter(item.url)
        except OSError as erro:
            falhas.append(f"{item.chave} v{item.versao}: {erro}")
            continue
        if not corpo.startswith(b"%PDF"):
            falhas.append(f"{item.chave} v{item.versao}: resposta não é PDF ({item.url})")
            continue
        arquivo = pasta_raw / nome_arquivo(item)
        arquivo.write_bytes(corpo)
        sha = hashlib.sha256(corpo).hexdigest()
        relativo = str(arquivo.relative_to(pasta_dados))
        docs[item.conteudo_id] = Documento.de_item(item, relativo, sha, agora())
        manifesto.gravar(caminho_manifesto, docs)
        novos += 1
        log.info("baixado %s v%s (%d KB)", item.chave, item.versao, len(corpo) // 1024)
    return Resumo(novos=novos, ja_baixados=ja_baixados, falhas=tuple(falhas))


def listar(cliente: Cliente) -> list[ItemLista]:
    pagina = cliente.obter(URL_LISTA).decode("utf-8", errors="replace")
    return ler_lista(pagina)


def _integro(arquivo: Path, sha256: str) -> bool:
    return arquivo.exists() and hashlib.sha256(arquivo.read_bytes()).hexdigest() == sha256
