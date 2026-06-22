from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DocumentReference:
    reference_type: str
    value: str
    source_layer: str | None
    source_field: str
    source_title: str | None = None
    year: str | None = None
    validation_status: str = "PENDENTE"
    validation_hint: str | None = None
    raw_context: str | None = None

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

