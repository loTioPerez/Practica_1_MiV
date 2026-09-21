import pandas as pd
from pathlib import Path

# 1. Carregar dades
data_dir = Path(__file__).resolve().parents[1] / "data"
csv_files = list(data_dir.glob("*.csv"))

if len(csv_files) != 1:
    raise FileNotFoundError(
        f"S'esperava trobar exactament un CSV a {data_dir}, pero se n'han trobat {len(csv_files)}."
    )

df = pd.read_csv(csv_files[0])

# 2. Filtrar els subtipus utilitzats per CNN
tipus = [
    "Air/drone strike",
    "Shelling/artillery/missile attack"
]

df_filtrat = df[df["sub_event_type"].isin(tipus)]

# 3. Identificar actors
actors = [
    "Hezbollah",
    "Military Forces of Israel (2022-)"
]

df_actors = df_filtrat[
    df_filtrat["actor1"].isin(actors)
]

# 4. Reproduir l'abast geogràfic de CNN
df_cnn = df_actors[
    df_actors["country"].isin(["Israel", "Lebanon"])
]

print("VERSIÓ CNN")
print(df_cnn["actor1"].value_counts())

# 5. Mirar els esdeveniments de Síria
df_siria = df_actors[
    df_actors["country"] == "Syria"
]

print("\nSÍRIA")
print(df_siria["actor1"].value_counts())

# 6. Mirar on apareix Hezbollah dins de Síria
hezbollah_siria = df_siria[
    df_siria["actor1"] == "Hezbollah"
]

print("\nHEZBOLLAH A SÍRIA PER ADMIN1")
print(hezbollah_siria["admin1"].value_counts())
