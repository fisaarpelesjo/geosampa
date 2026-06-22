from geosampa_lote_analyzer.utils.cql import build_lote_cql, quote_cql_string


def test_quote_cql_string_escapes_single_quote() -> None:
    assert quote_cql_string("D'Água") == "'D''Água'"


def test_build_lote_cql_preserves_leading_zeros() -> None:
    cql = build_lote_cql("123", "045", "0067")
    assert "cd_setor_fiscal='123'" in cql
    assert "cd_quadra_fiscal='045'" in cql
    assert "cd_lote='0067'" in cql
