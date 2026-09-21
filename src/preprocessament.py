import pandas as pd
from pathlib import Path

# ============================================================
# 1. CARREGAR LES DADES ORIGINALS
# ============================================================

csv_path = Path(__file__).resolve().parents[1] / "data" / "acled_raw.csv"
df = pd.read_csv(csv_path)

# Convertim la data de text a tipus data
df["event_date"] = pd.to_datetime(df["event_date"])

print("FILES ORIGINALS:", len(df))
print("\nPAÏSOS DEL DATASET:")
print(df["country"].value_counts())


# ============================================================
# 2. REPRODUIR ELS TIPUS D'ATAC UTILITZATS PER CNN
# ============================================================

tipus_cnn = [
    "Air/drone strike",
    "Shelling/artillery/missile attack"
]

df_tipus = df[
    df["sub_event_type"].isin(tipus_cnn)
].copy()

print("\nFILES DESPRÉS DE FILTRAR ELS TIPUS D'ATAC:")
print(len(df_tipus))


# ============================================================
# 3. PREPROCESSAMENT 1: NORMALITZACIÓ DELS ACTORS
# ============================================================

mapa_actors = {
    "Military Forces of Israel (2022-)": "Israel",
    "Hezbollah": "Hezbollah"
}

# Ens quedem únicament amb els dos actors principals
df_actors = df_tipus[
    df_tipus["actor1"].isin(mapa_actors.keys())
].copy()

# Creem una denominació simplificada
df_actors["actor_origin"] = df_actors["actor1"].map(mapa_actors)

print("\nESDEVENIMENTS PER ACTOR:")
print(df_actors["actor_origin"].value_counts())


# ============================================================
# 4. PREPROCESSAMENT 2: RECLASSIFICACIÓ GEOGRÀFICA
# ============================================================

def classificar_zona(fila):

    if fila["country"] == "Israel":
        return "Israel"

    elif fila["country"] == "Lebanon":
        return "Lebanon"

    elif fila["country"] == "Syria" and fila["admin1"] == "Quneitra":
        return "Quneitra / Golan"

    elif fila["country"] == "Syria":
        return "Syria - other"

    else:
        return "Other"


df_actors["zona_operativa"] = df_actors.apply(
    classificar_zona,
    axis=1
)

# Marquem quines files formarien part de la visualització de CNN
df_actors["scope_cnn"] = df_actors["country"].isin(
    ["Israel", "Lebanon"]
)

print("\nZONES OPERATIVES:")
print(df_actors["zona_operativa"].value_counts())


# ============================================================
# 5. COMPROVACIÓ DE LA RECONSTRUCCIÓ CNN
# ============================================================

df_cnn = df_actors[
    df_actors["scope_cnn"]
].copy()

print("\nVERSIÓ CNN:")
print(df_cnn["actor_origin"].value_counts())


# ============================================================
# 6. QUÈ QUEDA FORA A SÍRIA?
# ============================================================

df_siria = df_actors[
    df_actors["country"] == "Syria"
].copy()

print("\nESDEVENIMENTS A SÍRIA:")
print(df_siria["actor_origin"].value_counts())

print("\nHEZBOLLAH A SÍRIA PER REGIÓ:")
print(
    df_siria[
        df_siria["actor_origin"] == "Hezbollah"
    ]["admin1"].value_counts()
)


# ============================================================
# 7. COMPROVACIÓ DELS OBJECTIUS DELS ATACS A SÍRIA
# ============================================================

israel_siria = df_siria[
    df_siria["actor_origin"] == "Israel"
].copy()

hezbollah_siria = df_siria[
    df_siria["actor_origin"] == "Hezbollah"
].copy()


print("\nOBJECTIUS DELS ATACS ISRAELIANS A SÍRIA:")
print(
    israel_siria["actor2"]
    .value_counts(dropna=False)
    .head(20)
)


print("\nOBJECTIUS DELS ATACS DE HEZBOLLAH A SÍRIA:")
print(
    hezbollah_siria["actor2"]
    .value_counts(dropna=False)
    .head(20)
)


print("\nACTORS ASSOCIATS ALS OBJECTIUS DELS ATACS ISRAELIANS A SÍRIA:")

print(
    israel_siria["assoc_actor_2"]
    .value_counts(dropna=False)
    .head(20)
)


def conte_actor_associat(valor, actor):
    if pd.isna(valor):
        return False

    actors = [
        a.strip()
        for a in valor.split(";")
    ]

    return actor in actors


heizbollah_associat = israel_siria["assoc_actor_2"].apply(
    lambda x: conte_actor_associat(x, "Hezbollah")
)

israel_contra_hezbollah = israel_siria[
    (israel_siria["actor2"] == "Hezbollah")
    | heizbollah_associat
].copy()


print(
    "\nATACS ISRAELIANS A SÍRIA "
    "AMB HEZBOLLAH COM ACTOR2 O ACTOR ASSOCIAT:"
)

print(len(israel_contra_hezbollah))


# ============================================================
# 8. COMPROVAR EL CRITERI D'ACTOR2 DINS DE L'ABAST CNN
# ============================================================

print("\nOBJECTIUS DELS ATACS ISRAELIANS DINS DE L'ABAST CNN:")
print(
    df_cnn[
        df_cnn["actor_origin"] == "Israel"
    ]["actor2"].value_counts(dropna=False).head(10)
)

print("\nOBJECTIUS DELS ATACS DE HEZBOLLAH DINS DE L'ABAST CNN:")
print(
    df_cnn[
        df_cnn["actor_origin"] == "Hezbollah"
    ]["actor2"].value_counts(dropna=False).head(10)
)


# ============================================================
# 9. COMPARACIÓ CNN VS. ABAST GEOGRÀFIC AMPLIAT
# ============================================================

# CNN: només Israel + Líban
df_cnn = df_actors[
    df_actors["country"].isin(["Israel", "Lebanon"])
].copy()

# Versió ampliada:
# mateixos actors, mateixos tipus d'atac i mateixes dates,
# però incorporant també Síria
df_ampliat = df_actors[
    df_actors["country"].isin(
        ["Israel", "Lebanon", "Syria"]
    )
].copy()


resum = pd.DataFrame({
    "CNN": df_cnn["actor_origin"].value_counts(),
    "Ampliat": df_ampliat["actor_origin"].value_counts()
})

resum = resum.reindex(["Israel", "Hezbollah"])

resum["Diferencia"] = (
    resum["Ampliat"] - resum["CNN"]
)

resum["Increment_%"] = (
    resum["Diferencia"] / resum["CNN"] * 100
).round(2)

print("\nCOMPARACIÓ CNN VS. ABAST AMPLIAT:")
print(resum)


ratio_cnn = (
    resum.loc["Israel", "CNN"]
    / resum.loc["Hezbollah", "CNN"]
)

ratio_ampliat = (
    resum.loc["Israel", "Ampliat"]
    / resum.loc["Hezbollah", "Ampliat"]
)

print("\nRÀTIO ISRAEL / HEZBOLLAH")
print("CNN:", round(ratio_cnn, 2))
print("Ampliat:", round(ratio_ampliat, 2))


# ============================================================
# 10. PREPROCESSAMENT 3:
# AGREGACIÓ TEMPORAL I COMPLETAT DE DIES SENSE ESDEVENIMENTS
# ============================================================

# Comptem esdeveniments per dia i actor dins de l'abast CNN
serie_cnn = (
    df_cnn
    .groupby(["event_date", "actor_origin"])
    .size()
    .reset_index(name="events")
)

serie_cnn["scope"] = "CNN"


# Comptem esdeveniments per dia i actor dins de l'abast ampliat
serie_ampliada = (
    df_ampliat
    .groupby(["event_date", "actor_origin"])
    .size()
    .reset_index(name="events")
)

serie_ampliada["scope"] = "Ampliat"


# Unim les dues sèries
serie = pd.concat(
    [serie_cnn, serie_ampliada],
    ignore_index=True
)


# ============================================================
# CREAR TOTES LES COMBINACIONS:
# dia × actor × scope
# ============================================================

dates = pd.date_range(
    start="2023-10-08",
    end="2026-09-07",
    freq="D"
)

actors = ["Israel", "Hezbollah"]
scopes = ["CNN", "Ampliat"]

index_complet = pd.MultiIndex.from_product(
    [dates, actors, scopes],
    names=["event_date", "actor_origin", "scope"]
)

serie_completa = (
    serie
    .set_index(["event_date", "actor_origin", "scope"])
    .reindex(index_complet, fill_value=0)
    .reset_index()
)


print("\nMOSTRA DE LA SÈRIE TEMPORAL COMPLETA:")
print(serie_completa.head(20))


print("\nNOMBRE DE FILES DE LA SÈRIE:")
print(len(serie_completa))

print("\nTOTALS DESPRÉS DE L'AGREGACIÓ:")
print(
    serie_completa
    .groupby(["scope", "actor_origin"])["events"]
    .sum()
)


print("\nPICS DIARIS - CNN:")

for actor in actors:

    dades_actor = serie_completa[
        (serie_completa["scope"] == "CNN")
        & (serie_completa["actor_origin"] == actor)
    ]

    fila_max = dades_actor.loc[
        dades_actor["events"].idxmax()
    ]

    print(
        actor,
        fila_max["event_date"].date(),
        fila_max["events"]
    )


# ============================================================
# 11. GUARDAR DATASET DERIVAT
# ============================================================

output_path = (
    Path(__file__).resolve().parents[1]
    / "output"
    / "dades_filtrades.csv"
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)

serie_completa.to_csv(
    output_path,
    index=False
)

print(
    "\nDataset derivat guardat a:",
    output_path
)