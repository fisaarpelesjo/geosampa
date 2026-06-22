import csv
import logging
from pathlib import Path

from lxml import etree

from geosampa_lote_analyzer.clients.geosampa_wfs import GeoSampaWfsClient
from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, RAW_DIR
from geosampa_lote_analyzer.domain.keywords import DEFAULT_LAYER_KEYWORDS
from geosampa_lote_analyzer.domain.models import LayerInfo
from geosampa_lote_analyzer.utils.files import ensure_parent
from geosampa_lote_analyzer.utils.text import match_keywords

logger = logging.getLogger(__name__)


class LayerDiscoveryService:
    def __init__(self, client: GeoSampaWfsClient | None = None) -> None:
        self.client = client or GeoSampaWfsClient()

    def discover(
        self,
        keywords: list[str] | None = None,
        output_path: Path = PROCESSED_DIR / "candidate_layers_inventory.csv",
    ) -> tuple[list[LayerInfo], Path]:
        keywords = keywords or DEFAULT_LAYER_KEYWORDS
        xml = self.client.get_capabilities()
        capabilities_path = RAW_DIR / "capabilities_wfs_1_0_0.xml"
        ensure_parent(capabilities_path).write_text(xml, encoding="utf-8")

        root = etree.fromstring(xml.encode("utf-8"))
        layers: list[LayerInfo] = []
        for feature_type in root.xpath(".//*[local-name()='FeatureType']"):
            name = self._first_text(feature_type, "Name")
            if not name:
                continue
            title = self._first_text(feature_type, "Title")
            abstract = self._first_text(feature_type, "Abstract")
            crs = self._first_text(feature_type, "DefaultSRS") or self._first_text(
                feature_type, "DefaultCRS"
            )
            bbox = self._bbox(feature_type)
            searchable = " ".join([name, title or "", abstract or ""])
            matches = match_keywords(searchable, keywords)
            layers.append(
                LayerInfo(
                    type_name=name,
                    title=title,
                    abstract=abstract,
                    matched_keywords=matches,
                    default_crs=crs,
                    bbox_minx=bbox[0],
                    bbox_miny=bbox[1],
                    bbox_maxx=bbox[2],
                    bbox_maxy=bbox[3],
                    is_candidate=bool(matches),
                )
            )

        self._write_inventory(output_path, layers)
        logger.info("Total de camadas no WFS: %s", len(layers))
        logger.info("Camadas candidatas: %s", sum(layer.is_candidate for layer in layers))
        return layers, output_path

    def _first_text(self, element: etree._Element, local_name: str) -> str | None:
        values = element.xpath(f"./*[local-name()='{local_name}']/text()")
        if not values:
            return None
        text = str(values[0]).strip()
        return text or None

    def _bbox(
        self, element: etree._Element
    ) -> tuple[float | None, float | None, float | None, float | None]:
        lower = element.xpath(".//*[local-name()='LowerCorner']/text()")
        upper = element.xpath(".//*[local-name()='UpperCorner']/text()")
        if lower and upper:
            try:
                minx, miny = (float(part) for part in str(lower[0]).split()[:2])
                maxx, maxy = (float(part) for part in str(upper[0]).split()[:2])
                return minx, miny, maxx, maxy
            except ValueError:
                pass
        latlon = element.xpath(".//*[local-name()='LatLongBoundingBox']")
        if latlon:
            attrs = latlon[0].attrib
            try:
                return (
                    float(attrs.get("minx", "")),
                    float(attrs.get("miny", "")),
                    float(attrs.get("maxx", "")),
                    float(attrs.get("maxy", "")),
                )
            except ValueError:
                pass
        return None, None, None, None

    def _write_inventory(self, path: Path, layers: list[LayerInfo]) -> None:
        ensure_parent(path)
        columns = [
            "type_name",
            "title",
            "abstract",
            "matched_keywords",
            "default_crs",
            "bbox_minx",
            "bbox_miny",
            "bbox_maxx",
            "bbox_maxy",
            "is_candidate",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for layer in layers:
                row = layer.model_dump()
                row["matched_keywords"] = ",".join(layer.matched_keywords)
                writer.writerow(row)
