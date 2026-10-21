from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from vigencia import execucao
from vigencia.avaliacao import CitacaoEsperada, Pergunta
from vigencia.config import carregar
from vigencia.geracao import Citacao, Resposta
from vigencia.indice import Resultado
from vigencia.juiz import Julgamento, Veredito, montar_pedido

CONFIG = carregar(Path(__file__).parents[1] / "configs" / "cabecalho-rerank-20.toml")
PERGUNTA = Pergunta(
    id="regra-01",
    origem="real",
    persona="suporte",
    tipo="regra de validação",
    pergunta="Deu rejeição 1037. O que é?",
    resposta_esperada="Regra UB56-10: pCBS deve ser 0,9% em 2025 e 2026.",
    citacoes=[CitacaoEsperada("NT 2025.002", "1.52", 47)],
    inspiracao=None,
    notas="",
    revisado=True,
)
RESULTADO = Resultado("id=", 1, "NT 2025.002", "1.52", date(2026, 10, 1), 47, 47, "x" * 700, 0.9)
RESPOSTA = Resposta(
    texto="pCBS precisa ser 0,9%[1].",
    citacoes=[Citacao(1, "NT 2025.002 v1.52, p. 47", "u", "deve ser igual a 0,9%")],
    recusou=False,
    modelo="claude-opus-5-5",
    tokens_entrada=3000,
    tokens_saida=500,
)


def julgamento(correta: bool, fundamentada: bool) -> Julgamento:
    return Julgamento(Veredito("ok", correta, fundamentada), "claude-opus-5-5", 1000, 200)


def registro(id_: str, tipo: str, correta: bool, fundamentada: bool) -> dict[str, Any]:
    pergunta = Pergunta(**{**PERGUNTA.__dict__, "id": id_, "tipo": tipo})
    return execucao.registro(
        pergunta, 1, [RESULTADO], RESPOSTA, julgamento(correta, fundamentada), {"busca": 1}
    )


def test_estimativa_cresce_com_o_contexto_e_tem_custo() -> None:
    curta = execucao.estimar([(PERGUNTA, [RESULTADO])], CONFIG)
    longa = execucao.estimar([(PERGUNTA, [RESULTADO] * 5)], CONFIG)
    assert longa.tokens_entrada > curta.tokens_entrada
    assert curta.custo is not None and 0 < curta.custo < 0.1


def test_registro_soma_custo_de_geracao_e_juiz() -> None:
    r = registro("regra-01", "regra de validação", True, True)
    assert r["custo"] == pytest.approx((3000 * 4 + 500 * 20 + 1000 * 4 + 200 * 20) / 1_000_000)
    assert r["juiz"] == {"critica": "ok", "correta": True, "fundamentada": True}


def test_resumir_por_tipo() -> None:
    regs = [
        registro("a", "temporal", True, True),
        registro("b", "temporal", True, False),
        registro("c", "diff", False, False),
    ]
    taxas = execucao.resumir(regs)
    assert taxas["geral"].passa == pytest.approx(1 / 3)
    assert taxas["tipo temporal"].correta == 1.0
    assert taxas["tipo temporal"].fundamentada == 0.5


def test_kappa() -> None:
    assert execucao.kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert execucao.kappa([True, True, False, False], [True, False, True, False]) == 0.0


def test_calibrar_ignora_rotulo_vazio_e_lista_divergencias() -> None:
    regs = [registro("a", "temporal", True, True), registro("b", "diff", False, True)]
    rotulos = [
        {"id": "a", "correta": True, "fundamentada": None},
        {"id": "b", "correta": True, "fundamentada": True},
    ]
    resultado = execucao.calibrar(regs, rotulos)
    assert resultado["correta"].n == 2
    assert resultado["correta"].divergentes == ["b"]
    assert resultado["fundamentada"].n == 1


def test_modelo_de_rotulos_vem_sem_julgamento() -> None:
    linhas = execucao.modelo_de_rotulos([registro("regra-01", "regra", True, True)], [PERGUNTA])
    assert linhas[0]["correta"] is None and linhas[0]["fundamentada"] is None
    assert linhas[0]["resposta_esperada"] == PERGUNTA.resposta_esperada


def test_pedido_ao_juiz_traz_esperada_resposta_e_citacoes() -> None:
    pedido = montar_pedido(PERGUNTA, RESPOSTA)
    assert "<resposta_esperada>" in pedido and "UB56-10" in pedido
    assert '[1] NT 2025.002 v1.52, p. 47: "deve ser igual a 0,9%"' in pedido


def test_caminho_da_execucao() -> None:
    destino = execucao.caminho(Path("evals/execucoes"), "base", datetime(2026, 10, 20, 21, 5))
    assert destino == Path("evals/execucoes/20261020-2105-base.jsonl")


def test_ida_e_volta_jsonl(tmp_path: Path) -> None:
    regs = [registro("a", "temporal", True, True)]
    execucao.gravar(tmp_path / "x.jsonl", regs)
    assert execucao.ler(tmp_path / "x.jsonl") == regs
