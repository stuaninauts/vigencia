"""Linha de comando: `vigencia <comando>`."""

from __future__ import annotations

import argparse
import logging
import os
import statistics
import time
from datetime import date
from pathlib import Path

from vigencia import avaliacao, baixar, config, indexar, indice
from vigencia.busca import Buscador


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


def _buscador(cfg: config.Config, conn: indice.Conexao) -> Buscador:
    """Carrega o modelo de embedding só quando o método de busca usa vetores."""
    embutir = None
    if cfg.busca.metodo in ("vetorial", "hibrida"):
        from vigencia.embeddings import SentenceTransformerEmbedder

        embedder = SentenceTransformerEmbedder(cfg.embedding.modelo, cfg.embedding.lote)

        def embutir(texto: str) -> list[float]:
            return embedder.embutir([texto])[0]

    reordenar = None
    if cfg.busca.reranker:
        from vigencia.embeddings import CrossEncoderReranker

        reordenar = CrossEncoderReranker(cfg.busca.reranker).pontuar
    return Buscador(conn, indexar.nome_indice(cfg), cfg.busca, embutir, reordenar)


def _cmd_buscar(args: argparse.Namespace) -> int:
    cfg = config.carregar(args.config)
    with indice.conectar() as conn:
        resultados = _buscador(cfg, conn).buscar(args.pergunta, args.k)
    for posicao, r in enumerate(resultados, start=1):
        paginas = f"p. {r.pagina_inicio}" + (
            f"-{r.pagina_fim}" if r.pagina_fim != r.pagina_inicio else ""
        )
        print(f"[{posicao}] {r.chave} v{r.versao} {paginas} (pontuação {r.pontuacao:.3f})")  # noqa: T201
        print("    " + " ".join(r.texto.split())[:300])  # noqa: T201
    return 0


def _cmd_perguntar(args: argparse.Namespace) -> int:
    """Faz uma chamada paga à API da Anthropic por pergunta."""
    import anthropic

    from vigencia import geracao

    cfg = config.carregar(args.config)
    with indice.conectar() as conn:
        resultados = _buscador(cfg, conn).buscar(args.pergunta)
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
    cfg = config.carregar(args.config)
    perguntas = [p for p in avaliacao.carregar_golden(args.golden) if p.citacoes]
    k = args.k or cfg.busca.top_k
    posicoes: list[int | None] = []
    latencias: list[float] = []
    with indice.conectar() as conn:
        buscador = _buscador(cfg, conn)
        buscador.buscar(perguntas[0].pergunta, k)  # aquecimento: modelo na GPU, BM25 em memória
        for pergunta in perguntas:
            inicio = time.perf_counter()
            resultados = buscador.buscar(pergunta.pergunta, k)
            latencias.append((time.perf_counter() - inicio) * 1000)
            posicao = avaliacao.posicao_do_acerto(resultados, pergunta.citacoes)
            posicoes.append(posicao)
            marca = f"acerto em {posicao}" if posicao else "FALHA"
            achados = ", ".join(f"{r.chave} p.{r.pagina_inicio}" for r in resultados)
            print(f"{pergunta.id:16} {marca:12} top-{k}: {achados}")  # noqa: T201
    b = cfg.busca
    metodo = b.metodo if b.metodo == "vetorial" else f"{b.metodo} ({b.dicionario})"
    if b.reranker:
        metodo += f" + reranker {b.reranker} (top {b.candidatos_reranker})"
    print(f"\n{cfg.nome} · {metodo} · índice {indexar.nome_indice(cfg)} · recall@{k} e MRR")  # noqa: T201
    grupos: dict[str, list[int | None]] = {"geral": posicoes}
    for pergunta, posicao in zip(perguntas, posicoes, strict=True):
        grupos.setdefault(f"origem {pergunta.origem}", []).append(posicao)
        grupos.setdefault(f"tipo {pergunta.tipo}", []).append(posicao)
    for nome, valores in grupos.items():
        m = avaliacao.metricas(valores)
        print(f"  {nome:30} n={m.perguntas:<3} recall {m.recall_at_k:.2f}  MRR {m.mrr:.2f}")  # noqa: T201
    p50, p95 = statistics.quantiles(latencias, n=20)[9], statistics.quantiles(latencias, n=20)[18]
    print(f"  latência da busca: p50 {p50:.0f} ms · p95 {p95:.0f} ms")  # noqa: T201
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
