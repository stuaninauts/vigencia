"""Avaliação ponta a ponta (busca, geração e juiz) e calibração do juiz contra rótulos humanos."""

from __future__ import annotations

import json
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from vigencia import geracao, juiz
from vigencia.avaliacao import Pergunta
from vigencia.config import Config
from vigencia.geracao import Resposta
from vigencia.indice import Resultado
from vigencia.juiz import Julgamento

# Estimativa grosseira, só para decidir se vale rodar: português tem ~3,5 caracteres por token, e a
# saída com raciocínio adaptativo em esforço médio fica perto de algumas centenas de tokens.
CARACTERES_POR_TOKEN = 3.5
SAIDA_GERACAO = 800
SAIDA_JUIZ = 400
RESPOSTA_TIPICA = 1500  # caracteres da resposta e das citações enviadas ao juiz

CRITERIOS = ("correta", "fundamentada")


def tokens(texto: str) -> int:
    return math.ceil(len(texto) / CARACTERES_POR_TOKEN)


@dataclass(frozen=True)
class Estimativa:
    perguntas: int
    tokens_entrada: int
    tokens_saida: int
    custo: float | None


def estimar(itens: list[tuple[Pergunta, list[Resultado]]], cfg: Config) -> Estimativa:
    """Custo provável de gerar e julgar cada pergunta, sem chamar a API."""
    entrada_ger = entrada_juiz = 0
    for pergunta, resultados in itens:
        contexto = "".join(r.texto for r in resultados)
        entrada_ger += tokens(geracao.INSTRUCOES + contexto + pergunta.pergunta)
        entrada_juiz += tokens(
            juiz.INSTRUCOES + pergunta.pergunta + pergunta.resposta_esperada
        ) + math.ceil(RESPOSTA_TIPICA / CARACTERES_POR_TOKEN)
    n = len(itens)
    saida_ger, saida_juiz = n * SAIDA_GERACAO, n * SAIDA_JUIZ
    custo_ger = geracao.custo(cfg.geracao.modelo, entrada_ger, saida_ger)
    custo_juiz = geracao.custo(cfg.juiz.modelo, entrada_juiz, saida_juiz)
    total = None if custo_ger is None or custo_juiz is None else custo_ger + custo_juiz
    return Estimativa(n, entrada_ger + entrada_juiz, saida_ger + saida_juiz, total)


def registro(
    pergunta: Pergunta,
    posicao: int | None,
    resultados: list[Resultado],
    resposta: Resposta,
    julgamento: Julgamento,
    latencias_ms: dict[str, int],
) -> dict[str, Any]:
    """Uma linha da execução: o que foi perguntado, recuperado, respondido e julgado."""
    custos = [resposta.custo_estimado(), julgamento.custo_estimado()]
    return {
        "id": pergunta.id,
        "tipo": pergunta.tipo,
        "origem": pergunta.origem,
        "posicao_acerto": posicao,
        "recuperados": [f"{r.chave} v{r.versao} p.{r.pagina_inicio}" for r in resultados],
        "resposta": resposta.texto,
        "citacoes": [asdict(c) for c in resposta.citacoes],
        "recusou": resposta.recusou,
        "juiz": asdict(julgamento.veredito),
        "modelos": {"geracao": resposta.modelo, "juiz": julgamento.modelo},
        "tokens": {
            "geracao": [resposta.tokens_entrada, resposta.tokens_saida],
            "juiz": [julgamento.tokens_entrada, julgamento.tokens_saida],
        },
        "custo": None if None in custos else sum(c for c in custos if c is not None),
        "latencia_ms": latencias_ms,
    }


def caminho(raiz: Path, nome_config: str, agora: datetime) -> Path:
    return raiz / f"{agora:%Y%m%d-%H%M}-{nome_config}.jsonl"


def ler(caminho_: Path) -> list[dict[str, Any]]:
    linhas = caminho_.read_text("utf-8").splitlines()
    return [json.loads(linha) for linha in linhas if linha.strip()]


def gravar(caminho_: Path, registros: Iterable[dict[str, Any]]) -> None:
    caminho_.parent.mkdir(parents=True, exist_ok=True)
    texto = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros)
    caminho_.write_text(texto, "utf-8")


@dataclass(frozen=True)
class Taxas:
    n: int
    correta: float
    fundamentada: float
    passa: float
    """Correta e fundamentada ao mesmo tempo."""


def resumir(registros: list[dict[str, Any]]) -> dict[str, Taxas]:
    """Taxas do juiz no geral, por origem e por tipo de pergunta."""
    grupos: dict[str, list[dict[str, Any]]] = {"geral": registros}
    for r in registros:
        grupos.setdefault(f"origem {r['origem']}", []).append(r)
        grupos.setdefault(f"tipo {r['tipo']}", []).append(r)
    saida = {}
    for nome, itens in grupos.items():
        n = len(itens)
        correta = sum(r["juiz"]["correta"] for r in itens)
        fundamentada = sum(r["juiz"]["fundamentada"] for r in itens)
        passa = sum(r["juiz"]["correta"] and r["juiz"]["fundamentada"] for r in itens)
        saida[nome] = Taxas(n, correta / n, fundamentada / n, passa / n)
    return saida


def modelo_de_rotulos(
    registros: list[dict[str, Any]], perguntas: list[Pergunta]
) -> list[dict[str, Any]]:
    """Linhas para o humano rotular. Os critérios vêm vazios para não ancorar no juiz."""
    por_id = {p.id: p for p in perguntas}
    return [
        {
            "id": r["id"],
            "pergunta": por_id[r["id"]].pergunta,
            "resposta_esperada": por_id[r["id"]].resposta_esperada,
            "resposta": r["resposta"],
            "citacoes": [f"[{c['resultado']}] {c['titulo']}: {c['trecho']}" for c in r["citacoes"]],
            "correta": None,
            "fundamentada": None,
            "comentario": "",
        }
        for r in registros
    ]


def kappa(a: list[bool], b: list[bool]) -> float:
    """Kappa de Cohen: concordância acima do acaso (1 é perfeita, 0 é a do acaso)."""
    n = len(a)
    if n == 0:
        return 0.0
    observada = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    esperada = pa * pb + (1 - pa) * (1 - pb)
    return 1.0 if esperada == 1 else (observada - esperada) / (1 - esperada)


@dataclass(frozen=True)
class Concordancia:
    n: int
    concordancia: float
    kappa: float
    divergentes: list[str]


def calibrar(
    registros: list[dict[str, Any]], rotulos: list[dict[str, Any]]
) -> dict[str, Concordancia]:
    """Compara o juiz com os rótulos humanos preenchidos, critério por critério."""
    juiz_por_id = {r["id"]: r["juiz"] for r in registros}
    saida = {}
    for criterio in CRITERIOS:
        pares = [
            (rot["id"], bool(juiz_por_id[rot["id"]][criterio]), bool(rot[criterio]))
            for rot in rotulos
            if rot.get(criterio) is not None and rot["id"] in juiz_por_id
        ]
        do_juiz = [p[1] for p in pares]
        do_humano = [p[2] for p in pares]
        iguais = sum(x == y for x, y in zip(do_juiz, do_humano, strict=True))
        saida[criterio] = Concordancia(
            n=len(pares),
            concordancia=iguais / len(pares) if pares else 0.0,
            kappa=kappa(do_juiz, do_humano),
            divergentes=[i for i, x, y in pares if x != y],
        )
    return saida
