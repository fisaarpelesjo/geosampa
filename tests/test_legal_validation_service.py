import csv

from geosampa_lote_analyzer.services.legal_validation_service import LegalValidationService


def test_legal_validation_generates_legal_and_process_tasks(tmp_path) -> None:
    references = tmp_path / "refs.csv"
    _write_csv(
        references,
        [
            {
                "reference_type": "DECRETO",
                "value": "12.345/2020",
                "year": "2020",
                "source_layer": "camada",
                "source_field": "campo",
            },
            {
                "reference_type": "PROCESSO",
                "value": "12.345.678.90*12",
                "year": "",
                "source_layer": "camada",
                "source_field": "processo",
            },
            {
                "reference_type": "PLANTA",
                "value": "A-1",
                "year": "",
                "source_layer": "camada",
                "source_field": "planta",
            },
        ],
    )

    rows, csv_path, json_path = LegalValidationService().generate(
        document_references_path=references,
        csv_path=tmp_path / "tasks.csv",
        json_path=tmp_path / "tasks.json",
    )

    assert csv_path.exists()
    assert json_path.exists()
    assert len(rows) == 2
    assert rows[0]["validation_channel"] == "LEGISLACAO_DIARIO_OFICIAL"
    assert rows[1]["validation_channel"] == "PROCESSOS_ADMINISTRATIVOS"


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
