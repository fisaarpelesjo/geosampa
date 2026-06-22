import csv
from pathlib import Path

from geosampa_lote_analyzer.domain.constants import ATTACHMENTS_DIR, PROCESSED_DIR
from geosampa_lote_analyzer.domain.drawings import NOTE_LOCAL, NOTE_PENDING, DrawingRequest
from geosampa_lote_analyzer.utils.files import ensure_parent, safe_filename, write_json


class DrawingAssociationService:
    def generate(
        self,
        document_references_path: Path = PROCESSED_DIR / "document_references.csv",
        attachments_dir: Path = ATTACHMENTS_DIR,
        csv_path: Path = PROCESSED_DIR / "drawing_requests.csv",
        json_path: Path = PROCESSED_DIR / "drawing_requests.json",
    ) -> tuple[list[DrawingRequest], Path, Path]:
        rows = self._read_csv(document_references_path)
        local_files = self._list_attachments(attachments_dir)

        requests: list[DrawingRequest] = []
        seen: set[tuple[str, str | None, str]] = set()
        for row in rows:
            if row.get("reference_type") != "PLANTA":
                continue
            value = row.get("value", "")
            source_layer = row.get("source_layer") or None
            source_field = row.get("source_field", "")
            key = (value, source_layer, source_field)
            if key in seen:
                continue
            seen.add(key)
            local_path = self._find_attachment(value, local_files)
            requests.append(
                DrawingRequest(
                    value=value,
                    source_layer=source_layer,
                    source_field=source_field,
                    source_title=row.get("source_title") or None,
                    status="ANEXO_LOCAL_ENCONTRADO" if local_path else "A_SOLICITAR",
                    local_path=str(local_path) if local_path else None,
                    note=NOTE_LOCAL if local_path else NOTE_PENDING,
                )
            )

        self._write_csv(csv_path, requests)
        write_json(json_path, [request.model_dump() for request in requests])
        return requests, csv_path, json_path

    def _list_attachments(self, attachments_dir: Path) -> list[Path]:
        if not attachments_dir.exists():
            return []
        return [path for path in attachments_dir.iterdir() if path.is_file()]

    def _find_attachment(self, value: str, local_files: list[Path]) -> Path | None:
        if not value:
            return None
        needle = safe_filename(value).lower()
        for path in local_files:
            if needle in safe_filename(path.stem).lower():
                return path
        return None

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _write_csv(self, path: Path, requests: list[DrawingRequest]) -> None:
        ensure_parent(path)
        columns = [
            "value",
            "source_layer",
            "source_field",
            "source_title",
            "status",
            "local_path",
            "note",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for request in requests:
                writer.writerow(request.model_dump())
