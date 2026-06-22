from dataclasses import asdict, dataclass, field
from typing import Any

OCCUPATION_CATEGORY_KEYWORDS = {
    "EDIFICACAO": ["edificacao", "edificação", "construcao", "construção"],
    "VIAS": ["via", "vias", "logradouro", "calcada", "calçada", "meio fio", "meio-fio"],
    "ILUMINACAO": ["iluminacao", "iluminação", "poste", "luminaria", "luminária"],
    "DRENAGEM": ["drenagem", "galeria", "bueiro", "boca de lobo"],
    "SERVICO_PUBLICO": [
        "servico publico",
        "serviço público",
        "setor censitario",
        "setor censitário",
        "vulnerabilidade",
    ],
    "EQUIPAMENTO_URBANO": [
        "equipamento",
        "escola",
        "posto de saude",
        "posto de saúde",
        "praca",
        "praça",
    ],
}

CAUTIOUS_NOTE = (
    "Indício técnico de proximidade com edificação ou infraestrutura urbana. "
    "Não comprova ocupação humana, posse ou moradia: exige confirmação em campo ou fonte oficial."
)


@dataclass
class OccupationFinding:
    layer_type_name: str
    layer_title: str | None
    category: str
    geometry_types: list[str] = field(default_factory=list)
    intersects_count: int = 0
    intersection_ratio: float = 0.0
    status: str = ""
    note: str = CAUTIOUS_NOTE

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
