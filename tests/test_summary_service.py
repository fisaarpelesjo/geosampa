import csv
import json

from geosampa_lote_analyzer.services.summary_service import SummaryService


def test_summary_consolidates_all_artifacts(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text(json.dumps({"sql_base": "174.001.0038"}), encoding="utf-8")

    risk = tmp_path / "risk.csv"
    _write_csv(
        risk,
        [
            {
                "category": "Manancial, APP e represa",
                "layer_type_name": "geoportal:manancial_billings",
                "intersection_ratio": "0.375",
                "risk_score": "3",
                "risk_level": "ALTO",
            },
            {
                "category": "Cadastro municipal",
                "layer_type_name": "geoportal:lote_cidadao",
                "intersection_ratio": "1.0",
                "risk_score": "1",
                "risk_level": "BAIXO",
            },
        ],
    )
    divergence = tmp_path / "div.csv"
    _write_csv(
        divergence,
        [
            {
                "category": "EDIFICACAO",
                "layer_type_name": "geoportal:edificacao",
                "cadastral_field": "area_construida_m2",
                "divergencia": "True",
            }
        ],
    )
    drawings = tmp_path / "drawings.csv"
    _write_csv(
        drawings,
        [
            {
                "value": "A-5.457",
                "source_layer": "geoportal:cadastro_area_publica",
                "status": "A_SOLICITAR",
            }
        ],
    )
    legislation = tmp_path / "legislation.csv"
    _write_csv(
        legislation,
        [
            {
                "reference_type": "DECRETO",
                "value": "49.659/08",
                "search_url": "https://legislacao.prefeitura.sp.gov.br/busca?numero=49659",
            }
        ],
    )
    pdfs = tmp_path / "pdfs.csv"
    _write_csv(pdfs, [])

    output_path = SummaryService().generate(
        target_properties_path=target,
        risk_matrix_path=risk,
        cadastral_divergence_path=divergence,
        drawing_requests_path=drawings,
        legislation_lookup_path=legislation,
        pdf_documents_path=pdfs,
        output_path=tmp_path / "resumo.md",
    )

    markdown = output_path.read_text(encoding="utf-8")
    assert "Lote 174.001.0038" in markdown
    assert "geoportal:manancial_billings" in markdown
    assert "1 de 1 sinais com divergência" in markdown
    assert "A-5.457" in markdown
    assert "49.659/08" in markdown
    assert "Nenhum PDF local indexado" in markdown


def test_summary_handles_missing_artifacts(tmp_path) -> None:
    output_path = SummaryService().generate(
        target_properties_path=tmp_path / "nao_existe.json",
        risk_matrix_path=tmp_path / "nao_existe.csv",
        cadastral_divergence_path=tmp_path / "nao_existe.csv",
        drawing_requests_path=tmp_path / "nao_existe.csv",
        legislation_lookup_path=tmp_path / "nao_existe.csv",
        pdf_documents_path=tmp_path / "nao_existe.csv",
        output_path=tmp_path / "resumo.md",
    )

    markdown = output_path.read_text(encoding="utf-8")
    assert "não informado" in markdown
    assert "Matriz de risco não disponível." in markdown


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row}) or ["value"]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
