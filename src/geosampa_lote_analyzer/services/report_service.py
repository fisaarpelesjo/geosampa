import csv
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, REPORTS_DIR
from geosampa_lote_analyzer.utils.files import write_json


class ReportService:
    def generate(
        self,
        target_properties_path: Path = PROCESSED_DIR / "target_lote_properties.json",
        intersections_path: Path = PROCESSED_DIR / "intersections.csv",
        markdown_path: Path = REPORTS_DIR / "relatorio_lote.md",
        json_path: Path = REPORTS_DIR / "relatorio_lote.json",
    ) -> tuple[Path, Path]:
        import json

        info = json.loads(target_properties_path.read_text(encoding="utf-8"))
        rows = self._read_rows(intersections_path)
        with_intersection = [row for row in rows if int(row.get("intersects_count") or 0) > 0]
        without_intersection = [
            row
            for row in rows
            if int(row.get("intersects_count") or 0) == 0 and row.get("status") != "ERROR"
        ]
        errors = [row for row in rows if row.get("status") == "ERROR"]

        markdown = self._markdown(info, rows, with_intersection, without_intersection, errors)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown, encoding="utf-8")
        write_json(
            json_path,
            {
                "lote": info,
                "camadas_analisadas": len(rows),
                "camadas_com_intersecao": len(with_intersection),
                "intersecoes": with_intersection,
                "falhas": errors,
            },
        )
        return markdown_path, json_path

    def _read_rows(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as file:
            return list(csv.DictReader(file))

    def _markdown(
        self,
        info: dict[str, Any],
        rows: list[dict[str, str]],
        with_intersection: list[dict[str, str]],
        without_intersection: list[dict[str, str]],
        errors: list[dict[str, str]],
    ) -> str:
        sql = info.get("sql_base") or "não identificado"
        tipo_quadra = info.get("tipo_quadra") or "não informado"
        tipo_lote = info.get("tipo_lote") or "não informado"
        lines = [
            f"# Relatório técnico — Lote/área {sql}",
            "",
            "## 1. Resumo executivo",
            "",
            (
                f"A área consultada corresponde ao cadastro base `{sql}`. "
                f"Na camada `geoportal:lote_cidadao`, o dado público retornado indica "
                f"`{tipo_quadra}` como tipo de quadra e `{tipo_lote}` como tipo de lote."
            ),
            "",
            (
                "Foram analisadas camadas públicas do GeoSampa relacionadas a área pública, "
                "parque, manancial, preservação ambiental, utilidade pública, interesse social "
                "e desapropriação. O resultado técnico está organizado abaixo por camada."
            ),
            "",
            (
                "Este relatório não substitui certidão oficial do DESAP, consulta a processo SEI, "
                "matrícula imobiliária, nem parecer jurídico."
            ),
            "",
            "## 2. Identificação cadastral",
            "",
            f"- SQL base: {info.get('sql_base') or 'não informado'}",
            f"- SQL completo: {info.get('sql_completo') or 'não informado'}",
            f"- Setor: {info.get('setor') or 'não informado'}",
            f"- Quadra: {info.get('quadra') or 'não informado'}",
            f"- Lote: {info.get('lote') or 'não informado'}",
            f"- Dígito SQL: {info.get('digito_sql') or 'não informado'}",
            f"- Código do contribuinte: {info.get('codigo_contribuinte') or 'não informado'}",
            "",
            "## 3. Geometria e localização",
            "",
            "A geometria oficial foi salva no diretório `data/processed`.",
            "",
            "## 4. Classificação cadastral",
            "",
            f"- Tipo quadra: {tipo_quadra}",
            f"- Tipo lote: {tipo_lote}",
            f"- Código tipo lote: {info.get('codigo_tipo_lote') or 'não informado'}",
            f"- Logradouro: {info.get('logradouro') or 'não informado'}",
            f"- Número de porta: {info.get('numero_porta') or 'não informado'}",
            "",
            "## 5. Camadas analisadas",
            "",
            f"Foram processadas {len(rows)} camadas candidatas.",
            "",
            "## 6. Interseções encontradas",
            "",
        ]
        lines.extend(
            self._table(with_intersection)
            if with_intersection
            else ["Não foram registradas interseções nas camadas processadas.", ""]
        )
        lines.extend(["## 7. Camadas sem interseção", ""])
        lines.extend(
            self._table(without_intersection[:50])
            if without_intersection
            else ["Nenhuma camada sem interseção foi registrada.", ""]
        )
        lines.extend(["## 8. Falhas ou limitações de consulta", ""])
        lines.extend(
            self._table(errors[:50])
            if errors
            else ["Não foram registradas falhas técnicas nas camadas processadas.", ""]
        )
        lines.extend(
            [
                "## 9. Indícios técnicos",
                "",
                (
                    "O dado público consultado indica classificação cadastral de espaço "
                    "livre/quadra pública quando esses campos aparecem preenchidos dessa "
                    "forma no WFS. Interseções espaciais devem ser interpretadas como "
                    "indícios técnicos, não como conclusão jurídica."
                ),
                "",
                "## 10. O que ainda precisa ser confirmado em fonte oficial",
                "",
                "- Certidão ou manifestação do DESAP, quando aplicável.",
                "- Consulta a processo SEI relacionado ao ponto exato.",
                "- Matrícula imobiliária ou documentação dominial.",
                "- Decreto e planta expropriatória, se houver.",
                "",
                "## 11. Arquivos gerados",
                "",
                "- `data/raw/lote_<setor>_<quadra>_<lote>_raw.geojson`",
                "- `data/processed/target_lote_<setor>_<quadra>_<lote>.geojson`",
                "- `data/processed/candidate_layers_inventory.csv`",
                "- `data/processed/intersections.csv`",
                "- `data/processed/intersections.geojson`",
                "- `data/reports/relatorio_<setor>_<quadra>_<lote>.json`",
                "",
                "## 12. Anexos técnicos",
                "",
                (
                    "As propriedades completas retornadas pela camada de lote foram salvas "
                    "em arquivo JSON no diretório `data/processed`."
                ),
                "",
            ]
        )
        return "\n".join(lines)

    def _table(self, rows: list[dict[str, str]]) -> list[str]:
        lines = [
            "| Camada | Status | Feições | Área interseção m² | Erro |",
            "| --- | --- | ---: | ---: | --- |",
        ]
        for row in rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        row.get("layer_type_name", ""),
                        row.get("status", ""),
                        row.get("intersects_count", "0"),
                        row.get("intersection_area_m2", "0"),
                        (row.get("error_message", "") or "").replace("|", "/"),
                    ]
                )
                + " |"
            )
        lines.append("")
        return lines
