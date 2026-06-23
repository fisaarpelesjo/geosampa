import csv
import json
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, REPORTS_DIR
from geosampa_lote_analyzer.utils.files import ensure_parent

CAUTIOUS_NOTES = [
    "Interseção espacial e divergência cadastral são indício técnico, não conclusão jurídica.",
    "Risco técnico prioriza verificação; não comprova domínio, posse ou irregularidade.",
    "Toda referência legal (decreto, lei, dispositivo) precisa ser confirmada na fonte oficial.",
    (
        "Cadastro vazio é compatível com área pública regular ou com pendência cadastral; "
        "não decide a hipótese por si só."
    ),
]


class SummaryService:
    def generate(
        self,
        target_properties_path: Path = PROCESSED_DIR / "target_lote_properties.json",
        risk_matrix_path: Path = PROCESSED_DIR / "risk_matrix.csv",
        cadastral_divergence_path: Path = PROCESSED_DIR / "cadastral_divergence.csv",
        drawing_requests_path: Path = PROCESSED_DIR / "drawing_requests.csv",
        legislation_lookup_path: Path = PROCESSED_DIR / "legislation_lookup.csv",
        pdf_documents_path: Path = PROCESSED_DIR / "pdf_documents_index.csv",
        output_path: Path = REPORTS_DIR / "resumo_lote.md",
    ) -> Path:
        cadastro = self._read_json(target_properties_path)
        risk_rows = self._read_csv(risk_matrix_path)
        divergence_rows = self._read_csv(cadastral_divergence_path)
        drawing_rows = self._read_csv(drawing_requests_path)
        legislation_rows = self._read_csv(legislation_lookup_path)
        pdf_rows = self._read_csv(pdf_documents_path)

        markdown = self._markdown(
            cadastro,
            risk_rows,
            divergence_rows,
            drawing_rows,
            legislation_rows,
            pdf_rows,
        )
        ensure_parent(output_path).write_text(markdown, encoding="utf-8")
        return output_path

    def _markdown(
        self,
        cadastro: dict[str, Any],
        risk_rows: list[dict[str, str]],
        divergence_rows: list[dict[str, str]],
        drawing_rows: list[dict[str, str]],
        legislation_rows: list[dict[str, str]],
        pdf_rows: list[dict[str, str]],
    ) -> str:
        sql_base = cadastro.get("sql_base") or "não informado"
        lines = [f"# Resumo investigativo — Lote {sql_base}", "", "## Cadastro", ""]
        lines.extend(self._cadastro_lines(cadastro))
        lines.extend(["", "## Achados de risco técnico", ""])
        lines.extend(self._risk_lines(risk_rows))
        lines.extend(["", "## Divergência cadastral x ocupação aparente", ""])
        lines.extend(self._divergence_lines(divergence_rows))
        lines.extend(["", "## Legislação a confirmar", ""])
        lines.extend(self._legislation_lines(legislation_rows))
        lines.extend(["", "## Plantas e croquis a solicitar", ""])
        lines.extend(self._drawing_lines(drawing_rows))
        lines.extend(["", "## PDFs oficiais indexados", ""])
        lines.extend(self._pdf_lines(pdf_rows))
        lines.extend(["", "## Leitura cautelosa", ""])
        lines.extend(f"- {note}" for note in CAUTIOUS_NOTES)
        lines.append("")
        return "\n".join(lines)

    def _cadastro_lines(self, cadastro: dict[str, Any]) -> list[str]:
        if not cadastro:
            return ["Cadastro não disponível."]
        fields = [
            ("Tipo quadra / tipo lote", "tipo_quadra", "tipo_lote"),
            ("Código do contribuinte", "codigo_contribuinte", None),
            ("Número de porta / logradouro", "numero_porta", "logradouro"),
            ("Área terreno / área construída (m²)", "area_terreno_m2", "area_construida_m2"),
        ]
        lines = []
        for label, key_a, key_b in fields:
            value_a = cadastro.get(key_a) or "não informado"
            if key_b:
                value_b = cadastro.get(key_b) or "não informado"
                lines.append(f"- {label}: {value_a} / {value_b}")
            else:
                lines.append(f"- {label}: {value_a}")
        return lines

    def _risk_lines(self, rows: list[dict[str, str]]) -> list[str]:
        if not rows:
            return ["Matriz de risco não disponível."]
        by_level = {"CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAIXO": 0}
        for row in rows:
            level = row.get("risk_level", "")
            if level in by_level:
                by_level[level] += 1
        summary = ", ".join(f"{level}: {count}" for level, count in by_level.items())
        lines = [summary, ""]
        relevant = [row for row in rows if row.get("risk_level") in {"CRITICO", "ALTO"}]
        if not relevant:
            lines.append("Nenhum achado CRITICO ou ALTO.")
            return lines
        lines.append("| Nível | Categoria | Camada | % sobreposição |")
        lines.append("| --- | --- | --- | ---: |")
        for row in sorted(relevant, key=lambda r: self._int(r.get("risk_score")), reverse=True):
            ratio = self._float(row.get("intersection_ratio")) * 100
            lines.append(
                f"| {row.get('risk_level', '')} | {row.get('category', '')} | "
                f"{row.get('layer_type_name', '')} | {ratio:.1f}% |"
            )
        return lines

    def _divergence_lines(self, rows: list[dict[str, str]]) -> list[str]:
        if not rows:
            return ["Nenhuma comparação cadastro x ocupação disponível."]
        flagged = [row for row in rows if row.get("divergencia") == "True"]
        lines = [f"{len(flagged)} de {len(rows)} sinais com divergência (cadastro vazio)."]
        if flagged:
            lines.append("")
            for row in flagged:
                lines.append(
                    f"- {row.get('category', '')}: {row.get('layer_type_name', '')} "
                    f"(campo cadastral vazio: {row.get('cadastral_field', '')})"
                )
        return lines

    def _legislation_lines(self, rows: list[dict[str, str]]) -> list[str]:
        if not rows:
            return ["Nenhuma referência legislativa para confirmar."]
        lines = ["| Tipo | Valor | Link de busca |", "| --- | --- | --- |"]
        for row in rows:
            lines.append(
                f"| {row.get('reference_type', '')} | {row.get('value', '')} | "
                f"{row.get('search_url', '')} |"
            )
        return lines

    def _drawing_lines(self, rows: list[dict[str, str]]) -> list[str]:
        if not rows:
            return ["Nenhuma planta ou croqui referenciado."]
        found = sum(row.get("status") == "ANEXO_LOCAL_ENCONTRADO" for row in rows)
        lines = [f"{len(rows)} itens ({found} com anexo local, {len(rows) - found} a solicitar)."]
        lines.append("")
        for row in rows:
            lines.append(f"- {row.get('value', '')} ({row.get('source_layer', '')})")
        return lines

    def _pdf_lines(self, rows: list[dict[str, str]]) -> list[str]:
        if not rows:
            return ["Nenhum PDF local indexado em data/anexos."]
        lines = [f"{len(rows)} referências extraídas de PDFs locais."]
        lines.append("")
        for row in rows:
            lines.append(
                f"- {row.get('reference_type', '')} {row.get('value', '')} "
                f"({row.get('citation', '')})"
            )
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
