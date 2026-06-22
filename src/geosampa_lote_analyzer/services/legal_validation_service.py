import csv
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json

LEGAL_REFERENCE_TYPES = {
    "DECRETO",
    "LEI",
    "LEGISLACAO",
    "DISPOSITIVO_LEGAL",
    "INSTRUMENTO_LEGAL",
}


class LegalValidationService:
    def generate(
        self,
        document_references_path: Path = PROCESSED_DIR / "document_references.csv",
        csv_path: Path = PROCESSED_DIR / "legal_validation_tasks.csv",
        json_path: Path = PROCESSED_DIR / "legal_validation_tasks.json",
    ) -> tuple[list[dict[str, Any]], Path, Path]:
        references = self._read_csv(document_references_path)
        rows = [self._task_from_reference(reference) for reference in references]
        rows = [row for row in rows if row]
        self._write_csv(csv_path, rows)
        write_json(json_path, rows)
        return rows, csv_path, json_path

    def _task_from_reference(self, reference: dict[str, str]) -> dict[str, Any] | None:
        reference_type = reference.get("reference_type", "")
        value = reference.get("value", "")
        if not value:
            return None
        if reference_type == "PROCESSO":
            return self._process_task(reference)
        if reference_type in LEGAL_REFERENCE_TYPES:
            return self._legal_task(reference)
        return None

    def _legal_task(self, reference: dict[str, str]) -> dict[str, Any]:
        value = reference.get("value", "")
        search_query = self._legal_search_query(reference)
        return {
            "reference_type": reference.get("reference_type", ""),
            "value": value,
            "year": reference.get("year", ""),
            "source_layer": reference.get("source_layer", ""),
            "source_field": reference.get("source_field", ""),
            "validation_status": "PENDENTE",
            "validation_channel": "LEGISLACAO_DIARIO_OFICIAL",
            "primary_url": "https://legislacao.prefeitura.sp.gov.br/",
            "secondary_url": "https://diariooficial.prefeitura.sp.gov.br/",
            "search_query": search_query,
            "next_step": "Pesquisar número/ano no Catálogo de Legislação e no Diário Oficial.",
        }

    def _process_task(self, reference: dict[str, str]) -> dict[str, Any]:
        value = reference.get("value", "")
        return {
            "reference_type": "PROCESSO",
            "value": value,
            "year": reference.get("year", ""),
            "source_layer": reference.get("source_layer", ""),
            "source_field": reference.get("source_field", ""),
            "validation_status": "PENDENTE",
            "validation_channel": "PROCESSOS_ADMINISTRATIVOS",
            "primary_url": "https://processos.prefeitura.sp.gov.br/",
            "secondary_url": "",
            "search_query": value,
            "next_step": "Consultar o número no Portal de Processos Administrativos.",
        }

    def _legal_search_query(self, reference: dict[str, str]) -> str:
        value = reference.get("value", "")
        year = reference.get("year", "")
        reference_type = reference.get("reference_type", "").lower().replace("_", " ")
        query = " ".join(part for part in [reference_type, value, year] if part)
        return quote_plus(query)

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _write_csv(self, path: Path, rows: list[dict[str, Any]]) -> None:
        ensure_parent(path)
        columns = [
            "reference_type",
            "value",
            "year",
            "source_layer",
            "source_field",
            "validation_status",
            "validation_channel",
            "primary_url",
            "secondary_url",
            "search_query",
            "next_step",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})

