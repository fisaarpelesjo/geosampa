from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class OfficialSource:
    source_type: str
    source_name: str
    title: str
    url: str
    query: str | None = None
    description: str | None = None
    organization: str | None = None
    resource_formats: list[str] = field(default_factory=list)
    resource_count: int = 0
    score: float | None = None
    status: str = "LOCALIZADO"
    notes: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)

