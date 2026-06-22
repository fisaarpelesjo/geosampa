def geojson_crs_name(data: dict) -> str | None:
    crs = data.get("crs")
    if isinstance(crs, dict):
        props = crs.get("properties")
        if isinstance(props, dict):
            name = props.get("name")
            return str(name) if name else None
    return None

