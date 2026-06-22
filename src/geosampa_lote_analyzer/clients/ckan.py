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


class CkanClient:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.session = requests.Session()

    def package_search(self, query: str, rows: int = 10) -> dict[str, Any]:
        params: dict[str, Any] = {"q": query, "rows": rows}
        logger.info("Consultando Portal de Dados Abertos: %s", query)
        return self._request_json("package_search", params)

    def package_show(self, package_id: str) -> dict[str, Any]:
        params = {"id": package_id}
        logger.info("Consultando dataset no Portal de Dados Abertos: %s", package_id)
        return self._request_json("package_show", params)

    def _request_json(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.config.dados_abertos_api_url.rstrip('/')}/{action}"
        cache_path = self._cache_path(url, params)
        if self.config.cache_enabled and cache_path.exists():
            logger.debug("Usando cache CKAN: %s", cache_path)
            return json.loads(cache_path.read_text(encoding="utf-8"))

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
                data = response.json()
                if self.config.cache_enabled:
                    ensure_parent(cache_path).write_text(
                        json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                return data
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                logger.warning("Falha CKAN na tentativa %s: %s", attempt, exc)
                if attempt < len(delays):
                    time.sleep(delay)
        raise RuntimeError(f"Falha ao consultar CKAN: {last_error}") from last_error

    def _cache_path(self, url: str, params: dict[str, Any]) -> Path:
        payload = json.dumps({"url": url, "params": params}, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}.json"

