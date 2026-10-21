from pathlib import Path

from vigencia.config import carregar

BASELINE = Path(__file__).parents[1] / "configs" / "baseline.toml"


def test_carrega_o_baseline() -> None:
    cfg = carregar(BASELINE)
    assert cfg.nome == "baseline"
    assert cfg.chunking.estrategia == "tamanho-fixo"
    assert cfg.embedding.modelo == "BAAI/bge-m3"
    assert len(cfg.impressao) == 12


def test_impressao_muda_quando_o_arquivo_muda(tmp_path: Path) -> None:
    copia = tmp_path / "variante.toml"
    copia.write_text(
        BASELINE.read_text("utf-8").replace("tamanho = 1500", "tamanho = 800"), "utf-8"
    )
    assert carregar(copia).impressao != carregar(BASELINE).impressao


def test_mudar_a_geracao_nao_muda_o_indice(tmp_path: Path) -> None:
    copia = tmp_path / "outro-modelo.toml"
    copia.write_text(
        BASELINE.read_text("utf-8").replace('esforco = "medium"', 'esforco = "low"'), "utf-8"
    )
    assert carregar(copia).impressao == carregar(BASELINE).impressao
