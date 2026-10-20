import pytest

from vigencia.busca import Bm25, Buscador, fundir_rrf, tem_codigo
from vigencia.config import ConfigBusca
from vigencia.indice import consulta_ou

DOCS = {
    ("a", 0): {"rejeicao": 1, "1115": 1, "grupo": 1, "ibscbs": 1},
    ("a", 1): {"grupo": 3, "nota": 2},
    ("b", 0): {"nota": 1, "credit": 1, "1201": 1},
}


def test_bm25_prefere_termo_raro() -> None:
    ranking = Bm25(DOCS).pontuar(["grupo", "1115"], k=3)
    assert ranking[0][0] == ("a", 0)


def test_bm25_ignora_termo_fora_do_vocabulario() -> None:
    assert Bm25(DOCS).pontuar(["inexistente"], k=3) == []


def test_bm25_respeita_k() -> None:
    assert len(Bm25(DOCS).pontuar(["nota", "grupo"], k=1)) == 1


def test_rrf_premia_quem_aparece_nas_duas_listas() -> None:
    vetorial = [("x", 0), ("y", 0), ("z", 0)]
    lexical = [("y", 0), ("w", 0)]
    fundido = fundir_rrf([vetorial, lexical], rrf_k=60, k=2)
    assert [c for c, _ in fundido] == [("y", 0), ("x", 0)]
    assert fundido[0][1] == pytest.approx(1 / 62 + 1 / 61)


def test_consulta_ou_escapa_aspas() -> None:
    assert consulta_ou(["d'agua", "1115"]) == "'d''agua' | '1115'"


def test_metodo_invalido_e_barrado_na_config() -> None:
    with pytest.raises(ValueError, match="método"):
        ConfigBusca(top_k=5, metodo="magica")  # type: ignore[arg-type]


def test_busca_vetorial_exige_embedding() -> None:
    with pytest.raises(ValueError, match="embedding"):
        Buscador(None, "indice", ConfigBusca(top_k=5, metodo="hibrida"), None)  # type: ignore[arg-type]


def test_rrf_com_peso_favorece_a_lista_pesada() -> None:
    vetorial = [("x", 0), ("y", 0)]
    lexical = [("y", 0), ("x", 0)]
    fundido = fundir_rrf([vetorial, lexical], rrf_k=60, k=2, pesos=[1.0, 2.0])
    assert fundido[0][0] == ("y", 0)


@pytest.mark.parametrize(
    ("pergunta", "esperado"),
    [
        ("O que é a rejeição 1201 e como evito?", True),
        ("Saiu a v1.52 da NT 2025.002. O que mudou?", True),
        ("A regra UB12-10 já vale?", True),
        ("Que cClassTrib usar, 800001?", True),
        ("Qual alíquota de IBS estadual nas notas de 2026? E em 2027?", False),
        ("Um cliente vai emitir devoluções em 20/10/2026.", False),
        ("Quais valores de IBS e CBS aparecem no DANFE?", False),
    ],
)
def test_detecta_codigo_na_pergunta(pergunta: str, esperado: bool) -> None:
    assert tem_codigo(pergunta) is esperado
