from dataclasses import asdict, dataclass
from typing import Any

LEGISLATION_REFERENCE_TYPES = {"DECRETO", "LEI", "LEGISLACAO", "DISPOSITIVO_LEGAL"}

MANUAL_CONFIRMATION_NOTE = (
    "Link de busca manual no Catálogo de Legislação Municipal. "
    "O site não expõe API de busca estável: confirmar número, ano, tipo e ementa "
    "manualmente antes de validar a referência."
)


@dataclass
class LegislationLookup:
    reference_type: str
    value: str
    number: str | None
    year: str | None
    search_url: str
    note: str = MANUAL_CONFIRMATION_NOTE

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
