# GeoSampa Lote Analyzer

Ferramenta Python para consultar dados públicos do GeoSampa via WFS e cruzar a geometria de um lote ou área com camadas públicas relevantes.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Uso

Pipeline completo:

```bash
python -m geosampa_lote_analyzer run-all --setor <setor> --quadra <quadra> --lote <lote>
```

Comandos individuais:

```bash
python -m geosampa_lote_analyzer fetch-lote --setor <setor> --quadra <quadra> --lote <lote>
python -m geosampa_lote_analyzer discover-layers
python -m geosampa_lote_analyzer intersect
python -m geosampa_lote_analyzer report
python -m geosampa_lote_analyzer map
```

## Saídas

- `data/raw/lote_<setor>_<quadra>_<lote>_raw.geojson`
- `data/processed/target_lote_<setor>_<quadra>_<lote>.geojson`
- `data/processed/target_lote_<setor>_<quadra>_<lote>_properties.json`
- `data/processed/candidate_layers_inventory.csv`
- `data/processed/intersections.csv`
- `data/processed/intersections.geojson`
- `data/reports/relatorio_<setor>_<quadra>_<lote>.md`
- `data/reports/relatorio_<setor>_<quadra>_<lote>.json`
- `data/reports/mapa_<setor>_<quadra>_<lote>.html`

## Limitações

Este projeto não substitui certidões oficiais, consulta a processos SEI, matrícula imobiliária ou parecer jurídico. Resultado vazio em uma camada não prova inexistência do fenômeno; pode indicar indisponibilidade, mudança de nome, limitação do WFS, erro de CRS ou ausência de dado público exposto naquele serviço.
