import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    wfs_base_url: str = os.getenv(
        "GEOSAMPA_WFS_BASE_URL",
        "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/ows",
    )
    wfs_capabilities_url: str = os.getenv(
        "GEOSAMPA_WFS_CAPABILITIES_URL",
        "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/ows",
    )
    lote_layer: str = "geoportal:lote_cidadao"
    request_timeout_seconds: int = 60
    max_features_default: int = 500
    cache_enabled: bool = os.getenv("GEOSAMPA_CACHE_ENABLED", "true").lower() != "false"
    output_crs: str = "EPSG:4326"
    metric_crs: str = "EPSG:31983"
    data_dir: Path = Path("data")


settings = Settings()
