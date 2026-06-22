import csv
import re
from pathlib import Path

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR
from geosampa_lote_analyzer.domain.legislation import LEGISLATION_REFERENCE_TYPES, LegislationLookup
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json

SEARCH_BASE_URL = "https://legislacao.prefeitura.sp.gov.br/busca"


class LegislationLookupService:
    def generate(
        self,
        document_references_path: Path = PROCESSED_DIR / "document_references.csv",
        csv_path: Path = PROCESSED_DIR / "legislation_lookup.csv",
        json_path: Path = PROCESSED_DIR / "legislation_lookup.json",
    ) -> tuple[list[LegislationLookup], Path, Path]:
        rows = self._read_csv(document_references_path)
        lookups: list[LegislationLookup] = []
        seen: set[tuple[str, str | None, str | None]] = set()
        for row in rows:
            reference_type = row.get("reference_type", "")
            if reference_type not in LEGISLATION_REFERENCE_TYPES:
                continue
            value = row.get("value", "")
            number = self._number(value)
            year = row.get("year") or self._year(value)
            key = (reference_type, number, year)
            if key in seen:
                continue
            seen.add(key)
            lookups.append(
                LegislationLookup(
                    reference_type=reference_type,
                    value=value,
                    number=number,
                    year=year,
                    search_url=self._search_url(number, year),
                )
            )

        self._write_csv(csv_path, lookups)
        write_json(json_path, [lookup.model_dump() for lookup in lookups])
        return lookups, csv_path, json_path

    def _number(self, value: str) -> str | None:
        head = value.split("/")[0] if value else ""
        digits = re.sub(r"\D", "", head)
        return digits or None

    def _year(self, value: str) -> str | None:
        parts = value.split("/") if value else []
        if len(parts) < 2:
            return None
        digits = re.sub(r"\D", "", parts[1])
        return digits or None

    def _search_url(self, number: str | None, year: str | None) -> str:
        params = []
        if number:
            params.append(f"numero={number}")
        if year:
            params.append(f"ano={year}")
        query = "&".join(params)
        return f"{SEARCH_BASE_URL}?{query}" if query else SEARCH_BASE_URL

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _write_csv(self, path: Path, lookups: list[LegislationLookup]) -> None:
        ensure_parent(path)
        columns = ["reference_type", "value", "number", "year", "search_url", "note"]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for lookup in lookups:
                writer.writerow(lookup.model_dump())
