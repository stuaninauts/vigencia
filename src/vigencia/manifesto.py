"""Manifesto: registro de cada documento baixado, em JSON Lines."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

from vigencia.portal import ItemLista


@dataclass(frozen=True)
class Documento:
    """Um documento baixado: uma versão de uma NT, com o hash do PDF."""

    conteudo_id: str
    chave: str
    tipo: str
    numero: str
    versao: str | None
    publicado_em: date
    vigente_no_portal: bool
    rt: bool
    substituida_por: str | None
    titulo: str
    descricao: str
    url: str
    arquivo: str
    sha256: str
    baixado_em: datetime

    @classmethod
    def de_item(cls, item: ItemLista, arquivo: str, sha256: str, baixado_em: datetime) -> Documento:
        return cls(
            conteudo_id=item.conteudo_id,
            chave=item.chave,
            tipo=item.tipo,
            numero=item.numero,
            versao=item.versao,
            publicado_em=item.publicado_em,
            vigente_no_portal=item.vigente_no_portal,
            rt=item.rt,
            substituida_por=item.substituida_por,
            titulo=item.titulo,
            descricao=item.descricao,
            url=item.url,
            arquivo=arquivo,
            sha256=sha256,
            baixado_em=baixado_em,
        )

    def para_json(self) -> str:
        dados = asdict(self)
        dados["publicado_em"] = self.publicado_em.isoformat()
        dados["baixado_em"] = self.baixado_em.isoformat(timespec="seconds")
        return json.dumps(dados, ensure_ascii=False, sort_keys=True)

    @classmethod
    def de_json(cls, linha: str) -> Documento:
        dados = json.loads(linha)
        dados["publicado_em"] = date.fromisoformat(dados["publicado_em"])
        dados["baixado_em"] = datetime.fromisoformat(dados["baixado_em"])
        return cls(**dados)


def ler(caminho: Path) -> dict[str, Documento]:
    """Lê o manifesto, indexado por `conteudo_id`. Manifesto ausente é manifesto vazio."""
    if not caminho.exists():
        return {}
    docs = (Documento.de_json(linha) for linha in caminho.read_text("utf-8").splitlines() if linha)
    return {d.conteudo_id: d for d in docs}


def gravar(caminho: Path, docs: dict[str, Documento]) -> None:
    """Grava em ordem estável (publicação, chave, versão) e de forma atômica."""
    ordenados = sorted(docs.values(), key=lambda d: (d.publicado_em, d.chave, d.versao or ""))
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text("".join(d.para_json() + "\n" for d in ordenados), "utf-8")
    temporario.replace(caminho)
