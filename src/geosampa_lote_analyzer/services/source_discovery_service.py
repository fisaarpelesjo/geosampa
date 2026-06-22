import csv
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.clients.ckan import CkanClient
from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.domain.source_keywords import DEFAULT_SOURCE_KEYWORDS
from geosampa_lote_analyzer.domain.sources import OfficialSource
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json


class SourceDiscoveryService:
    def __init__(self, ckan_client: CkanClient | None = None) -> None:
        self.ckan_client = ckan_client or CkanClient()

    def discover(
        self,
        keywords: list[str] | None = None,
        rows_per_keyword: int = 5,
        csv_path: Path = PROCESSED_DIR / "official_sources_inventory.csv",
        json_path: Path = PROCESSED_DIR / "official_sources_inventory.json",
    ) -> tuple[list[OfficialSource], Path, Path]:
        keywords = keywords or DEFAULT_SOURCE_KEYWORDS
        sources = self._static_sources()
        seen = {self._source_key(source) for source in sources}

        for keyword in keywords:
            data = self.ckan_client.package_search(keyword, rows=rows_per_keyword)
            for dataset in data.get("result", {}).get("results", []):
                source = self._source_from_ckan_dataset(keyword, dataset)
                key = self._source_key(source)
                if key in seen:
                    continue
                seen.add(key)
                sources.append(source)

        self._write_csv(csv_path, sources)
        write_json(json_path, [source.model_dump() for source in sources])
        return sources, csv_path, json_path

    def _static_sources(self) -> list[OfficialSource]:
        return [
            OfficialSource(
                source_type="wfs",
                source_name="GeoSampa WFS",
                title="Serviço WFS do GeoSampa",
                url="https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows",
                status="API",
                notes="Fonte vetorial principal para camadas geoespaciais.",
            ),
            OfficialSource(
                source_type="wms",
                source_name="GeoSampa WMS",
                title="Serviço WMS do GeoSampa",
                url="https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows",
                status="API",
                notes="Fonte cartográfica para visualização e conferência.",
            ),
            OfficialSource(
                source_type="portal",
                source_name="Legislação Municipal",
                title="Catálogo de Legislação Municipal",
                url="https://legislacao.prefeitura.sp.gov.br/",
                status="MANUAL",
                notes="Útil para validar leis, decretos e dispositivos legais.",
            ),
            OfficialSource(
                source_type="portal",
                source_name="Portal de Processos Administrativos",
                title="Consulta de Processos Administrativos",
                url="https://processos.prefeitura.sp.gov.br/",
                status="MANUAL",
                notes="Útil para consultar processos por número e andamento.",
            ),
            OfficialSource(
                source_type="portal",
                source_name="Diário Oficial do Município",
                title="Diário Oficial da Cidade de São Paulo",
                url="https://diariooficial.prefeitura.sp.gov.br/",
                status="MANUAL",
                notes="Útil para confirmar publicações oficiais.",
            ),
        ]

    def _source_from_ckan_dataset(self, keyword: str, dataset: dict[str, Any]) -> OfficialSource:
        resources = dataset.get("resources") or []
        formats = sorted(
            {
                str(resource.get("format") or "").upper()
                for resource in resources
                if resource.get("format")
            }
        )
        organization = dataset.get("organization") or {}
        return OfficialSource(
            source_type="ckan_dataset",
            source_name="Portal de Dados Abertos",
            title=str(dataset.get("title") or dataset.get("name") or ""),
            url=str(dataset.get("url") or dataset.get("metadata_modified") or ""),
            query=keyword,
            description=dataset.get("notes"),
            organization=organization.get("title") or organization.get("name"),
            resource_formats=formats,
            resource_count=len(resources),
            score=dataset.get("score"),
            status="API",
            notes="Dataset encontrado via API CKAN do Portal de Dados Abertos.",
            raw={
                "id": dataset.get("id"),
                "name": dataset.get("name"),
                "metadata_modified": dataset.get("metadata_modified"),
            },
        )

    def _source_key(self, source: OfficialSource) -> tuple[str, str, str]:
        return source.source_type, source.source_name, source.title

    def _write_csv(self, path: Path, sources: list[OfficialSource]) -> None:
        ensure_parent(path)
        columns = [
            "source_type",
            "source_name",
            "title",
            "url",
            "query",
            "description",
            "organization",
            "resource_formats",
            "resource_count",
            "score",
            "status",
            "notes",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for source in sources:
                row = source.model_dump()
                row["resource_formats"] = ",".join(source.resource_formats)
                writer.writerow({column: row.get(column, "") for column in columns})

