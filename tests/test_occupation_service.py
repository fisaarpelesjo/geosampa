import csv
import json

from geosampa_lote_analyzer.services.occupation_service import OccupationService


def test_occupation_finds_infrastructure_layers_with_geometry_types(tmp_path) -> None:
    intersections = tmp_path / "intersections.csv"
    _write_csv(
        intersections,
        [
            {
                "layer_type_name": "geoportal:edificacao",
                "layer_title": "Edificações",
                "intersects_count": "1",
                "intersection_ratio": "0.1",
                "status": "INTERSECTS",
                "matched_keywords": "edificacao",
            },
            {
                "layer_type_name": "geoportal:iluminacao_publica",
                "layer_title": "Pontos de iluminação pública",
                "intersects_count": "3",
                "intersection_ratio": "0.0",
                "status": "TOUCHES_ONLY",
                "matched_keywords": "iluminacao",
            },
            {
                "layer_type_name": "geoportal:planta_dup_dis_pd",
                "layer_title": "Plantas DUP DIS",
                "intersects_count": "2",
                "intersection_ratio": "0.5",
                "status": "INTERSECTS",
                "matched_keywords": "dup,dis",
            },
            {
                "layer_type_name": "geoportal:sem_intersecao",
                "layer_title": "Edificações sem interseção",
                "intersects_count": "0",
                "intersection_ratio": "0.0",
                "status": "NO_INTERSECTION",
                "matched_keywords": "edificacao",
            },
        ],
    )
    geojson = tmp_path / "intersections.geojson"
    geojson.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"layer_type_name": "geoportal:edificacao"},
                        "geometry": {"type": "Polygon", "coordinates": []},
                    },
                    {
                        "type": "Feature",
                        "properties": {"layer_type_name": "geoportal:iluminacao_publica"},
                        "geometry": {"type": "Point", "coordinates": [0, 0]},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    findings, csv_path, json_path = OccupationService().generate(
        intersections_path=intersections,
        intersections_geojson_path=geojson,
        csv_path=tmp_path / "occupation.csv",
        json_path=tmp_path / "occupation.json",
    )

    by_layer = {finding.layer_type_name: finding for finding in findings}
    assert set(by_layer) == {"geoportal:edificacao", "geoportal:iluminacao_publica"}
    assert by_layer["geoportal:edificacao"].category == "EDIFICACAO"
    assert by_layer["geoportal:edificacao"].geometry_types == ["Polygon"]
    assert by_layer["geoportal:iluminacao_publica"].category == "ILUMINACAO"
    assert by_layer["geoportal:iluminacao_publica"].geometry_types == ["Point"]
    assert all(finding.note for finding in findings)
    assert csv_path.exists()
    assert json_path.exists()


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
