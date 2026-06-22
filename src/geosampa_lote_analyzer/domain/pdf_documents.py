from dataclasses import asdict, dataclass
from typing import Any

ORGAO_KEYWORDS = [
    "svma",
    "sehab",
    "subprefeitura",
    "secretaria municipal",
    "prefeitura",
    "cartorio de registro de imoveis",
    "tabelionato",
    "diario oficial",
]

CAUTIOUS_NOTE = (
    "Texto extraído automaticamente de PDF local. Confirmar número, data, órgão e "
    "ementa no documento original antes de validar."
)


@dataclass
class PdfReferenceFinding:
    file_name: str
    page: int
    reference_type: str
    value: str
    orgao: str | None
    data_publicacao: str | None
    citation: str
    raw_context: str
    note: str = CAUTIOUS_NOTE

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
