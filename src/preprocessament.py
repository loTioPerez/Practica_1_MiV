import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURACIÓ
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = BASE_DIR / "data" / "acled_raw.csv"
OUTPUT_PATH = BASE_DIR / "output" / "dades_filtrades.csv"

DATA_INICI = "2023-10-08"
DATA_FI = "2026-09-07"

TIPUS_CNN = [
    "Air/drone strike",
    "Shelling/artillery/missile attack"
]

MAPA_ACTORS = {
    "Military Forces of Israel (2022-)": "Israel",
    "Hezbollah": "Hezbollah"
}


# ============================================================
# 1. CARREGAR I SELECCIONAR LES DADES D'INTERÈS
# ============================================================

df = pd.read_csv(INPUT_PATH)

df["event_date"] = pd.to_datetime(df["event_date"])

# Conservem únicament els tipus d'esdeveniment
# representats a la visualització original
df = df[
    df["sub_event_type"].isin(TIPUS_CNN)
].copy()

print("Files després de seleccionar els tipus d'atac:", len(df))


# ============================================================
# 2. PREPROCESSAMENT 1:
# NORMALITZACIÓ DELS ACTORS
# ============================================================

# Seleccionem només els dos actors estudiats
df = df[
    df["actor1"].isin(MAPA_ACTORS.keys())
].copy()

# Simplifiquem les denominacions originals d'ACLED
df["actor_origin"] = df["actor1"].map(MAPA_ACTORS)

print("\nEsdeveniments per actor:")
print(df["actor_origin"].value_counts())


# ============================================================
# 3. PREPROCESSAMENT 2:
# RECLASSIFICACIÓ GEOGRÀFICA
# ============================================================

def classificar_zona(fila):

    if fila["country"] == "Israel":
        return "Israel"

    if fila["country"] == "Lebanon":
        return "Lebanon"

    if fila["country"] == "Syria" and fila["admin1"] == "Quneitra":
        return "Quneitra / Golan"

    if fila["country"] == "Syria":
        return "Syria - other"

    return "Other"


df["zona_operativa"] = df.apply(
    classificar_zona,
    axis=1
)

print("\nEsdeveniments per zona:")
print(df["zona_operativa"].value_counts())


# ============================================================
# 4. DEFINIR ELS DOS ABASTS GEOGRÀFICS
# ============================================================

# Abast de la visualització original de CNN
df_cnn = df[
    df["country"].isin(["Israel", "Lebanon"])
].copy()

# Redisseny: mateix criteri, incorporant també Síria
df_ampliat = df[
    df["country"].isin(["Israel", "Lebanon", "Syria"])
].copy()


# ============================================================
# 5. VALIDAR L'EFECTE DEL CANVI GEOGRÀFIC
# ============================================================

resum = pd.DataFrame({
    "CNN": df_cnn["actor_origin"].value_counts(),
    "Ampliat": df_ampliat["actor_origin"].value_counts()
})

resum = resum.reindex(["Israel", "Hezbollah"])

resum["Diferencia"] = (
    resum["Ampliat"] - resum["CNN"]
)

resum["Increment_%"] = (
    resum["Diferencia"]
    / resum["CNN"]
    * 100
).round(2)

print("\nComparació CNN vs. abast ampliat:")
print(resum)


ratio_cnn = (
    resum.loc["Israel", "CNN"]
    / resum.loc["Hezbollah", "CNN"]
)

ratio_ampliat = (
    resum.loc["Israel", "Ampliat"]
    / resum.loc["Hezbollah", "Ampliat"]
)

print("\nRàtio Israel / Hezbollah:")
print("CNN:", round(ratio_cnn, 2))
print("Ampliat:", round(ratio_ampliat, 2))


# ============================================================
# 6. PREPROCESSAMENT 3:
# AGREGACIÓ TEMPORAL
# ============================================================

def agregar_per_dia(dataframe, scope):

    serie = (
        dataframe
        .groupby(["event_date", "actor_origin"])
        .size()
        .reset_index(name="events")
    )

    serie["scope"] = scope

    return serie


serie_cnn = agregar_per_dia(
    df_cnn,
    "CNN"
)

serie_ampliada = agregar_per_dia(
    df_ampliat,
    "Ampliat"
)

serie = pd.concat(
    [serie_cnn, serie_ampliada],
    ignore_index=True
)


# ============================================================
# 7. COMPLETAR ELS DIES SENSE ESDEVENIMENTS
# ============================================================

dates = pd.date_range(
    DATA_INICI,
    DATA_FI,
    freq="D"
)

actors = [
    "Israel",
    "Hezbollah"
]

scopes = [
    "CNN",
    "Ampliat"
]

index_complet = pd.MultiIndex.from_product(
    [dates, actors, scopes],
    names=[
        "event_date",
        "actor_origin",
        "scope"
    ]
)

serie_completa = (
    serie
    .set_index([
        "event_date",
        "actor_origin",
        "scope"
    ])
    .reindex(
        index_complet,
        fill_value=0
    )
    .reset_index()
)


# ============================================================
# 8. COMPROVACIÓ FINAL
# ============================================================

print("\nTotals finals:")
print(
    serie_completa
    .groupby(
        ["scope", "actor_origin"]
    )["events"]
    .sum()
)


# ============================================================
# 9. GUARDAR EL DATASET DERIVAT
# ============================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

serie_completa.to_csv(
    OUTPUT_PATH,
    index=False
)

print(
    "\nDataset generat:",
    OUTPUT_PATH
)