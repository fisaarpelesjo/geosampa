from geosampa_lote_analyzer.services.lote_service import build_lote_info


def test_sql_completo_when_digit_exists() -> None:
    info = build_lote_info(
        {
            "cd_setor_fiscal": "123",
            "cd_quadra_fiscal": "045",
            "cd_lote": "0067",
            "cd_digito_sql": "7",
        }
    )
    assert info.sql_base == "123.045.0067"
    assert info.sql_completo == "123.045.0067-7"


def test_lote_info_is_tolerant_to_missing_fields() -> None:
    info = build_lote_info({})
    assert info.sql_base is None
    assert info.raw_properties == {}
