from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DumpMixin:
    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LoteInfo(DumpMixin):
    setor: str | None
    quadra: str | None
    lote: str | None
    digito_sql: str | None
    sql_base: str | None
    sql_completo: str | None
    tipo_quadra: str | None
    tipo_lote: str | None
    codigo_tipo_lote: str | None
    logradouro: str | None
    numero_porta: str | None
    area_terreno_m2: float | None
    area_construida_m2: float | None
    codigo_contribuinte: str | None
    raw_properties: dict[str, Any]


@dataclass
class LayerInfo(DumpMixin):
    type_name: str
    title: str | None = None
    abstract: str | None = None
    matched_keywords: list[str] = field(default_factory=list)
    default_crs: str | None = None
    bbox_minx: float | None = None
    bbox_miny: float | None = None
    bbox_maxx: float | None = None
    bbox_maxy: float | None = None
    is_candidate: bool = False
