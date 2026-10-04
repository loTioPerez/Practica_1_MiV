# Pràctica 1 — Modelització i Visualització de Dades

Redisseny crític d'una visualització de CNN sobre els esdeveniments entre Israel i Hezbollah utilitzant dades d'ACLED.

## Estructura

- `data/acled_raw.csv` → dades originals.
- `src/preprocessament.py` → filtratge, normalització i agregació de les dades.
- `output/dades_filtrades.csv` → dataset derivat utilitzat per la visualització.
- `src/app.py` → dashboard interactiu amb Streamlit i Plotly.
- `documentacio/Enunciat.pdf` → enunciat de la pràctica.

## Execució

Instal·lar dependències / Generar dades filtrades / Desplegar Dashboard:

```bash
pip install -r requirements.txt

python src/preprocessament.py

streamlit run src/app.py