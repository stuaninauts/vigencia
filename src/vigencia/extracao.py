"""Extração de texto dos PDFs, página a página."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pagina:
    numero: int
    texto: str


def paginas(texto: str) -> list[Pagina]:
    """Separa a saída do pdftotext pelas quebras de página (form feed). Numeração a partir de 1."""
    partes = texto.split("\f")
    if partes and not partes[-1].strip():
        partes = partes[:-1]
    return [Pagina(numero=i, texto=p) for i, p in enumerate(partes, start=1)]


def extrair(pdf: Path) -> list[Pagina]:
    """Texto com `pdftotext -layout`, que preserva o alinhamento das colunas das tabelas."""
    saida = subprocess.run(  # noqa: S603 (comando fixo, sem shell)
        ["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"],  # noqa: S607
        capture_output=True,
        check=True,
    )
    return paginas(saida.stdout.decode("utf-8"))
