from geosampa_lote_analyzer.utils.text import match_keywords, normalize_text


def test_normalize_text_removes_accents() -> None:
    assert normalize_text("Área Pública / Preservação") == "area publica preservacao"


def test_match_keywords_with_accents() -> None:
    matches = match_keywords("Camada de Área Pública Municipal", ["area publica", "zeis"])
    assert matches == ["area publica"]

