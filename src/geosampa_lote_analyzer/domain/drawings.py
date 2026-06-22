from dataclasses import asdict, dataclass
from typing import Any

NOTE_LOCAL = (
    "Anexo local encontrado por nome de arquivo; confirmar se corresponde à planta correta."
)
NOTE_PENDING = (
    "Planta não localizada localmente; solicitar ao órgão responsável ou consultar fonte oficial."
)


@dataclass
class DrawingRequest:
    value: str
    source_layer: str | None
    source_field: str
    source_title: str | None
    status: str
    local_path: str | None = None
    note: str = NOTE_PENDING

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
