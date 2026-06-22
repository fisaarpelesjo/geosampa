import csv
from pathlib import Path

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.domain.risk import (
    DEFAULT_CATEGORY_WEIGHTS,
    RiskFinding,
    risk_level_from_score,
)
from geosampa_lote_analyzer.services.dossier_service import CATEGORY_RULES
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json
from geosampa_lote_analyzer.utils.text import keyword_in_text, normalize_text

RATIO_BONUS_THRESHOLD = 0.5


class RiskMatrixService:
    def generate(
        self,
        intersections_path: Path = PROCESSED_DIR / "intersections.csv",
        csv_path: Path = PROCESSED_DIR / "risk_matrix.csv",
        json_path: Path = PROCESSED_DIR / "risk_matrix.json",
        weights: dict[str, int] | None = None,
    ) -> tuple[list[RiskFinding], Path, Path]:
        category_weights = {**DEFAULT_CATEGORY_WEIGHTS, **(weights or {})}
        rows = self._read_csv(intersections_path)

        findings: list[RiskFinding] = []
        for row in rows:
            if self._int(row.get("intersects_count")) <= 0:
                continue
            category = self._category(row)
            weight = category_weights.get(category, 0)
            ratio = self._float(row.get("intersection_ratio"))
            score = weight + (1 if ratio >= RATIO_BONUS_THRESHOLD else 0)
            findings.append(
                RiskFinding(
                    category=category,
                    layer_type_name=row.get("layer_type_name", ""),
                    layer_title=row.get("layer_title"),
                    status=row.get("status", ""),
                    intersection_ratio=ratio,
                    weight=weight,
                    risk_score=score,
                    risk_level=risk_level_from_score(score),
                )
            )

        findings.sort(key=lambda finding: finding.risk_score, reverse=True)
        self._write_csv(csv_path, findings)
        write_json(json_path, [finding.model_dump() for finding in findings])
        return findings, csv_path, json_path

    def _category(self, row: dict[str, str]) -> str:
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
            if any(keyword_in_text(rule, text) for rule in rules):
                return category
        return "Outras interseções"

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

    def _write_csv(self, path: Path, findings: list[RiskFinding]) -> None:
        ensure_parent(path)
        columns = [
            "category",
            "layer_type_name",
            "layer_title",
            "status",
            "intersection_ratio",
            "weight",
            "risk_score",
            "risk_level",
            "note",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for finding in findings:
                writer.writerow(finding.model_dump())
