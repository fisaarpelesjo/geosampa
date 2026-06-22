from geosampa_lote_analyzer.utils.geo import normalize_crs


def test_normalize_crs_keeps_epsg_code() -> None:
    assert normalize_crs("EPSG:31983") == "EPSG:31983"


def test_normalize_crs_from_urn() -> None:
    assert normalize_crs("urn:ogc:def:crs:EPSG::31983") == "EPSG:31983"


def test_normalize_crs_empty_value() -> None:
    assert normalize_crs("") is None
