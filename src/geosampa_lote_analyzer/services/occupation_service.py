import csv
import json
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.domain.occupation import OCCUPATION_CATEGORY_KEYWORDS, OccupationFinding
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json
from geosampa_lote_analyzer.utils.text import normalize_text


class OccupationService:
    def generate(
        self,
        intersections_path: Path = PROCESSED_DIR / "intersections.csv",
        intersections_geojson_path: Path = PROCESSED_DIR / "intersections.geojson",
        csv_path: Path = PROCESSED_DIR / "occupation_indicators.csv",
        json_path: Path = PROCESSED_DIR / "occupation_indicators.json",
    ) -> tuple[list[OccupationFinding], Path, Path]:
        rows = self._read_csv(intersections_path)
        geometry_types_by_layer = self._geometry_types_by_layer(intersections_geojson_path)

        findings: list[OccupationFinding] = []
        for row in rows:
            if self._int(row.get("intersects_count")) <= 0:
                continue
            category = self._category(row)
            if category is None:
                continue
            layer_type_name = row.get("layer_type_name", "")
            findings.append(
                OccupationFinding(
                    layer_type_name=layer_type_name,
                    layer_title=row.get("layer_title"),
                    category=category,
                    geometry_types=sorted(geometry_types_by_layer.get(layer_type_name, set())),
                    intersects_count=self._int(row.get("intersects_count")),
                    intersection_ratio=self._float(row.get("intersection_ratio")),
                    status=row.get("status", ""),
                )
            )

        self._write_csv(csv_path, findings)
        write_json(json_path, [finding.model_dump() for finding in findings])
        return findings, csv_path, json_path

    def _category(self, row: dict[str, str]) -> str | None:
        text = normalize_text(
            " ".join(
                [
                    row.get("layer_type_name", ""),
                    row.get("layer_title", ""),
                    row.get("matched_keywords", ""),
                ]
            )
        )
        for category, keywords in OCCUPATION_CATEGORY_KEYWORDS.items():
            if any(normalize_text(keyword) in text for keyword in keywords):
                return category
        return None

    def _geometry_types_by_layer(self, path: Path) -> dict[str, set[str]]:
        geometry_types: dict[str, set[str]] = {}
        if not path.exists():
            return geometry_types
        data = json.loads(path.read_text(encoding="utf-8"))
        for feature in data.get("features", []):
            props = feature.get("properties") or {}
            layer_type_name = props.get("layer_type_name")
            geometry = feature.get("geometry") or {}
            geometry_type = geometry.get("type")
            if not layer_type_name or not geometry_type:
                continue
            geometry_types.setdefault(layer_type_name, set()).add(geometry_type)
        return geometry_types

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _int(self, value: str | None) -> int:
        try:
            return int(float(value or 0))
        except ValueError:
            return 0

    def _float(self, value: str | None) -> float:
        try:
            return float(value or 0)
        except ValueError:
            return 0.0

    def _write_csv(self, path: Path, findings: list[OccupationFinding]) -> None:
        ensure_parent(path)
        columns = [
            "layer_type_name",
            "layer_title",
            "category",
            "geometry_types",
            "intersects_count",
            "intersection_ratio",
            "status",
            "note",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for finding in findings:
                row: dict[str, Any] = finding.model_dump()
                row["geometry_types"] = ",".join(finding.geometry_types)
                writer.writerow({column: row.get(column, "") for column in columns})
