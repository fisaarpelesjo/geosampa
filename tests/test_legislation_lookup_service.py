import csv

from geosampa_lote_analyzer.services.legislation_lookup_service import LegislationLookupService


def test_legislation_lookup_builds_search_url_and_dedupes(tmp_path) -> None:
    references = tmp_path / "document_references.csv"
    _write_csv(
        references,
        [
            {
                "reference_type": "DECRETO",
                "value": "12.345/08",
                "year": "2008",
            },
            {
                "reference_type": "DECRETO",
                "value": "12.345/08",
                "year": "2008",
            },
            {
                "reference_type": "LEI",
                "value": "16.402/2016",
                "year": "2016",
            },
            {
                "reference_type": "PLANTA",
                "value": "A-1.234",
                "year": "",
            },
        ],
    )

    lookups, csv_path, json_path = LegislationLookupService().generate(
        document_references_path=references,
        csv_path=tmp_path / "lookup.csv",
        json_path=tmp_path / "lookup.json",
    )

    assert len(lookups) == 2
    decreto = next(item for item in lookups if item.reference_type == "DECRETO")
    assert decreto.number == "12345"
    assert decreto.year == "2008"
    assert decreto.search_url == "https://legislacao.prefeitura.sp.gov.br/busca?numero=12345&ano=2008"
    assert csv_path.exists()
    assert json_path.exists()


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
