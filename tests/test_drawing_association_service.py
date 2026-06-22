import csv

from geosampa_lote_analyzer.services.drawing_association_service import (
    DrawingAssociationService,
)


def test_finds_local_attachment_by_filename(tmp_path) -> None:
    references = tmp_path / "document_references.csv"
    _write_csv(
        references,
        [
            {
                "reference_type": "PLANTA",
                "value": "A-5.457",
                "source_layer": "geoportal:cadastro_area_publica",
                "source_field": "tx_planta",
                "source_title": "Cadastro de Área Pública",
            },
            {
                "reference_type": "PLANTA",
                "value": "102582",
                "source_layer": "geoportal:croqui_patrimonial",
                "source_field": "nr_croqui",
                "source_title": "Croqui Patrimonial",
            },
            {
                "reference_type": "DECRETO",
                "value": "49.659/08",
                "source_layer": "geoportal:cadparcs_parque",
                "source_field": "tx_instrumento_legal_criacao",
            },
        ],
    )
    attachments_dir = tmp_path / "anexos"
    attachments_dir.mkdir()
    (attachments_dir / "planta_A-5.457.pdf").write_text("conteudo", encoding="utf-8")

    requests, csv_path, json_path = DrawingAssociationService().generate(
        document_references_path=references,
        attachments_dir=attachments_dir,
        csv_path=tmp_path / "drawings.csv",
        json_path=tmp_path / "drawings.json",
    )

    assert len(requests) == 2
    by_value = {request.value: request for request in requests}
    assert by_value["A-5.457"].status == "ANEXO_LOCAL_ENCONTRADO"
    assert by_value["A-5.457"].local_path is not None
    assert by_value["102582"].status == "A_SOLICITAR"
    assert by_value["102582"].local_path is None
    assert csv_path.exists()
    assert json_path.exists()


def test_no_attachments_dir_means_all_pending(tmp_path) -> None:
    references = tmp_path / "document_references.csv"
    _write_csv(
        references,
        [
            {
                "reference_type": "PLANTA",
                "value": "30436",
                "source_layer": "geoportal:planta_dup_dis_pd",
                "source_field": "nm_planta_terreno",
            }
        ],
    )

    requests, _, _ = DrawingAssociationService().generate(
        document_references_path=references,
        attachments_dir=tmp_path / "anexos_inexistente",
        csv_path=tmp_path / "drawings.csv",
        json_path=tmp_path / "drawings.json",
    )

    assert requests[0].status == "A_SOLICITAR"


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
