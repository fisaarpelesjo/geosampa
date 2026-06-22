import csv
import logging
import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from geosampa_lote_analyzer.domain.constants import ATTACHMENTS_DIR, PROCESSED_DIR
from geosampa_lote_analyzer.domain.pdf_documents import ORGAO_KEYWORDS, PdfReferenceFinding
from geosampa_lote_analyzer.services.document_reference_service import TEXT_PATTERNS
from geosampa_lote_analyzer.utils.files import ensure_parent, write_json
from geosampa_lote_analyzer.utils.text import keyword_in_text, normalize_text

logger = logging.getLogger(__name__)

DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}\s+de\s+[a-zà-ú]+\s+de\s+\d{4}\b", re.I),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
]

SNIPPET_RADIUS = 60


class PdfDocumentService:
    def generate(
        self,
        pdf_dir: Path = ATTACHMENTS_DIR,
        csv_path: Path = PROCESSED_DIR / "pdf_documents_index.csv",
        json_path: Path = PROCESSED_DIR / "pdf_documents_index.json",
    ) -> tuple[list[PdfReferenceFinding], Path, Path]:
        findings: list[PdfReferenceFinding] = []
        if pdf_dir.exists():
            for pdf_path in sorted(pdf_dir.glob("*.pdf")):
                findings.extend(self._read_pdf(pdf_path))

        findings = self._deduplicate(findings)
        self._write_csv(csv_path, findings)
        write_json(json_path, [finding.model_dump() for finding in findings])
        return findings, csv_path, json_path

    def _read_pdf(self, pdf_path: Path) -> list[PdfReferenceFinding]:
        try:
            reader = PdfReader(str(pdf_path))
        except (PdfReadError, OSError) as exc:
            logger.warning("Falha ao abrir PDF %s: %s", pdf_path.name, exc)
            return [
                PdfReferenceFinding(
                    file_name=pdf_path.name,
                    page=0,
                    reference_type="ERRO_LEITURA",
                    value=str(exc),
                    orgao=None,
                    data_publicacao=None,
                    citation=pdf_path.name,
                    raw_context="",
                )
            ]

        findings: list[PdfReferenceFinding] = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # extração pode falhar por PDF malformado
                logger.warning(
                    "Falha ao extrair texto de %s p.%s: %s", pdf_path.name, page_number, exc
                )
                continue
            if not text.strip():
                continue
            orgao = self._orgao(text)
            data_publicacao = self._date(text)
            for reference_type, pattern in TEXT_PATTERNS:
                for match in pattern.finditer(text):
                    findings.append(
                        PdfReferenceFinding(
                            file_name=pdf_path.name,
                            page=page_number,
                            reference_type=reference_type,
                            value=self._value(reference_type, match),
                            orgao=orgao,
                            data_publicacao=data_publicacao,
                            citation=f"{pdf_path.name}, p. {page_number}",
                            raw_context=self._snippet(text, match),
                        )
                    )
        return findings

    def _value(self, reference_type: str, match: re.Match) -> str:
        if reference_type in {"DECRETO", "LEI"}:
            return f"{match.group(1)}/{match.group(2)}"
        if reference_type in {"MATRICULA", "PLANTA"} and match.groups():
            return match.group(1)
        return match.group(0)

    def _orgao(self, text: str) -> str | None:
        normalized = normalize_text(text)
        for keyword in ORGAO_KEYWORDS:
            if keyword_in_text(keyword, normalized):
                return keyword.upper()
        return None

    def _date(self, text: str) -> str | None:
        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    def _snippet(self, text: str, match: re.Match) -> str:
        start = max(0, match.start() - SNIPPET_RADIUS)
        end = min(len(text), match.end() + SNIPPET_RADIUS)
        return " ".join(text[start:end].split())

    def _deduplicate(self, findings: list[PdfReferenceFinding]) -> list[PdfReferenceFinding]:
        deduplicated: list[PdfReferenceFinding] = []
        seen: set[tuple[str, int, str, str]] = set()
        for finding in findings:
            key = (finding.file_name, finding.page, finding.reference_type, finding.value)
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(finding)
        return deduplicated

    def _write_csv(self, path: Path, findings: list[PdfReferenceFinding]) -> None:
        ensure_parent(path)
        columns = [
            "file_name",
            "page",
            "reference_type",
            "value",
            "orgao",
            "data_publicacao",
            "citation",
            "raw_context",
            "note",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for finding in findings:
                writer.writerow(finding.model_dump())
