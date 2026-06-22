import csv

from geosampa_lote_analyzer.services.risk_matrix_service import RiskMatrixService


def test_classifies_risk_levels_by_category_and_ratio(tmp_path) -> None:
    intersections = tmp_path / "intersections.csv"
    _write_csv(
        intersections,
        [
            {
                "layer_type_name": "geoportal:manancial_billings",
                "layer_title": "Manancial Billings",
                "intersects_count": "3",
                "intersection_ratio": "0.6",
                "status": "INTERSECTS",
                "matched_keywords": "manancial",
            },
            {
                "layer_type_name": "geoportal:pde_parque_municipal",
                "layer_title": "Parques Municipais",
                "intersects_count": "1",
                "intersection_ratio": "0.07",
                "status": "INTERSECTS",
                "matched_keywords": "parque",
            },
            {
                "layer_type_name": "geoportal:lote_cidadao",
                "layer_title": "lote_cidadao",
                "intersects_count": "1",
                "intersection_ratio": "1.0",
                "status": "CONTAINS_TARGET",
                "matched_keywords": "",
            },
            {
                "layer_type_name": "geoportal:sem_achado",
                "layer_title": "Sem achado",
                "intersects_count": "0",
                "intersection_ratio": "0",
                "status": "NO_INTERSECTION",
                "matched_keywords": "",
            },
        ],
    )

    findings, csv_path, json_path = RiskMatrixService().generate(
        intersections_path=intersections,
        csv_path=tmp_path / "risk.csv",
        json_path=tmp_path / "risk.json",
    )

    by_layer = {finding.layer_type_name: finding for finding in findings}
    assert len(findings) == 3
    assert by_layer["geoportal:manancial_billings"].risk_level == "CRITICO"
    assert by_layer["geoportal:pde_parque_municipal"].risk_level == "MEDIO"
    assert by_layer["geoportal:lote_cidadao"].risk_level == "BAIXO"
    assert csv_path.exists()
    assert json_path.exists()


def test_custom_weights_override_defaults(tmp_path) -> None:
    intersections = tmp_path / "intersections.csv"
    _write_csv(
        intersections,
        [
            {
                "layer_type_name": "geoportal:pde_parque_municipal",
                "layer_title": "Parques Municipais",
                "intersects_count": "1",
                "intersection_ratio": "0.07",
                "status": "INTERSECTS",
                "matched_keywords": "parque",
            }
        ],
    )

    findings, _, _ = RiskMatrixService().generate(
        intersections_path=intersections,
        csv_path=tmp_path / "risk.csv",
        json_path=tmp_path / "risk.json",
        weights={"Parque e áreas verdes": 0},
    )

    assert findings[0].risk_level == "BAIXO"


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
