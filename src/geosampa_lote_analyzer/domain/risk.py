from dataclasses import asdict, dataclass
from typing import Any

DEFAULT_CATEGORY_WEIGHTS = {
    "Área pública": 3,
    "DUP/DIS e desapropriação": 3,
    "Manancial, APP e represa": 3,
    "Parque e áreas verdes": 2,
    "ZEIS e zoneamento": 2,
    "Ocupação e infraestrutura": 1,
    "Cadastro municipal": 0,
    "Outras interseções": 0,
}

RISK_DISCLAIMER = (
    "Risco técnico é indício para priorizar verificação, não conclusão jurídica de "
    "domínio, posse ou irregularidade."
)


@dataclass
class RiskFinding:
    category: str
    layer_type_name: str
    layer_title: str | None
    status: str
    intersection_ratio: float
    weight: int
    risk_score: int
    risk_level: str
    note: str = RISK_DISCLAIMER

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def risk_level_from_score(score: int) -> str:
    if score >= 4:
        return "CRITICO"
    if score == 3:
        return "ALTO"
    if score == 2:
        return "MEDIO"
    return "BAIXO"
