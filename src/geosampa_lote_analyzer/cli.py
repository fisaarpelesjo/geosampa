import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from geosampa_lote_analyzer.domain.constants import ATTACHMENTS_DIR, PROCESSED_DIR, REPORTS_DIR
from geosampa_lote_analyzer.domain.keywords import DEFAULT_LAYER_KEYWORDS
from geosampa_lote_analyzer.logging_config import configure_logging
from geosampa_lote_analyzer.services.cadastral_divergence_service import (
    CadastralDivergenceService,
)
from geosampa_lote_analyzer.services.document_reference_service import DocumentReferenceService
from geosampa_lote_analyzer.services.dossier_service import DossierService
from geosampa_lote_analyzer.services.drawing_association_service import (
    DrawingAssociationService,
)
from geosampa_lote_analyzer.services.intersection_service import IntersectionService
from geosampa_lote_analyzer.services.layer_discovery_service import LayerDiscoveryService
from geosampa_lote_analyzer.services.legal_validation_service import LegalValidationService
from geosampa_lote_analyzer.services.legislation_lookup_service import LegislationLookupService
from geosampa_lote_analyzer.services.lote_service import LoteService
from geosampa_lote_analyzer.services.map_service import MapService
from geosampa_lote_analyzer.services.occupation_service import OccupationService
from geosampa_lote_analyzer.services.pdf_document_service import PdfDocumentService
from geosampa_lote_analyzer.services.report_service import ReportService
from geosampa_lote_analyzer.services.risk_matrix_service import RiskMatrixService
from geosampa_lote_analyzer.services.source_discovery_service import SourceDiscoveryService
from geosampa_lote_analyzer.services.summary_service import SummaryService
from geosampa_lote_analyzer.services.validation_matrix_service import ValidationMatrixService

app = typer.Typer(help="Analisa lotes do GeoSampa via WFS.")
console = Console()
TARGET_PATH = PROCESSED_DIR / "target_lote.geojson"
LAYERS_PATH = PROCESSED_DIR / "candidate_layers_inventory.csv"
TARGET_PROPERTIES_PATH = PROCESSED_DIR / "target_lote_properties.json"
INTERSECTIONS_CSV_PATH = PROCESSED_DIR / "intersections.csv"
INTERSECTIONS_GEOJSON_PATH = PROCESSED_DIR / "intersections.geojson"


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    configure_logging(verbose)


@app.command("fetch-lote")
def fetch_lote(
    setor: str = typer.Option(...),
    quadra: str = typer.Option(...),
    lote: str = typer.Option(...),
) -> None:
    info, raw_path, processed_path = LoteService().fetch_lote(setor, quadra, lote)
    console.print("Feature encontrada: 1")
    console.print(f"SQL base: {info.sql_base or ''}")
    console.print(f"Dígito SQL: {info.digito_sql or ''}")
    console.print(f"Tipo quadra: {info.tipo_quadra or ''}")
    console.print(f"Tipo lote: {info.tipo_lote or ''}")
    console.print(f"Arquivo bruto: {raw_path}")
    console.print(f"Arquivo processado: {processed_path}")


@app.command("discover-layers")
def discover_layers(
    keywords: str = typer.Option(",".join(DEFAULT_LAYER_KEYWORDS)),
) -> None:
    parsed_keywords = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]
    layers, path = LayerDiscoveryService().discover(parsed_keywords)
    console.print(f"Total de camadas no WFS: {len(layers)}")
    console.print(f"Camadas candidatas: {sum(layer.is_candidate for layer in layers)}")
    console.print(f"Inventário salvo em: {path}")


@app.command("discover-sources")
def discover_sources(
    keywords: str = typer.Option(
        "",
        help="Lista de termos separados por vírgula. Se vazio, usa termos padrão.",
    ),
    rows_per_keyword: int = typer.Option(5, min=1, max=50),
) -> None:
    parsed_keywords = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]
    sources, csv_path, json_path = SourceDiscoveryService().discover(
        parsed_keywords or None,
        rows_per_keyword=rows_per_keyword,
    )
    console.print(f"Fontes inventariadas: {len(sources)}")
    console.print(f"Inventário CSV: {csv_path}")
    console.print(f"Inventário JSON: {json_path}")


@app.command("document-references")
def document_references(
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_GEOJSON_PATH,
    target_properties: Annotated[Path | None, typer.Option()] = None,
) -> None:
    references, csv_path, json_path = DocumentReferenceService().generate(
        intersections_path=intersections,
        target_properties_path=target_properties,
    )
    console.print(f"Referências documentais: {len(references)}")
    console.print(f"Inventário CSV: {csv_path}")
    console.print(f"Inventário JSON: {json_path}")


@app.command("dossie")
def dossier(
    target_properties: Annotated[Path, typer.Option()] = TARGET_PROPERTIES_PATH,
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_CSV_PATH,
    document_references_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "document_references.csv",
    official_sources_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "official_sources_inventory.csv",
) -> None:
    markdown_path, json_path = DossierService().generate(
        target_properties_path=target_properties,
        intersections_path=intersections,
        document_references_path=document_references_path,
        official_sources_path=official_sources_path,
    )
    console.print(f"Dossiê Markdown: {markdown_path}")
    console.print(f"Dossiê JSON: {json_path}")


@app.command("validation-matrix")
def validation_matrix(
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_CSV_PATH,
    document_references_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "document_references.csv",
    official_sources_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "official_sources_inventory.csv",
) -> None:
    rows, csv_path, json_path = ValidationMatrixService().generate(
        intersections_path=intersections,
        document_references_path=document_references_path,
        official_sources_path=official_sources_path,
    )
    console.print(f"Itens de validação: {len(rows)}")
    console.print(f"Matriz CSV: {csv_path}")
    console.print(f"Matriz JSON: {json_path}")


@app.command("legal-validation")
def legal_validation(
    document_references_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "document_references.csv",
) -> None:
    rows, csv_path, json_path = LegalValidationService().generate(
        document_references_path=document_references_path,
    )
    console.print(f"Tarefas de validação legal: {len(rows)}")
    console.print(f"Tarefas CSV: {csv_path}")
    console.print(f"Tarefas JSON: {json_path}")


@app.command("pdf-documents")
def pdf_documents(
    pdf_dir: Annotated[Path, typer.Option()] = ATTACHMENTS_DIR,
) -> None:
    findings, csv_path, json_path = PdfDocumentService().generate(pdf_dir=pdf_dir)
    console.print(f"Referências extraídas de PDFs: {len(findings)}")
    console.print(f"Índice CSV: {csv_path}")
    console.print(f"Índice JSON: {json_path}")


@app.command("plantas-croquis")
def plantas_croquis(
    document_references_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "document_references.csv",
    attachments_dir: Annotated[Path, typer.Option()] = ATTACHMENTS_DIR,
) -> None:
    requests, csv_path, json_path = DrawingAssociationService().generate(
        document_references_path=document_references_path,
        attachments_dir=attachments_dir,
    )
    found = sum(request.status == "ANEXO_LOCAL_ENCONTRADO" for request in requests)
    console.print(f"Plantas/croquis referenciados: {len(requests)}")
    console.print(f"Anexos locais encontrados: {found}")
    console.print(f"A solicitar: {len(requests) - found}")
    console.print(f"Lista CSV: {csv_path}")
    console.print(f"Lista JSON: {json_path}")


@app.command("summary")
def summary(
    target_properties: Annotated[Path, typer.Option()] = TARGET_PROPERTIES_PATH,
) -> None:
    output_path = SummaryService().generate(target_properties_path=target_properties)
    console.print(f"Resumo investigativo: {output_path}")


@app.command("risk-matrix")
def risk_matrix(
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_CSV_PATH,
    weights_json: Annotated[
        Path | None,
        typer.Option(help="JSON com pesos por categoria para sobrescrever os padrões."),
    ] = None,
) -> None:
    weights = json.loads(weights_json.read_text(encoding="utf-8")) if weights_json else None
    findings, csv_path, json_path = RiskMatrixService().generate(
        intersections_path=intersections,
        weights=weights,
    )
    by_level = {level: 0 for level in ("CRITICO", "ALTO", "MEDIO", "BAIXO")}
    for finding in findings:
        by_level[finding.risk_level] += 1
    console.print(f"Achados na matriz de risco: {len(findings)}")
    for level, count in by_level.items():
        console.print(f"{level}: {count}")
    console.print(f"Matriz CSV: {csv_path}")
    console.print(f"Matriz JSON: {json_path}")


@app.command("cadastral-divergence")
def cadastral_divergence(
    target_properties: Annotated[Path, typer.Option()] = TARGET_PROPERTIES_PATH,
    occupation_indicators_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "occupation_indicators.csv",
) -> None:
    divergences, csv_path, json_path = CadastralDivergenceService().generate(
        target_properties_path=target_properties,
        occupation_indicators_path=occupation_indicators_path,
    )
    flagged = sum(divergence.divergencia for divergence in divergences)
    console.print(f"Comparações cadastro x ocupação: {len(divergences)}")
    console.print(f"Divergências sinalizadas: {flagged}")
    console.print(f"Divergências CSV: {csv_path}")
    console.print(f"Divergências JSON: {json_path}")


@app.command("legislation-lookup")
def legislation_lookup(
    document_references_path: Annotated[
        Path, typer.Option()
    ] = PROCESSED_DIR / "document_references.csv",
) -> None:
    lookups, csv_path, json_path = LegislationLookupService().generate(
        document_references_path=document_references_path,
    )
    console.print(f"Referências legislativas para confirmar: {len(lookups)}")
    console.print(f"Links CSV: {csv_path}")
    console.print(f"Links JSON: {json_path}")


@app.command("occupation")
def occupation(
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_CSV_PATH,
    intersections_geojson: Annotated[Path, typer.Option()] = INTERSECTIONS_GEOJSON_PATH,
) -> None:
    findings, csv_path, json_path = OccupationService().generate(
        intersections_path=intersections,
        intersections_geojson_path=intersections_geojson,
    )
    console.print(f"Indícios de ocupação/infraestrutura: {len(findings)}")
    console.print(f"Indicadores CSV: {csv_path}")
    console.print(f"Indicadores JSON: {json_path}")


@app.command("intersect")
def intersect(
    target: Annotated[Path, typer.Option()] = TARGET_PATH,
    layers: Annotated[Path, typer.Option()] = LAYERS_PATH,
) -> None:
    csv_path, geojson_path = IntersectionService().intersect(target, layers)
    console.print(f"Relatório de interseções: {csv_path}")
    console.print(f"GeoJSON de interseções: {geojson_path}")


@app.command("report")
def report(
    target_properties: Annotated[Path, typer.Option()] = TARGET_PROPERTIES_PATH,
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_CSV_PATH,
) -> None:
    markdown_path, json_path = ReportService().generate(target_properties, intersections)
    console.print(f"Relatório Markdown: {markdown_path}")
    console.print(f"Relatório JSON: {json_path}")


@app.command("map")
def map_command(
    target: Annotated[Path, typer.Option()] = TARGET_PATH,
    intersections: Annotated[Path, typer.Option()] = INTERSECTIONS_GEOJSON_PATH,
) -> None:
    path = MapService().generate(target, intersections)
    console.print(f"Mapa HTML: {path}")


@app.command("run-all")
def run_all(
    setor: str = typer.Option(...),
    quadra: str = typer.Option(...),
    lote: str = typer.Option(...),
) -> None:
    info, raw_path, processed_path = LoteService().fetch_lote(setor, quadra, lote)
    layers, layers_path = LayerDiscoveryService().discover()
    csv_path, geojson_path = IntersectionService().intersect(processed_path, layers_path)
    props_path = PROCESSED_DIR / f"target_lote_{setor}_{quadra}_{lote}_properties.json"
    report_base = f"{setor}_{quadra}_{lote}"
    markdown_path, json_path = ReportService().generate(
        props_path,
        csv_path,
        markdown_path=Path("data") / "reports" / f"relatorio_{report_base}.md",
        json_path=Path("data") / "reports" / f"relatorio_{report_base}.json",
    )
    try:
        map_path = MapService().generate(
            processed_path,
            geojson_path,
            output_path=Path("data") / "reports" / f"mapa_{report_base}.html",
        )
    except Exception as exc:
        map_path = None
        console.print(f"Mapa HTML não foi gerado: {exc}")

    console.print(f"SQL base: {info.sql_base or ''}")
    console.print(f"SQL completo: {info.sql_completo or ''}")
    console.print(f"Tipo quadra: {info.tipo_quadra or ''}")
    console.print(f"Tipo lote: {info.tipo_lote or ''}")
    console.print(f"Arquivo bruto: {raw_path}")
    console.print(f"Arquivo processado: {processed_path}")
    console.print(f"Inventário de camadas: {layers_path}")
    console.print(f"Camadas candidatas: {sum(layer.is_candidate for layer in layers)}")
    console.print(f"Interseções CSV: {csv_path}")
    console.print(f"Interseções GeoJSON: {geojson_path}")
    console.print(f"Relatório Markdown: {markdown_path}")
    console.print(f"Relatório JSON: {json_path}")
    if map_path:
        console.print(f"Mapa HTML: {map_path}")


@app.command("investigar")
def investigar(
    setor: str = typer.Option(...),
    quadra: str = typer.Option(...),
    lote: str = typer.Option(...),
) -> None:
    info, raw_path, processed_path = LoteService().fetch_lote(setor, quadra, lote)
    props_path = PROCESSED_DIR / f"target_lote_{setor}_{quadra}_{lote}_properties.json"
    report_base = f"{setor}_{quadra}_{lote}"

    layers, layers_path = LayerDiscoveryService().discover()
    csv_path, geojson_path = IntersectionService().intersect(processed_path, layers_path)
    _sources, sources_csv, _sources_json = SourceDiscoveryService().discover()
    references, references_csv, _references_json = DocumentReferenceService().generate(
        intersections_path=geojson_path,
        target_properties_path=props_path,
    )
    dossier_md, _dossier_json = DossierService().generate(
        target_properties_path=props_path,
        intersections_path=csv_path,
        document_references_path=references_csv,
        official_sources_path=sources_csv,
        markdown_path=REPORTS_DIR / f"dossie_{report_base}.md",
        json_path=REPORTS_DIR / f"dossie_{report_base}.json",
    )
    ValidationMatrixService().generate(
        intersections_path=csv_path,
        document_references_path=references_csv,
        official_sources_path=sources_csv,
    )
    LegalValidationService().generate(document_references_path=references_csv)
    _occupation, occupation_csv, _occupation_json = OccupationService().generate(
        intersections_path=csv_path,
        intersections_geojson_path=geojson_path,
    )
    divergences, divergence_csv, _divergence_json = CadastralDivergenceService().generate(
        target_properties_path=props_path,
        occupation_indicators_path=occupation_csv,
    )
    risks, risk_csv, _risk_json = RiskMatrixService().generate(intersections_path=csv_path)
    drawings, drawings_csv, _drawings_json = DrawingAssociationService().generate(
        document_references_path=references_csv,
    )
    legislation, legislation_csv, _legislation_json = LegislationLookupService().generate(
        document_references_path=references_csv,
    )
    pdfs, pdfs_csv, _pdfs_json = PdfDocumentService().generate()

    try:
        map_path = MapService().generate(
            processed_path,
            geojson_path,
            output_path=REPORTS_DIR / f"mapa_{report_base}.html",
        )
    except Exception as exc:
        map_path = None
        console.print(f"Mapa HTML não foi gerado: {exc}")

    summary_path = SummaryService().generate(
        target_properties_path=props_path,
        risk_matrix_path=risk_csv,
        cadastral_divergence_path=divergence_csv,
        drawing_requests_path=drawings_csv,
        legislation_lookup_path=legislation_csv,
        pdf_documents_path=pdfs_csv,
        output_path=REPORTS_DIR / f"resumo_{report_base}.md",
    )

    console.print(f"SQL base: {info.sql_base or ''}")
    console.print(f"Arquivo bruto: {raw_path}")
    console.print(f"Camadas candidatas: {sum(layer.is_candidate for layer in layers)}")
    console.print(f"Referências documentais: {len(references)}")
    alto_critico = sum(1 for risk in risks if risk.risk_level in ("ALTO", "CRITICO"))
    console.print(f"Achados ALTO/CRITICO na matriz de risco: {alto_critico}")
    console.print(f"Divergências cadastro x ocupação: {sum(d.divergencia for d in divergences)}")
    console.print(f"Plantas/croquis a solicitar: {len(drawings)}")
    console.print(f"Referências legislativas a confirmar: {len(legislation)}")
    console.print(f"Referências extraídas de PDFs locais: {len(pdfs)}")
    if map_path:
        console.print(f"Mapa HTML: {map_path}")
    console.print(f"Dossiê: {dossier_md}")
    console.print(f"Resumo investigativo: {summary_path}")
