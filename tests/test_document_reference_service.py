import json

from geosampa_lote_analyzer.services.document_reference_service import DocumentReferenceService


def test_document_reference_extracts_known_fields(tmp_path) -> None:
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "layer_type_name": "camada_teste",
                    "tx_planta": "A-1.234",
                    "tx_numero_processo": "12.345.678.90*12",
                    "tx_registro_completo": "Matrícula n° 12.345",
                    "tx_instrumento_legal_criacao": "Dec. 12.345/08",
                },
                "geometry": None,
            }
        ],
    }
    path = tmp_path / "intersections.geojson"
    path.write_text(json.dumps(data), encoding="utf-8")

    references, csv_path, json_path = DocumentReferenceService().generate(
        intersections_path=path,
        csv_path=tmp_path / "refs.csv",
        json_path=tmp_path / "refs.json",
    )

    values_by_type = {(reference.reference_type, reference.value) for reference in references}
    assert ("PLANTA", "A-1.234") in values_by_type
    assert ("PROCESSO", "12.345.678.90*12") in values_by_type
    assert ("MATRICULA", "12.345") in values_by_type
    assert ("DECRETO", "12.345/08") in values_by_type
    assert csv_path.exists()
    assert json_path.exists()


def test_document_reference_deduplicates_same_field_and_layer(tmp_path) -> None:
    data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "layer_type_name": "camada_teste",
                    "tx_planta": "A-1.234",
                },
                "geometry": None,
            },
            {
                "type": "Feature",
                "properties": {
                    "layer_type_name": "camada_teste",
                    "tx_planta": "A-1.234",
                },
                "geometry": None,
            },
        ],
    }
    path = tmp_path / "intersections.geojson"
    path.write_text(json.dumps(data), encoding="utf-8")

    references, _, _ = DocumentReferenceService().generate(
        intersections_path=path,
        csv_path=tmp_path / "refs.csv",
        json_path=tmp_path / "refs.json",
    )

    assert sum(reference.reference_type == "PLANTA" for reference in references) == 1
