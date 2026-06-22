import csv
import json
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, REPORTS_DIR
from geosampa_lote_analyzer.utils.files import write_json
from geosampa_lote_analyzer.utils.text import keyword_in_text, normalize_text

CATEGORY_RULES = {
    "Cadastro municipal": ["lote_cidadao"],
    "Área pública": ["area_publica", "area publica", "cadastro_area_publica", "area_cedida"],
    "DUP/DIS e desapropriação": ["planta_dup", "planta_expropriatoria", "desap", "dup", "dis"],
    "Parque e áreas verdes": ["parque", "parq", "area_verde", "corredor_verde"],
    "Manancial, APP e represa": ["manancial", "billings", "represa", "hidrografia"],
    "ZEIS e zoneamento": ["zeis", "zoneamento", "macroarea", "macrozona"],
    "Ocupação e infraestrutura": [
        "iluminacao",
        "drenagem",
        "setor_censitario",
        "vulnerabilidade",
        "servico",
        "logradouro",
        "edificacao",
        "arruamento",
        "equipamento",
    ],
}


class DossierService:
    def generate(
        self,
        target_properties_path: Path = PROCESSED_DIR / "target_lote_properties.json",
        intersections_path: Path = PROCESSED_DIR / "intersections.csv",
        document_references_path: Path = PROCESSED_DIR / "document_references.csv",
        official_sources_path: Path = PROCESSED_DIR / "official_sources_inventory.csv",
        markdown_path: Path = REPORTS_DIR / "dossie_lote.md",
        json_path: Path = REPORTS_DIR / "dossie_lote.json",
    ) -> tuple[Path, Path]:
        lote = self._read_json(target_properties_path)
        intersections = self._read_csv(intersections_path)
        references = self._read_csv(document_references_path)
        sources = self._read_csv(official_sources_path)
        categorized = self._categorized_intersections(intersections)
        summary = {
            "camadas_analisadas": len(intersections),
            "camadas_com_intersecao": len(
                [row for row in intersections if self._int(row.get("intersects_count")) > 0]
            ),
            "referencias_documentais": len(references),
            "fontes_oficiais": len(sources),
            "categorias_com_achados": [
                category for category, rows in categorized.items() if rows
            ],
        }

        markdown = self._markdown(lote, summary, categorized, references, sources)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        write_json(
            json_path,
            {
                "lote": lote,
                "resumo": summary,
                "achados_por_categoria": categorized,
                "referencias_documentais": references,
                "fontes_oficiais": sources,
            },
        )
        return markdown_path, json_path

    def _categorized_intersections(
        self, intersections: list[dict[str, str]]
    ) -> dict[str, list[dict[str, str]]]:
        categorized = {category: [] for category in CATEGORY_RULES}
        categorized["Outras interseções"] = []
        for row in intersections:
            if self._int(row.get("intersects_count")) <= 0:
                continue
            text = normalize_text(
                " ".join(
                    [
                        row.get("layer_type_name", ""),
                        row.get("layer_title", ""),
                        row.get("matched_keywords", ""),
                    ]
                )
            )
            matched_category = None
            for category, rules in CATEGORY_RULES.items():
                if any(keyword_in_text(rule, text) for rule in rules):
                    matched_category = category
                    break
            categorized[matched_category or "Outras interseções"].append(row)
        return categorized

    def _markdown(
        self,
        lote: dict[str, Any],
        summary: dict[str, Any],
        categorized: dict[str, list[dict[str, str]]],
        references: list[dict[str, str]],
        sources: list[dict[str, str]],
    ) -> str:
        lines = [
            "# Dossiê técnico consolidado",
            "",
            "## Resumo",
            "",
            "Este dossiê consolida achados técnicos a partir de dados públicos consultados. "
            "Ele não substitui certidão oficial, processo administrativo, matrícula imobiliária "
            "ou parecer jurídico.",
            "",
            f"- Camadas analisadas: {summary['camadas_analisadas']}",
            f"- Camadas com interseção: {summary['camadas_com_intersecao']}",
            (
                "- Referências documentais pendentes de validação: "
                f"{summary['referencias_documentais']}"
            ),
            f"- Fontes oficiais inventariadas: {summary['fontes_oficiais']}",
            "",
            "## Cadastro consultado",
            "",
            f"- SQL base: {lote.get('sql_base') or 'não informado'}",
            f"- SQL completo: {lote.get('sql_completo') or 'não informado'}",
            f"- Tipo quadra: {lote.get('tipo_quadra') or 'não informado'}",
            f"- Tipo lote: {lote.get('tipo_lote') or 'não informado'}",
            f"- Código tipo lote: {lote.get('codigo_tipo_lote') or 'não informado'}",
            f"- Código do contribuinte: {lote.get('codigo_contribuinte') or 'não informado'}",
            f"- Logradouro: {lote.get('logradouro') or 'não informado'}",
            f"- Número de porta: {lote.get('numero_porta') or 'não informado'}",
            "",
            "## Achados por categoria",
            "",
        ]
        for category, rows in categorized.items():
            lines.extend([f"### {category}", ""])
            if not rows:
                lines.extend(["Sem interseções registradas nesta categoria.", ""])
                continue
            lines.extend(self._intersection_table(rows))

        lines.extend(
            [
                "## Referências documentais pendentes",
                "",
                "As referências abaixo foram extraídas de campos e textos das camadas consultadas. "
                "Cada item deve ser confirmado na fonte oficial indicada.",
                "",
            ]
        )
        lines.extend(
            self._reference_table(references[:80])
            if references
            else ["Nenhuma referência extraída.", ""]
        )
        lines.extend(["## Fontes oficiais para validação", ""])
        lines.extend(
            self._source_table(sources[:80])
            if sources
            else ["Nenhuma fonte inventariada.", ""]
        )
        lines.extend(
            [
                "## Interpretação cautelosa",
                "",
                "- Interseção espacial é indício técnico, não conclusão jurídica.",
                "- Camada pública pode ter atualização, escala, CRS e metadados próprios.",
                "- Resultado vazio não prova inexistência de ato ou restrição.",
                (
                    "- Documentos legais, processos e matrículas precisam ser confirmados "
                    "nas fontes oficiais."
                ),
                "",
            ]
        )
        return "\n".join(lines)

    def _intersection_table(self, rows: list[dict[str, str]]) -> list[str]:
        lines = [
            "| Camada | Título | Status | Feições | Área m² | Percentual |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
        sorted_rows = sorted(
            rows,
            key=lambda item: self._float(item.get("intersection_ratio")),
            reverse=True,
        )
        for row in sorted_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._cell(row.get("layer_type_name")),
                        self._cell(row.get("layer_title")),
                        self._cell(row.get("status")),
                        str(self._int(row.get("intersects_count"))),
                        f"{self._float(row.get('intersection_area_m2')):.2f}",
                        f"{self._float(row.get('intersection_ratio')) * 100:.2f}%",
                    ]
                )
                + " |"
            )
        lines.append("")
        return lines

    def _reference_table(self, rows: list[dict[str, str]]) -> list[str]:
        lines = [
            "| Tipo | Valor | Camada | Campo | Status | Onde validar |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for row in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._cell(row.get("reference_type")),
                        self._cell(row.get("value")),
                        self._cell(row.get("source_layer")),
                        self._cell(row.get("source_field")),
                        self._cell(row.get("validation_status")),
                        self._cell(row.get("validation_hint")),
                    ]
                )
                + " |"
            )
        lines.append("")
        return lines

    def _source_table(self, rows: list[dict[str, str]]) -> list[str]:
        lines = [
            "| Fonte | Título | Categorias | Pontuação | Status |",
            "| --- | --- | --- | ---: | --- |",
        ]
        sorted_rows = sorted(
            rows,
            key=lambda item: self._int(item.get("relevance_score")),
            reverse=True,
        )
        for row in sorted_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        self._cell(row.get("source_name")),
                        self._cell(row.get("title")),
                        self._cell(row.get("validation_categories")),
                        str(self._int(row.get("relevance_score"))),
                        self._cell(row.get("status")),
                    ]
                )
                + " |"
            )
        lines.append("")
        return lines

    def _read_json(self, path: Path) -> dict[str, Any]:
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

    def _float(self, value: str | None) -> float:
        try:
            return float(value or 0)
        except ValueError:
            return 0.0

    def _cell(self, value: Any) -> str:
        return str(value or "").replace("|", "/").replace("\n", " ").strip()
