"""Linha de comando: `vigencia <comando>`."""

from __future__ import annotations

import argparse
import logging
import os
from datetime import date
from pathlib import Path

from vigencia import avaliacao, baixar, config, indexar, indice


def _pasta_dados() -> Path:
    return Path(os.environ.get("VIGENCIA_DADOS", "data"))


def _cmd_baixar(args: argparse.Namespace) -> int:
    cliente = baixar.ClienteHttp(intervalo=args.intervalo)
    itens = baixar.selecionar(baixar.listar(cliente), args.desde, not args.todos)
    logging.info("%d documentos selecionados", len(itens))
    resumo = baixar.baixar(itens, _pasta_dados(), cliente)
    logging.info("novos: %d · já baixados: %d", resumo.novos, resumo.ja_baixados)
    for falha in resumo.falhas:
        logging.error("falhou: %s", falha)
    return 1 if resumo.falhas else 0


def _cmd_indexar(args: argparse.Namespace) -> int:
    from vigencia.embeddings import SentenceTransformerEmbedder

    cfg = config.carregar(args.config)
    embedder = SentenceTransformerEmbedder(cfg.embedding.modelo, cfg.embedding.lote)
    with indice.conectar() as conn:
        resumo = indexar.indexar(_pasta_dados(), cfg, conn, embedder)
        documentos, chunks = indice.contar(conn, indexar.nome_indice(cfg))
    logging.info(
        "indexados: %d · pulados: %d · índice %s: %d documentos, %d chunks",
        resumo.indexados,
        resumo.pulados,
        indexar.nome_indice(cfg),
        documentos,
        chunks,
    )
    return 0


def _cmd_buscar(args: argparse.Namespace) -> int:
    from vigencia.embeddings import SentenceTransformerEmbedder

    cfg = config.carregar(args.config)
    embedder = SentenceTransformerEmbedder(cfg.embedding.modelo, cfg.embedding.lote)
    vetor = embedder.embutir([args.pergunta])[0]
    with indice.conectar() as conn:
        resultados = indice.buscar_vetorial(
            conn, indexar.nome_indice(cfg), vetor, args.k or cfg.busca.top_k
        )
    for posicao, r in enumerate(resultados, start=1):
        paginas = f"p. {r.pagina_inicio}" + (
            f"-{r.pagina_fim}" if r.pagina_fim != r.pagina_inicio else ""
        )
        print(f"[{posicao}] {r.chave} v{r.versao} {paginas} (distância {r.distancia:.3f})")  # noqa: T201
        print("    " + " ".join(r.texto.split())[:300])  # noqa: T201
    return 0


def _cmd_perguntar(args: argparse.Namespace) -> int:
    """Faz uma chamada paga à API da Anthropic por pergunta."""
    import anthropic

    from vigencia import geracao
    from vigencia.embeddings import SentenceTransformerEmbedder

    cfg = config.carregar(args.config)
    embedder = SentenceTransformerEmbedder(cfg.embedding.modelo, cfg.embedding.lote)
    vetor = embedder.embutir([args.pergunta])[0]
    with indice.conectar() as conn:
        resultados = indice.buscar_vetorial(conn, indexar.nome_indice(cfg), vetor, cfg.busca.top_k)
    resposta = geracao.responder(anthropic.Anthropic(), args.pergunta, resultados, cfg.geracao)
    if resposta.recusou:
        logging.warning("o modelo recusou responder")
    print(resposta.texto, end="\n\n")  # noqa: T201
    for n, r in enumerate(resultados, start=1):
        citado = "*" if any(c.resultado == n for c in resposta.citacoes) else " "
        print(f"{citado}[{n}] {geracao.titulo(r)}")  # noqa: T201
    custo = resposta.custo_estimado()
    logging.info(
        "%s · %d tokens de entrada, %d de saída%s",
        resposta.modelo,
        resposta.tokens_entrada,
        resposta.tokens_saida,
        f" · ~US$ {custo:.4f}" if custo is not None else "",
    )
    return 0


def _cmd_avaliar_busca(args: argparse.Namespace) -> int:
    from vigencia.embeddings import SentenceTransformerEmbedder

    cfg = config.carregar(args.config)
    perguntas = [p for p in avaliacao.carregar_golden(args.golden) if p.citacoes]
    embedder = SentenceTransformerEmbedder(cfg.embedding.modelo, cfg.embedding.lote)
    vetores = embedder.embutir([p.pergunta for p in perguntas])
    k = args.k or cfg.busca.top_k
    posicoes: list[int | None] = []
    with indice.conectar() as conn:
        for pergunta, vetor in zip(perguntas, vetores, strict=True):
            resultados = indice.buscar_vetorial(conn, indexar.nome_indice(cfg), vetor, k)
            posicao = avaliacao.posicao_do_acerto(resultados, pergunta.citacoes)
            posicoes.append(posicao)
            marca = f"acerto em {posicao}" if posicao else "FALHA"
            achados = ", ".join(f"{r.chave} p.{r.pagina_inicio}" for r in resultados)
            print(f"{pergunta.id:16} {marca:12} top-{k}: {achados}")  # noqa: T201
    m = avaliacao.metricas(posicoes)
    print(f"\n{indexar.nome_indice(cfg)}: {m.perguntas} perguntas com citação · ", end="")  # noqa: T201
    print(f"recall@{k} {m.recall_at_k:.2f} · MRR {m.mrr:.2f}")  # noqa: T201
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vigencia", description=__doc__)
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("baixar", help="baixa NTs do portal e atualiza o manifesto")
    p.add_argument("--desde", type=date.fromisoformat, default=date(2025, 1, 1))
    p.add_argument("--todos", action="store_true", help="inclui documentos não vigentes")
    p.add_argument("--intervalo", type=float, default=2.0, help="segundos entre requisições")
    p.set_defaults(func=_cmd_baixar)

    p = sub.add_parser("indexar", help="extrai, faz chunks e indexa os documentos do manifesto")
    p.add_argument("--config", type=Path, default=Path("configs/baseline.toml"))
    p.set_defaults(func=_cmd_indexar)

    p = sub.add_parser("buscar", help="mostra os chunks recuperados para uma pergunta (sem LLM)")
    p.add_argument("pergunta")
    p.add_argument("--config", type=Path, default=Path("configs/baseline.toml"))
    p.add_argument("-k", type=int, default=None, help="quantos chunks (padrão: top_k da config)")
    p.set_defaults(func=_cmd_buscar)

    p = sub.add_parser("perguntar", help="responde com Claude citando as NTs (chamada paga)")
    p.add_argument("pergunta")
    p.add_argument("--config", type=Path, default=Path("configs/baseline.toml"))
    p.set_defaults(func=_cmd_perguntar)

    p = sub.add_parser("avaliar-busca", help="recall@k e MRR do retrieval no golden set (sem LLM)")
    p.add_argument("--golden", type=Path, default=Path("evals/golden/dev/perguntas.jsonl"))
    p.add_argument("--config", type=Path, default=Path("configs/baseline.toml"))
    p.add_argument("-k", type=int, default=None)
    p.set_defaults(func=_cmd_avaliar_busca)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    for ruidoso in ("httpx", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)
    resultado: int = args.func(args)
    return resultado
