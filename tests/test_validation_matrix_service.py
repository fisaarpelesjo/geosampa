import csv

from geosampa_lote_analyzer.services.validation_matrix_service import ValidationMatrixService


def test_validation_matrix_links_findings_to_sources(tmp_path) -> None:
    intersections = tmp_path / "intersections.csv"
    _write_csv(
        intersections,
        [
            {
                "layer_type_name": "geoportal:planta_dup_dis_pd",
                "layer_title": "Plantas DUP DIS",
                "intersects_count": "1",
                "matched_keywords": "dup,dis",
            }
        ],
    )
    references = tmp_path / "refs.csv"
    _write_csv(
        references,
        [
            {
                "source_layer": "geoportal:planta_dup_dis_pd",
                "reference_type": "DISPOSITIVO_LEGAL",
                "value": "123/2020",
            }
        ],
    )
    sources = tmp_path / "sources.csv"
    _write_csv(
        sources,
        [
            {
                "title": "Catálogo de Legislação Municipal",
                "source_name": "Legislação Municipal",
                "validation_categories": "DOCUMENTO_OFICIAL,DESAPROPRIACAO",
                "relevance_score": "5",
            }
        ],
    )

    rows, csv_path, json_path = ValidationMatrixService().generate(
        intersections_path=intersections,
        document_references_path=references,
        official_sources_path=sources,
        csv_path=tmp_path / "matrix.csv",
        json_path=tmp_path / "matrix.json",
    )

    assert csv_path.exists()
    assert json_path.exists()
    assert rows[0]["finding_category"] == "DUP/DIS e desapropriação"
    assert rows[0]["document_reference_count"] == 1
    assert "Catálogo de Legislação Municipal" in rows[0]["recommended_sources"]


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
