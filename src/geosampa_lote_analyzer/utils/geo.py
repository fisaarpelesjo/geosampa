def geojson_crs_name(data: dict) -> str | None:
    crs = data.get("crs")
    if isinstance(crs, dict):
        props = crs.get("properties")
        if isinstance(props, dict):
            name = props.get("name")
            return str(name) if name else None
    return None


def normalize_crs(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    upper = text.upper()
    if upper.startswith("URN:OGC:DEF:CRS:EPSG"):
        return f"EPSG:{upper.rsplit(':', maxsplit=1)[-1]}"
    if "EPSG:" in upper:
        return f"EPSG:{upper.rsplit('EPSG:', maxsplit=1)[-1].split('/')[-1]}"
    return text
