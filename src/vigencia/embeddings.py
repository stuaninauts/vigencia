"""Modelos de embedding atrás de uma interface mínima."""

from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    def embutir(self, textos: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    """Modelo local via sentence-transformers. Usa a GPU se houver, em meia precisão."""

    def __init__(self, modelo: str, lote: int) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        self._modelo = SentenceTransformer(modelo, device=dispositivo)
        if dispositivo == "cuda":
            self._modelo.half()
        self._lote = lote

    def embutir(self, textos: list[str]) -> list[list[float]]:
        vetores = self._modelo.encode(
            textos, batch_size=self._lote, normalize_embeddings=True, show_progress_bar=False
        )
        return [list(map(float, v)) for v in vetores]
