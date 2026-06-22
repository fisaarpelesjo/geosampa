import csv
import json
from pathlib import Path

from geosampa_lote_analyzer.domain.cadastral_divergence import (
    CATEGORY_CADASTRAL_FIELDS,
    CadastralDivergence,
)
from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json


class CadastralDivergenceService:
    def generate(
        self,
        target_properties_path: Path = PROCESSED_DIR / "target_lote_properties.json",
        occupation_indicators_path: Path = PROCESSED_DIR / "occupation_indicators.csv",
        csv_path: Path = PROCESSED_DIR / "cadastral_divergence.csv",
        json_path: Path = PROCESSED_DIR / "cadastral_divergence.json",
    ) -> tuple[list[CadastralDivergence], Path, Path]:
        cadastro = self._read_json(target_properties_path)
        occupation_rows = self._read_csv(occupation_indicators_path)

        divergences: list[CadastralDivergence] = []
        for row in occupation_rows:
            category = row.get("category", "")
            cadastral_field = CATEGORY_CADASTRAL_FIELDS.get(category)
            if not cadastral_field:
                continue
            cadastral_value = cadastro.get(cadastral_field)
            intersects_count = self._int(row.get("intersects_count"))
            divergencia = bool(intersects_count > 0 and not cadastral_value)
            divergences.append(
                CadastralDivergence(
                    category=category,
                    layer_type_name=row.get("layer_type_name", ""),
                    cadastral_field=cadastral_field,
                    cadastral_value=self._as_text(cadastral_value),
                    intersects_count=intersects_count,
                    divergencia=divergencia,
                )
            )

        self._write_csv(csv_path, divergences)
        write_json(json_path, [divergence.model_dump() for divergence in divergences])
        return divergences, csv_path, json_path

    def _as_text(self, value: object) -> str | None:
        if value in (None, ""):
            return None
        return str(value)

    def _read_json(self, path: Path) -> dict[str, object]:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

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

    def _write_csv(self, path: Path, divergences: list[CadastralDivergence]) -> None:
        ensure_parent(path)
        columns = [
            "category",
            "layer_type_name",
            "cadastral_field",
            "cadastral_value",
            "intersects_count",
            "divergencia",
            "note",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for divergence in divergences:
                writer.writerow(divergence.model_dump())
