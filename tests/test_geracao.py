from datetime import date

import pytest
from anthropic.types.beta import BetaMessage

from vigencia.config import ConfigGeracao
from vigencia.geracao import interpretar, montar_conteudo, titulo
from vigencia.indice import Resultado

R1 = Resultado("HXPO8VLbh4o=", 7, "NT 2025.002", "1.52", date(2026, 10, 1), 25, 26, "linha", 0.4)
R2 = Resultado("HXPO8VLbh4o=", 9, "NT 2025.002", "1.52", date(2026, 10, 1), 43, 43, "regra", 0.5)


def mensagem(conteudo: list[dict[str, object]], stop_reason: str = "end_turn") -> BetaMessage:
    return BetaMessage.model_validate(
        {
            "id": "msg_teste",
            "type": "message",
            "role": "assistant",
            "model": "claude-opus-5-5",
            "content": conteudo,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {"input_tokens": 2000, "output_tokens": 100},
        }
    )


def citacao(indice: int, trecho: str) -> dict[str, object]:
    return {
        "type": "search_result_location",
        "search_result_index": indice,
        "source": "https://exemplo/x#page=25",
        "title": "NT 2025.002 v1.52, p. 25-26",
        "cited_text": trecho,
        "start_block_index": 0,
        "end_block_index": 1,
    }


def test_titulo_mostra_faixa_de_paginas() -> None:
    assert titulo(R1) == "NT 2025.002 v1.52, p. 25-26"
    assert titulo(R2) == "NT 2025.002 v1.52, p. 43"


def test_cada_resultado_vira_search_result_com_citacao_e_link_para_a_pagina() -> None:
    blocos = montar_conteudo("pergunta?", [R1, R2])
    primeiro = blocos[0]
    assert primeiro["type"] == "search_result"
    assert primeiro["citations"] == {"enabled": True}
    assert primeiro["source"].endswith("conteudo=HXPO8VLbh4o%3D#page=25")
    assert blocos[-1] == {"type": "text", "text": "pergunta?"}


def test_interpretar_marca_o_resultado_citado() -> None:
    msg = mensagem(
        [
            {
                "type": "text",
                "text": "O campo tem 6 posições",
                "citations": [citacao(0, "C 1-1 6")],
            },
            {"type": "text", "text": ".", "citations": None},
        ]
    )
    resposta = interpretar(msg)
    assert resposta.texto == "O campo tem 6 posições[1]."
    assert [(c.resultado, c.trecho) for c in resposta.citacoes] == [(1, "C 1-1 6")]
    assert not resposta.recusou


def test_custo_estimado_pelo_modelo() -> None:
    resposta = interpretar(mensagem([{"type": "text", "text": "ok", "citations": None}]))
    assert resposta.custo_estimado() == pytest.approx((2000 * 4 + 100 * 20) / 1_000_000)


def test_recusa_e_registrada() -> None:
    assert interpretar(mensagem([], stop_reason="refusal")).recusou


def test_esforco_invalido_e_barrado_na_config() -> None:
    with pytest.raises(ValueError, match="esforço"):
        ConfigGeracao(modelo="claude-opus-5-5", esforco="altissimo", max_tokens=100)  # type: ignore[arg-type]
