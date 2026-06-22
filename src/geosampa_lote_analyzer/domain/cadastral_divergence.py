from dataclasses import asdict, dataclass
from typing import Any

CATEGORY_CADASTRAL_FIELDS = {
    "EDIFICACAO": "area_construida_m2",
    "VIAS": "numero_porta",
    "ILUMINACAO": "numero_porta",
    "SERVICO_PUBLICO": "codigo_contribuinte",
    "EQUIPAMENTO_URBANO": "codigo_contribuinte",
    "DRENAGEM": "codigo_contribuinte",
}

CAUTIOUS_NOTE = (
    "Indício técnico de divergência entre cadastro fiscal e ocupação aparente. "
    "Não comprova posse, domínio ou irregularidade: exige confirmação em campo ou fonte oficial."
)


@dataclass
class CadastralDivergence:
    category: str
    layer_type_name: str
    cadastral_field: str
    cadastral_value: str | None
    intersects_count: int
    divergencia: bool
    note: str = CAUTIOUS_NOTE

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
