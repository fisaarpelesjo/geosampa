from geosampa_lote_analyzer.clients.geosampa_wfs import GeoSampaWfsClient


class GeoSampaMetadataClient:
    def __init__(self, wfs_client: GeoSampaWfsClient | None = None) -> None:
        self.wfs_client = wfs_client or GeoSampaWfsClient()

    def get_capabilities(self) -> str:
        return self.wfs_client.get_capabilities()

