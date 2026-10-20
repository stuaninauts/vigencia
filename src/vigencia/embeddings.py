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


class CrossEncoderReranker:
    """Reranker local (cross-encoder): lê pergunta e chunk juntos e dá uma nota de relevância."""

    def __init__(self, modelo: str, lote: int = 16) -> None:
        import torch
        from sentence_transformers import CrossEncoder

        dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        kwargs = {"torch_dtype": torch.float16} if dispositivo == "cuda" else {}
        self._modelo = CrossEncoder(modelo, device=dispositivo, model_kwargs=kwargs)
        self._lote = lote

    def pontuar(self, pergunta: str, textos: list[str]) -> list[float]:
        notas = self._modelo.predict(
            [(pergunta, t) for t in textos], batch_size=self._lote, show_progress_bar=False
        )
        return [float(n) for n in notas]
