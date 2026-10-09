# Pràctica 1 — Modelització i Visualització de Dades

Redisseny d'una visualització de CNN sobre els esdeveniments entre Israel i Hezbollah utilitzant dades d'ACLED.

La visualització representa la distribució espaciotemporal dels esdeveniments a Israel, Líban i Síria.

## Estructura

- `data/acled_raw.csv` — dades originals d'ACLED.
- `src/preprocessament.py` — filtratge, normalització i agregació de les dades.
- `output/dades_visualitzacio.csv` — dataset processat utilitzat pel dashboard.
- `src/app.py` — dashboard interactiu.
- `documentacio/Enunciat.pdf` — enunciat de la pràctica.

## Execució

Instal·lar dependències:

    pip install -r requirements.txt

Executar el preprocessament:

    python src/preprocessament.py

Executar el dashboard:

    streamlit run src/app.py

## Tecnologies

Python · Pandas · Plotly · Streamlit

## Font de dades

ACLED — Armed Conflict Location & Event Data.