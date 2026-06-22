import csv
import json
import re
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.domain.document_references import DocumentReference
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json
from geosampa_lote_analyzer.utils.text import normalize_text

FIELD_TYPE_HINTS = {
    "decreto": "DECRETO",
    "dispositivo_legal": "DISPOSITIVO_LEGAL",
    "legislacao": "LEGISLACAO",
    "lei": "LEGISLACAO",
    "processo": "PROCESSO",
    "planta": "PLANTA",
    "croqui": "PLANTA",
    "matricula": "MATRICULA",
    "matrícula": "MATRICULA",
    "escritura": "ESCRITURA",
    "instrumento_legal": "INSTRUMENTO_LEGAL",
    "registro": "REGISTRO_IMOVEL",
}

TEXT_PATTERNS = [
    (
        "DECRETO",
        re.compile(r"\b(?:dec\.?|decreto)\s*(?:n[º°o.]*)?\s*([\d.]+)\s*/\s*(\d{2,4})", re.I),
    ),
    ("LEI", re.compile(r"\b(?:lei)\s*(?:n[º°o.]*)?\s*([\d.]+)\s*/\s*(\d{2,4})", re.I)),
    ("PROCESSO", re.compile(r"\b\d{2}\.\d{3}\.\d{3}\.\d{2}\*?\d{2}\b")),
    ("MATRICULA", re.compile(r"\bmatr[íi]cula\s*(?:n[º°o.]*)?\s*([\d.]+)", re.I)),
    ("PLANTA", re.compile(r"\b(?:planta)\s*([A-Z]?-?\d[\w.\-]*)", re.I)),
]


class DocumentReferenceService:
    def generate(
        self,
        intersections_path: Path = PROCESSED_DIR / "intersections.geojson",
        target_properties_path: Path | None = None,
        csv_path: Path = PROCESSED_DIR / "document_references.csv",
        json_path: Path = PROCESSED_DIR / "document_references.json",
    ) -> tuple[list[DocumentReference], Path, Path]:
        references: list[DocumentReference] = []
        if target_properties_path and target_properties_path.exists():
            properties = json.loads(target_properties_path.read_text(encoding="utf-8"))
            references.extend(
                self._extract_from_properties(
                    properties.get("raw_properties", properties),
                    source_layer="lote_cidadao",
                    source_title="Cadastro do lote",
                )
            )

        if intersections_path.exists():
            data = json.loads(intersections_path.read_text(encoding="utf-8"))
            for feature in data.get("features", []):
                props = feature.get("properties") or {}
                source_layer = props.get("layer_type_name")
                references.extend(
                    self._extract_from_properties(
                        props,
                        source_layer=source_layer,
                        source_title=source_layer,
                    )
                )

        references = self._deduplicate(references)
        self._write_csv(csv_path, references)
        write_json(json_path, [reference.model_dump() for reference in references])
        return references, csv_path, json_path

    def _extract_from_properties(
        self,
        properties: dict[str, Any],
        source_layer: str | None,
        source_title: str | None,
    ) -> list[DocumentReference]:
        references: list[DocumentReference] = []
        for field, value in properties.items():
            if value in (None, ""):
                continue
            text = str(value).strip()
            normalized_field = normalize_text(str(field))
            hinted_type = self._reference_type_from_field(normalized_field)
            if hinted_type:
                references.append(
                    self._build_reference(
                        hinted_type,
                        text,
                        source_layer,
                        str(field),
                        source_title,
                        raw_context=text,
                    )
                )
            references.extend(
                self._extract_from_text(
                    text,
                    source_layer=source_layer,
                    source_field=str(field),
                    source_title=source_title,
                )
            )
        return references

    def _reference_type_from_field(self, normalized_field: str) -> str | None:
        for field_hint, reference_type in FIELD_TYPE_HINTS.items():
            if normalize_text(field_hint) in normalized_field:
                return reference_type
        return None

    def _extract_from_text(
        self,
        text: str,
        source_layer: str | None,
        source_field: str,
        source_title: str | None,
    ) -> list[DocumentReference]:
        references: list[DocumentReference] = []
        for reference_type, pattern in TEXT_PATTERNS:
            for match in pattern.finditer(text):
                if reference_type in {"DECRETO", "LEI"}:
                    value = f"{match.group(1)}/{match.group(2)}"
                    year = self._normalize_year(match.group(2))
                elif reference_type in {"MATRICULA", "PLANTA"} and match.groups():
                    value = match.group(1)
                    year = None
                else:
                    value = match.group(0)
                    year = None
                references.append(
                    self._build_reference(
                        reference_type,
                        value,
                        source_layer,
                        source_field,
                        source_title,
                        year=year,
                        raw_context=text,
                    )
                )
        return references

    def _build_reference(
        self,
        reference_type: str,
        value: str,
        source_layer: str | None,
        source_field: str,
        source_title: str | None,
        year: str | None = None,
        raw_context: str | None = None,
    ) -> DocumentReference:
        return DocumentReference(
            reference_type=reference_type,
            value=value.strip(),
            source_layer=source_layer,
            source_field=source_field,
            source_title=source_title,
            year=year or self._year_from_value(value),
            validation_hint=self._validation_hint(reference_type, value),
            raw_context=raw_context,
        )

    def _validation_hint(self, reference_type: str, value: str) -> str:
        if reference_type in {"DECRETO", "LEI", "LEGISLACAO", "DISPOSITIVO_LEGAL"}:
            return "Validar no Catálogo de Legislação Municipal e no Diário Oficial."
        if reference_type == "PROCESSO":
            return "Validar no Portal de Processos Administrativos."
        if reference_type in {"PLANTA", "ESCRITURA", "MATRICULA", "REGISTRO_IMOVEL"}:
            return "Validar com órgão responsável, planta oficial ou cartório competente."
        if reference_type == "INSTRUMENTO_LEGAL":
            return "Validar no texto do instrumento legal citado."
        return "Validar em fonte oficial."

    def _deduplicate(self, references: list[DocumentReference]) -> list[DocumentReference]:
        deduplicated: list[DocumentReference] = []
        seen: set[tuple[str, str, str | None, str]] = set()
        for reference in references:
            key = (
                reference.reference_type,
                normalize_text(reference.value),
                reference.source_layer,
                reference.source_field,
            )
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(reference)
        return deduplicated

    def _write_csv(self, path: Path, references: list[DocumentReference]) -> None:
        ensure_parent(path)
        columns = [
            "reference_type",
            "value",
            "source_layer",
            "source_field",
            "source_title",
            "year",
            "validation_status",
            "validation_hint",
            "raw_context",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for reference in references:
                writer.writerow(reference.model_dump())

    def _year_from_value(self, value: str) -> str | None:
        match = re.search(r"\b(19|20)\d{2}\b", value)
        return match.group(0) if match else None

    def _normalize_year(self, value: str) -> str | None:
        if len(value) == 2:
            return f"20{value}" if int(value) < 50 else f"19{value}"
        return value
