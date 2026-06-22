import csv
import json

from geosampa_lote_analyzer.services.dossier_service import DossierService


def test_dossier_generates_markdown_and_json(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text(
        json.dumps(
            {
                "sql_base": "123.045.0067",
                "tipo_quadra": "MUNICIPAL",
                "tipo_lote": "MUNICIPAL",
            }
        ),
        encoding="utf-8",
    )
    intersections = tmp_path / "intersections.csv"
    _write_csv(
        intersections,
        [
            {
                "layer_type_name": "geoportal:planta_dup_dis_pd",
                "layer_title": "Plantas DUP DIS",
                "intersects_count": "2",
                "intersection_area_m2": "100",
                "intersection_ratio": "0.5",
                "status": "INTERSECTS",
                "matched_keywords": "dup,dis",
            }
        ],
    )
    references = tmp_path / "refs.csv"
    _write_csv(
        references,
        [
            {
                "reference_type": "PLANTA",
                "value": "A-1",
                "source_layer": "geoportal:planta_dup_dis_pd",
                "source_field": "tx_planta",
                "validation_status": "PENDENTE",
                "validation_hint": "Validar em fonte oficial.",
            }
        ],
    )
    sources = tmp_path / "sources.csv"
    _write_csv(
        sources,
        [
            {
                "source_name": "Legislação Municipal",
                "title": "Catálogo",
                "validation_categories": "DOCUMENTO_OFICIAL",
                "relevance_score": "5",
                "status": "MANUAL",
            }
        ],
    )

    markdown_path, json_path = DossierService().generate(
        target_properties_path=target,
        intersections_path=intersections,
        document_references_path=references,
        official_sources_path=sources,
        markdown_path=tmp_path / "dossie.md",
        json_path=tmp_path / "dossie.json",
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "DUP/DIS e desapropriação" in markdown
    assert "Referências documentais pendentes" in markdown
    assert json_path.exists()


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
