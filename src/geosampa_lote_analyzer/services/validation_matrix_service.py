import csv
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.services.dossier_service import CATEGORY_RULES
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json
from geosampa_lote_analyzer.utils.text import normalize_text

VALIDATION_CATEGORY_MAP = {
    "Cadastro municipal": ["AREA_PUBLICA", "DOCUMENTO_OFICIAL"],
    "Área pública": ["AREA_PUBLICA", "DOCUMENTO_OFICIAL"],
    "DUP/DIS e desapropriação": ["DESAPROPRIACAO", "DOCUMENTO_OFICIAL"],
    "Parque e áreas verdes": ["PARQUE", "MANANCIAL_APP", "DOCUMENTO_OFICIAL"],
    "Manancial, APP e represa": ["MANANCIAL_APP", "DOCUMENTO_OFICIAL"],
    "ZEIS e zoneamento": ["ZONEAMENTO", "DOCUMENTO_OFICIAL"],
    "Ocupação e infraestrutura": ["OCUPACAO_INFRAESTRUTURA", "HABITACAO"],
    "Outras interseções": ["DOCUMENTO_OFICIAL"],
}


NEXT_STEPS = {
    "Cadastro municipal": "Confirmar cadastro e natureza pública em fonte patrimonial oficial.",
    "Área pública": "Confirmar registro, matrícula, escritura, processo e status da área pública.",
    "DUP/DIS e desapropriação": "Validar dispositivo legal, planta e publicação oficial.",
    "Parque e áreas verdes": "Confirmar instrumento legal, situação do parque e órgão gestor.",
    "Manancial, APP e represa": "Confirmar classe ambiental, faixa de APP e legislação aplicável.",
    "ZEIS e zoneamento": "Confirmar perímetro, legislação de zoneamento e data de vigência.",
    "Ocupação e infraestrutura": (
        "Confirmar indícios de ocupação com camadas auxiliares e órgão competente."
    ),
    "Outras interseções": "Avaliar manualmente a pertinência da camada para o caso.",
}


class ValidationMatrixService:
    def generate(
        self,
        intersections_path: Path = PROCESSED_DIR / "intersections.csv",
        document_references_path: Path = PROCESSED_DIR / "document_references.csv",
        official_sources_path: Path = PROCESSED_DIR / "official_sources_inventory.csv",
        csv_path: Path = PROCESSED_DIR / "validation_matrix.csv",
        json_path: Path = PROCESSED_DIR / "validation_matrix.json",
    ) -> tuple[list[dict[str, Any]], Path, Path]:
        intersections = self._read_csv(intersections_path)
        references = self._read_csv(document_references_path)
        sources = self._read_csv(official_sources_path)
        rows = self._build_rows(intersections, references, sources)
        self._write_csv(csv_path, rows)
        write_json(json_path, rows)
        return rows, csv_path, json_path

    def _build_rows(
        self,
        intersections: list[dict[str, str]],
        references: list[dict[str, str]],
        sources: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for category in [*CATEGORY_RULES, "Outras interseções"]:
            category_intersections = [
                row for row in intersections if self._intersection_category(row) == category
            ]
            category_intersections = [
                row
                for row in category_intersections
                if self._int(row.get("intersects_count")) > 0
            ]
            if not category_intersections:
                continue
            source_categories = VALIDATION_CATEGORY_MAP.get(category, ["DOCUMENTO_OFICIAL"])
            matched_sources = self._sources_for_categories(sources, source_categories)
            matched_references = self._references_for_intersections(
                references,
                category_intersections,
            )
            rows.append(
                {
                    "finding_category": category,
                    "layers": "; ".join(
                        sorted({row.get("layer_type_name", "") for row in category_intersections})
                    ),
                    "intersection_count": len(category_intersections),
                    "document_reference_count": len(matched_references),
                    "validation_source_categories": ",".join(source_categories),
                    "recommended_sources": "; ".join(
                        source.get("title") or source.get("source_name", "")
                        for source in matched_sources[:5]
                    ),
                    "next_step": NEXT_STEPS.get(category, "Validar em fonte oficial."),
                    "status": "PENDENTE",
                }
            )
        return rows

    def _intersection_category(self, row: dict[str, str]) -> str:
        text = normalize_text(
            " ".join(
                [
                    row.get("layer_type_name", ""),
                    row.get("layer_title", ""),
                    row.get("matched_keywords", ""),
                ]
            )
        )
        for category, rules in CATEGORY_RULES.items():
            if any(normalize_text(rule) in text for rule in rules):
                return category
        return "Outras interseções"

    def _sources_for_categories(
        self,
        sources: list[dict[str, str]],
        categories: list[str],
    ) -> list[dict[str, str]]:
        matched = []
        for source in sources:
            source_categories = {
                category.strip()
                for category in (source.get("validation_categories") or "").split(",")
                if category.strip()
            }
            if source_categories.intersection(categories):
                matched.append(source)
        return sorted(
            matched,
            key=lambda source: self._int(source.get("relevance_score")),
            reverse=True,
        )

    def _references_for_intersections(
        self,
        references: list[dict[str, str]],
        intersections: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        layers = {row.get("layer_type_name") for row in intersections}
        return [reference for reference in references if reference.get("source_layer") in layers]

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _write_csv(self, path: Path, rows: list[dict[str, Any]]) -> None:
        ensure_parent(path)
        columns = [
            "finding_category",
            "layers",
            "intersection_count",
            "document_reference_count",
            "validation_source_categories",
            "recommended_sources",
            "next_step",
            "status",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})

    def _int(self, value: str | None) -> int:
        try:
            return int(float(value or 0))
        except ValueError:
            return 0
