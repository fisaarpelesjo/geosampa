import logging
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.clients.geosampa_wfs import GeoSampaWfsClient
from geosampa_lote_analyzer.config import settings
from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, RAW_DIR
from geosampa_lote_analyzer.domain.models import LoteInfo
from geosampa_lote_analyzer.utils.cql import build_lote_cql
from geosampa_lote_analyzer.utils.files import write_json

logger = logging.getLogger(__name__)


def safe_get(props: dict[str, Any], *names: str) -> Any:
    normalized = {key.lower(): value for key, value in props.items()}
    for name in names:
        if name in props:
            return props[name]
        lowered = name.lower()
        if lowered in normalized:
            return normalized[lowered]
    return None


def as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def build_lote_info(properties: dict[str, Any]) -> LoteInfo:
    setor = as_text(safe_get(properties, "cd_setor_fiscal", "setor"))
    quadra = as_text(safe_get(properties, "cd_quadra_fiscal", "quadra"))
    lote = as_text(safe_get(properties, "cd_lote", "lote"))
    digito = as_text(safe_get(properties, "cd_digito_sql", "digito_sql"))
    sql_base = f"{setor}.{quadra}.{lote}" if setor and quadra and lote else None
    sql_completo = f"{sql_base}-{digito}" if sql_base and digito else None
    return LoteInfo(
        setor=setor,
        quadra=quadra,
        lote=lote,
        digito_sql=digito,
        sql_base=sql_base,
        sql_completo=sql_completo,
        tipo_quadra=as_text(safe_get(properties, "tx_tipo_quadra", "tipo_quadra")),
        tipo_lote=as_text(safe_get(properties, "tx_tipo_lote", "tipo_lote")),
        codigo_tipo_lote=as_text(safe_get(properties, "cd_tipo_lote")),
        logradouro=as_text(safe_get(properties, "nm_logradouro_completo", "nm_logradouro")),
        numero_porta=as_text(safe_get(properties, "cd_numero_porta", "numero_porta")),
        area_terreno_m2=as_float(safe_get(properties, "qt_area_terreno", "area_terreno")),
        area_construida_m2=as_float(safe_get(properties, "qt_area_construida", "area_construida")),
        codigo_contribuinte=as_text(safe_get(properties, "cd_contribuinte", "codigo_contribuinte")),
        raw_properties=properties,
    )


class LoteService:
    def __init__(self, client: GeoSampaWfsClient | None = None) -> None:
        self.client = client or GeoSampaWfsClient()

    def fetch_lote(self, setor: str, quadra: str, lote: str) -> tuple[LoteInfo, Path, Path]:
        cql = build_lote_cql(setor, quadra, lote)
        raw = self.client.get_feature(settings.lote_layer, cql_filter=cql)
        features = raw.get("features", [])
        logger.info("Features encontradas para o lote: %s", len(features))
        if not features:
            raise RuntimeError(f"Nenhuma feature encontrada para {setor}.{quadra}.{lote}")

        raw_path = RAW_DIR / f"lote_{setor}_{quadra}_{lote}_raw.geojson"
        processed_path = PROCESSED_DIR / f"target_lote_{setor}_{quadra}_{lote}.geojson"
        props_path = PROCESSED_DIR / f"target_lote_{setor}_{quadra}_{lote}_properties.json"

        write_json(raw_path, raw)
        processed = dict(raw)
        processed["features"] = [features[0]]
        write_json(processed_path, processed)

        info = build_lote_info(features[0].get("properties", {}))
        write_json(props_path, info.model_dump())
        logger.info("Lote processado salvo em: %s", processed_path)
        return info, raw_path, processed_path

