from geosampa_lote_analyzer.services.source_discovery_service import SourceDiscoveryService


class FakeCkanClient:
    def package_search(self, query: str, rows: int = 10) -> dict:
        return {
            "success": True,
            "result": {
                "results": [
                    {
                        "id": "dataset-1",
                        "name": "dataset-teste",
                        "title": "Dataset de Teste de Habitação",
                        "notes": "Descrição sobre parque linear, manancial e habitação.",
                        "resources": [
                            {"format": "CSV"},
                            {"format": "GeoJSON"},
                            {"format": "CSV"},
                        ],
                        "organization": {"title": "Órgão Teste"},
                        "score": 1.5,
                    }
                ]
            },
        }


def test_source_discovery_adds_static_and_ckan_sources(tmp_path) -> None:
    service = SourceDiscoveryService(ckan_client=FakeCkanClient())
    sources, csv_path, json_path = service.discover(
        ["teste"],
        rows_per_keyword=1,
        csv_path=tmp_path / "sources.csv",
        json_path=tmp_path / "sources.json",
    )

    assert csv_path.exists()
    assert json_path.exists()
    assert any(source.source_name == "GeoSampa WFS" for source in sources)
    dataset = next(source for source in sources if source.title == "Dataset de Teste de Habitação")
    assert "HABITACAO" in dataset.validation_categories
    assert "PARQUE" in dataset.validation_categories
    assert "MANANCIAL_APP" in dataset.validation_categories
    assert dataset.relevance_score > 0


def test_source_discovery_deduplicates_ckan_results(tmp_path) -> None:
    service = SourceDiscoveryService(ckan_client=FakeCkanClient())
    sources, _, _ = service.discover(
        ["termo-a", "termo-b"],
        rows_per_keyword=1,
        csv_path=tmp_path / "sources.csv",
        json_path=tmp_path / "sources.json",
    )

    dataset_count = sum(source.title == "Dataset de Teste de Habitação" for source in sources)
    assert dataset_count == 1
