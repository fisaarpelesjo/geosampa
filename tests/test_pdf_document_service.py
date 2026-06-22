from geosampa_lote_analyzer.services.pdf_document_service import PdfDocumentService


def test_extracts_references_orgao_and_date_with_citation(tmp_path) -> None:
    pdf_dir = tmp_path / "anexos"
    pdf_dir.mkdir()
    _write_minimal_pdf(
        pdf_dir / "decreto.pdf",
        "SECRETARIA MUNICIPAL DO VERDE E DO MEIO AMBIENTE - SVMA. "
        "DECRETO 49.659/08 de 10 de janeiro de 2008. Cria unidade de conservacao.",
    )

    findings, csv_path, json_path = PdfDocumentService().generate(
        pdf_dir=pdf_dir,
        csv_path=tmp_path / "index.csv",
        json_path=tmp_path / "index.json",
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding.file_name == "decreto.pdf"
    assert finding.page == 1
    assert finding.reference_type == "DECRETO"
    assert finding.value == "49.659/08"
    assert finding.orgao == "SVMA"
    assert finding.data_publicacao == "10 de janeiro de 2008"
    assert finding.citation == "decreto.pdf, p. 1"
    assert csv_path.exists()
    assert json_path.exists()


def test_missing_pdf_dir_returns_empty(tmp_path) -> None:
    findings, csv_path, json_path = PdfDocumentService().generate(
        pdf_dir=tmp_path / "nao_existe",
        csv_path=tmp_path / "index.csv",
        json_path=tmp_path / "index.json",
    )

    assert findings == []
    assert csv_path.exists()
    assert json_path.exists()


def test_corrupted_pdf_marks_erro_leitura_without_raising(tmp_path) -> None:
    pdf_dir = tmp_path / "anexos"
    pdf_dir.mkdir()
    (pdf_dir / "corrompido.pdf").write_bytes(b"isto nao e um pdf valido")

    findings, _, _ = PdfDocumentService().generate(
        pdf_dir=pdf_dir,
        csv_path=tmp_path / "index.csv",
        json_path=tmp_path / "index.json",
    )

    assert len(findings) == 1
    assert findings[0].reference_type == "ERRO_LEITURA"
    assert findings[0].file_name == "corrompido.pdf"


def _write_minimal_pdf(path, text: str) -> None:
    content = f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET".encode("latin-1")

    header = b"%PDF-1.4\n"
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> "
        b"/MediaBox [0 0 612 792] /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(content)).encode() + b" >> stream\n"
        + content
        + b"\nendstream endobj\n",
    ]

    body = b""
    offsets = []
    position = len(header)
    for obj in objects:
        offsets.append(position)
        body += obj
        position += len(obj)

    xref_offset = len(header) + len(body)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets:
        xref += f"{offset:010d} 00000 n \n".encode()
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode()
        + b"\n%%EOF"
    )

    path.write_bytes(header + body + xref + trailer)
