"""Estratégias de chunking. Funções puras: recebem páginas e devolvem chunks."""

from __future__ import annotations

from dataclasses import dataclass

from vigencia.extracao import Pagina


@dataclass(frozen=True)
class Chunk:
    ordem: int
    texto: str
    pagina_inicio: int
    pagina_fim: int


def tamanho_fixo(paginas: list[Pagina], tamanho: int, sobreposicao: int) -> list[Chunk]:
    """Janelas de `tamanho` caracteres sobre o documento inteiro, ignorando seções e tabelas.

    É o baseline ingênuo de propósito: corta tabela no meio e mistura páginas. Cada chunk
    guarda a faixa de páginas que cobre, para a citação.
    """
    if not 0 <= sobreposicao < tamanho:
        raise ValueError("sobreposição precisa ser >= 0 e menor que o tamanho")
    texto = ""
    inicios: list[tuple[int, int]] = []  # (posição no texto, número da página)
    for pagina in paginas:
        inicios.append((len(texto), pagina.numero))
        texto += pagina.texto + "\n"
    chunks: list[Chunk] = []
    passo = tamanho - sobreposicao
    for ordem, inicio in enumerate(range(0, max(len(texto) - sobreposicao, 1), passo)):
        trecho = texto[inicio : inicio + tamanho]
        if not trecho.strip():
            continue
        fim = inicio + len(trecho) - 1
        chunks.append(
            Chunk(
                ordem=ordem,
                texto=trecho,
                pagina_inicio=_pagina_em(inicios, inicio),
                pagina_fim=_pagina_em(inicios, fim),
            )
        )
    return chunks


def _pagina_em(inicios: list[tuple[int, int]], posicao: int) -> int:
    numero = inicios[0][1] if inicios else 1
    for comeco, pagina in inicios:
        if comeco > posicao:
            break
        numero = pagina
    return numero
