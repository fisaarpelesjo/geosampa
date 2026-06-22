import csv
import json

from geosampa_lote_analyzer.services.cadastral_divergence_service import (
    CadastralDivergenceService,
)


def test_flags_divergence_when_cadastro_empty_but_occupation_found(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text(
        json.dumps(
            {
                "codigo_contribuinte": None,
                "numero_porta": None,
                "area_construida_m2": None,
            }
        ),
        encoding="utf-8",
    )
    occupation = tmp_path / "occupation.csv"
    _write_csv(
        occupation,
        [
            {
                "layer_type_name": "geoportal:edificacao",
                "category": "EDIFICACAO",
                "intersects_count": "1",
            },
            {
                "layer_type_name": "geoportal:drenagem",
                "category": "DRENAGEM",
                "intersects_count": "0",
            },
        ],
    )

    divergences, csv_path, json_path = CadastralDivergenceService().generate(
        target_properties_path=target,
        occupation_indicators_path=occupation,
        csv_path=tmp_path / "div.csv",
        json_path=tmp_path / "div.json",
    )

    by_layer = {item.layer_type_name: item for item in divergences}
    assert by_layer["geoportal:edificacao"].divergencia is True
    assert by_layer["geoportal:edificacao"].cadastral_field == "area_construida_m2"
    assert by_layer["geoportal:drenagem"].divergencia is False
    assert csv_path.exists()
    assert json_path.exists()


def test_no_divergence_when_cadastro_filled(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"area_construida_m2": 120.5}), encoding="utf-8")
    occupation = tmp_path / "occupation.csv"
    _write_csv(
        occupation,
        [
            {
                "layer_type_name": "geoportal:edificacao",
                "category": "EDIFICACAO",
                "intersects_count": "2",
            }
        ],
    )

    divergences, _, _ = CadastralDivergenceService().generate(
        target_properties_path=target,
        occupation_indicators_path=occupation,
        csv_path=tmp_path / "div.csv",
        json_path=tmp_path / "div.json",
    )

    assert divergences[0].divergencia is False


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
