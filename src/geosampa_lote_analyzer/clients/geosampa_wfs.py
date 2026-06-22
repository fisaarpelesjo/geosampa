import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

from geosampa_lote_analyzer.config import Settings, settings
from geosampa_lote_analyzer.domain.constants import CACHE_DIR
from geosampa_lote_analyzer.utils.files import ensure_parent

logger = logging.getLogger(__name__)


class GeoSampaWfsClient:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.session = requests.Session()

    def get_feature(
        self,
        type_name: str,
        cql_filter: str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        bbox_crs: str | None = None,
        max_features: int | None = None,
        output_format: str = "application/json",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "GetFeature",
            "typeName": type_name,
            "outputFormat": output_format,
        }
        if cql_filter:
            params["CQL_FILTER"] = cql_filter
        if bbox:
            bbox_parts = [str(value) for value in bbox]
            if bbox_crs:
                bbox_parts.append(bbox_crs)
            params["bbox"] = ",".join(bbox_parts)
        if max_features:
            params["maxFeatures"] = max_features

        logger.info("Consultando WFS GetFeature: %s", type_name)
        return self._request_json(self.config.wfs_base_url, params)

    def get_capabilities(self, version: str = "1.0.0") -> str:
        params = {"service": "WFS", "version": version, "request": "GetCapabilities"}
        logger.info("Consultando WFS GetCapabilities")
        return self._request_text(self.config.wfs_capabilities_url, params, suffix=".xml")

    def describe_feature_type(self, type_name: str) -> str:
        params = {
            "service": "WFS",
            "version": "1.0.0",
            "request": "DescribeFeatureType",
            "typeName": type_name,
        }
        logger.info("Consultando WFS DescribeFeatureType: %s", type_name)
        return self._request_text(self.config.wfs_base_url, params, suffix=".xml")

    def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        text = self._request_text(url, params, suffix=".json")
        return json.loads(text)

    def _request_text(self, url: str, params: dict[str, Any], suffix: str) -> str:
        cache_path = self._cache_path(url, params, suffix)
        if self.config.cache_enabled and cache_path.exists():
            logger.debug("Usando cache HTTP: %s", cache_path)
            return cache_path.read_text(encoding="utf-8")

        delays = [1, 3, 7]
        last_error: Exception | None = None
        for attempt, delay in enumerate(delays, start=1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.request_timeout_seconds,
                )
                response.raise_for_status()
                response.encoding = response.encoding or "utf-8"
                text = response.text
                if self.config.cache_enabled:
                    ensure_parent(cache_path).write_text(text, encoding="utf-8")
                return text
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("Falha HTTP na tentativa %s: %s", attempt, exc)
                if attempt < len(delays):
                    time.sleep(delay)
        raise RuntimeError(f"Falha ao consultar WFS: {last_error}") from last_error

    def _cache_path(self, url: str, params: dict[str, Any], suffix: str) -> Path:
        payload = json.dumps({"url": url, "params": params}, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}{suffix}"
