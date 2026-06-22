def quote_cql_string(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def build_lote_cql(setor: str, quadra: str, lote: str) -> str:
    return (
        f"cd_setor_fiscal={quote_cql_string(setor)} "
        f"AND cd_quadra_fiscal={quote_cql_string(quadra)} "
        f"AND cd_lote={quote_cql_string(lote)}"
    )

