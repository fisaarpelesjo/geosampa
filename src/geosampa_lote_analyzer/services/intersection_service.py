import csv
import json
import logging
from pathlib import Path
from typing import Any

from geosampa_lote_analyzer.clients.geosampa_wfs import GeoSampaWfsClient
from geosampa_lote_analyzer.config import settings
from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, RAW_DIR
from geosampa_lote_analyzer.utils.files import ensure_parent, safe_filename, write_json

logger = logging.getLogger(__name__)


class IntersectionService:
    def __init__(self, client: GeoSampaWfsClient | None = None) -> None:
        self.client = client or GeoSampaWfsClient()

    def intersect(
        self,
        target_path: Path = PROCESSED_DIR / "target_lote.geojson",
        layers_path: Path = PROCESSED_DIR / "candidate_layers_inventory.csv",
        csv_path: Path = PROCESSED_DIR / "intersections.csv",
        geojson_path: Path = PROCESSED_DIR / "intersections.geojson",
    ) -> tuple[Path, Path]:
        import geopandas as gpd

        target = gpd.read_file(target_path)
        if target.empty:
            raise RuntimeError("GeoJSON do lote alvo está vazio.")
        target = self._valid(target)
        bbox = tuple(float(value) for value in target.to_crs(settings.output_crs).total_bounds)
        target_metric = self._valid(target.to_crs(settings.metric_crs))
        target_geom = target_metric.geometry.iloc[0]
        target_area = float(target_geom.area)

        layers = self._read_candidate_layers(layers_path)
        rows: list[dict[str, Any]] = []
        intersection_features: list[dict[str, Any]] = []
        for layer in layers:
            row = self._process_layer(layer, bbox, target_metric, target_geom, target_area, gpd)
            rows.append(row)
            if row.get("_features"):
                intersection_features.extend(row.pop("_features"))

        self._write_rows(csv_path, rows)
        write_json(
            geojson_path,
            {"type": "FeatureCollection", "features": intersection_features},
        )
        logger.info("Camadas analisadas: %s", len(rows))
        logger.info("Camadas com interseção: %s", sum(r["intersects_count"] > 0 for r in rows))
        return csv_path, geojson_path

    def _process_layer(
        self,
        layer: dict[str, str],
        bbox: tuple[float, float, float, float],
        target_metric: Any,
        target_geom: Any,
        target_area: float,
        gpd: Any,
    ) -> dict[str, Any]:
        type_name = layer["type_name"]
        base_row: dict[str, Any] = {
            "layer_type_name": type_name,
            "layer_title": layer.get("title", ""),
            "features_downloaded": 0,
            "intersects_count": 0,
            "target_area_m2": target_area,
            "intersection_area_m2": 0.0,
            "intersection_ratio": 0.0,
            "matched_keywords": layer.get("matched_keywords", ""),
            "status": "NO_INTERSECTION",
            "error_message": "",
        }
        try:
            data = self.client.get_feature(
                type_name,
                bbox=bbox,
                max_features=settings.max_features_default,
            )
            raw_path = RAW_DIR / "candidate_layers_raw" / f"{safe_filename(type_name)}.geojson"
            write_json(raw_path, data)
            features = data.get("features", [])
            base_row["features_downloaded"] = len(features)
            if not features:
                return base_row

            gdf = gpd.GeoDataFrame.from_features(features, crs=settings.output_crs)
            if gdf.empty or gdf.geometry.is_empty.all():
                return base_row
            gdf = self._valid(gdf.to_crs(settings.metric_crs))
            intersects = gdf[gdf.intersects(target_geom)]
            if intersects.empty:
                return base_row

            intersections = intersects.geometry.intersection(target_geom)
            area = float(intersections.area.sum())
            touches_only = area <= 0.01 and bool(intersects.touches(target_geom).any())
            status = "TOUCHES_ONLY" if touches_only else "INTERSECTS"
            if bool(intersects.contains(target_geom).any()):
                status = "CONTAINS_TARGET"
            elif bool(target_metric.contains(intersects.unary_union).any()):
                status = "TARGET_CONTAINS_LAYER_FEATURE"

            base_row.update(
                {
                    "intersects_count": int(len(intersects)),
                    "intersection_area_m2": area,
                    "intersection_ratio": area / target_area if target_area else 0.0,
                    "status": status,
                    "_features": json.loads(
                        gpd.GeoDataFrame(
                            intersects.drop(columns="geometry"),
                            geometry=intersections,
                            crs=settings.metric_crs,
                        )
                        .to_crs(settings.output_crs)
                        .to_json()
                    ).get("features", []),
                }
            )
            for feature in base_row["_features"]:
                feature.setdefault("properties", {})["layer_type_name"] = type_name
            return base_row
        except Exception as exc:
            logger.warning("Falha ao processar camada %s: %s", type_name, exc)
            base_row.update({"status": "ERROR", "error_message": str(exc)})
            return base_row

    def _valid(self, gdf: Any) -> Any:
        try:
            gdf["geometry"] = gdf.geometry.make_valid()
        except AttributeError:
            gdf["geometry"] = gdf.geometry.buffer(0)
        return gdf

    def _read_candidate_layers(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as file:
            return [row for row in csv.DictReader(file) if row.get("is_candidate") == "True"]

    def _write_rows(self, path: Path, rows: list[dict[str, Any]]) -> None:
        ensure_parent(path)
        columns = [
            "layer_type_name",
            "layer_title",
            "features_downloaded",
            "intersects_count",
            "target_area_m2",
            "intersection_area_m2",
            "intersection_ratio",
            "matched_keywords",
            "status",
            "error_message",
        ]
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in columns})
