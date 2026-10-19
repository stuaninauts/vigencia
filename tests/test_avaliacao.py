from datetime import date
from pathlib import Path

import pytest

from vigencia.avaliacao import (
    CitacaoEsperada,
    carregar_golden,
    metricas,
    posicao_do_acerto,
)
from vigencia.indice import Resultado

GOLDEN = Path(__file__).parents[1] / "evals" / "golden" / "dev" / "perguntas.jsonl"


def resultado(chave: str, inicio: int, fim: int) -> Resultado:
    return Resultado("id=", chave, "1.52", date(2026, 10, 1), inicio, fim, "texto", 0.5)


def test_golden_dev_e_valido_e_tem_ids_unicos() -> None:
    perguntas = carregar_golden(GOLDEN)
    assert len({p.id for p in perguntas}) == len(perguntas)
    for p in perguntas:
        assert p.tipo in {
            "consulta de campo",
            "regra de validação",
            "temporal",
            "diff",
            "agregada",
            "multi-hop",
            "sem resposta",
        }
        assert p.origem in {"real", "sintetica"}, p.id
        assert (p.persona is None) == (p.origem == "sintetica"), p.id
        if p.tipo == "agregada":
            assert not p.citacoes, p.id
        elif p.tipo != "sem resposta":
            assert p.citacoes, p.id


def test_golden_dev_tem_15_reais_e_5_sinteticas() -> None:
    origens = [p.origem for p in carregar_golden(GOLDEN)]
    assert (origens.count("real"), origens.count("sintetica")) == (15, 5)


def test_acerto_quando_a_pagina_esta_na_faixa_do_chunk() -> None:
    esperada = [CitacaoEsperada("NT 2025.002", "1.52", 26)]
    resultados = [resultado("NT 2025.002", 40, 41), resultado("NT 2025.002", 25, 26)]
    assert posicao_do_acerto(resultados, esperada) == 2


def test_versao_diferente_nao_conta() -> None:
    esperada = [CitacaoEsperada("NT 2025.002", "1.51", 26)]
    assert posicao_do_acerto([resultado("NT 2025.002", 25, 26)], esperada) is None


def test_metricas() -> None:
    m = metricas([1, None, 2, None])
    assert m.recall_at_k == 0.5
    assert m.mrr == pytest.approx((1 + 0.5) / 4)
