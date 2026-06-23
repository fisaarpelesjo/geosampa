from pathlib import Path

from geosampa_lote_analyzer.domain.constants import PROCESSED_DIR, REPORTS_DIR


class MapService:
    def generate(
        self,
        target_path: Path = PROCESSED_DIR / "target_lote.geojson",
        intersections_path: Path = PROCESSED_DIR / "intersections.geojson",
        output_path: Path = REPORTS_DIR / "mapa_lote.html",
    ) -> Path:
        import folium
        import geopandas as gpd

        target = gpd.read_file(target_path).to_crs("EPSG:4326")
        bounds = target.total_bounds
        center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
        mapa = folium.Map(location=center, zoom_start=17, tiles="OpenStreetMap")
        folium.GeoJson(
            target.to_json(),
            name="Lote alvo",
            style_function=lambda _feature: {
                "color": "#d7191c",
                "weight": 3,
                "fillColor": "#fdae61",
                "fillOpacity": 0.35,
            },
        ).add_to(mapa)

        if intersections_path.exists():
            intersections = gpd.read_file(intersections_path).to_crs("EPSG:4326")
            if not intersections.empty:
                intersections = self._json_safe(intersections)
                folium.GeoJson(
                    intersections.to_json(),
                    name="Interseções",
                    style_function=lambda _feature: {
                        "color": "#2c7bb6",
                        "weight": 2,
                        "fillColor": "#abd9e9",
                        "fillOpacity": 0.45,
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["layer_type_name"]),
                ).add_to(mapa)

        folium.LayerControl().add_to(mapa)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mapa.save(str(output_path))
        return output_path

    def _json_safe(self, gdf):
        safe = gdf.copy()
        for column in safe.columns:
            if column == "geometry":
                continue
            if str(safe[column].dtype).startswith("datetime"):
                safe[column] = safe[column].astype(str)
        return safe
