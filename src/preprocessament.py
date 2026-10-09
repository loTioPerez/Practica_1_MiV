from pathlib import Path

import pandas as pd


# ============================================================
# 1. CONFIGURACIÓ DE RUTES I CONSTANTS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = BASE_DIR / "data" / "acled_raw.csv"
OUTPUT_PATH = BASE_DIR / "output" / "dades_visualitzacio.csv"

DATA_INICI = pd.Timestamp("2023-10-08")

TIPUS_ESDEVENIMENT = [
    "Air/drone strike",
    "Shelling/artillery/missile attack"
]

MAPA_ACTORS = {
    "Military Forces of Israel (2022-)": "Israel",
    "Hezbollah": "Hezbollah"
}

PAISOS = [
    "Israel",
    "Lebanon",
    "Syria",
    "Syrian Arab Republic"
]


# ============================================================
# 2. CARREGAR LES DADES ORIGINALS
# ============================================================

def carregar_dades():
    """Carrega el CSV original d'ACLED i converteix la data."""

    df = pd.read_csv(INPUT_PATH, low_memory=False)
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")

    return df


# ============================================================
# 3. CLASSIFICACIÓ GEOGRÀFICA
# ============================================================

def classificar_zona(row):
    """Classifica cada esdeveniment segons la seva zona geogràfica."""

    country = row["country"]
    admin1 = row["admin1"]

    if country == "Israel":
        return "Israel"

    if country == "Lebanon":
        return "Lebanon"

    if country in ["Syria", "Syrian Arab Republic"] and admin1 == "Quneitra":
        return "Quneitra/Golan"

    if country in ["Syria", "Syrian Arab Republic"]:
        return "Syria-other"

    return "Other"


# ============================================================
# 4. PREPROCESSAMENT
# ============================================================

def preprocessar_dades(df):
    """Aplica els filtres i transformacions necessaris."""

    # --------------------------------------------------------
    # 4.1. FILTRE TEMPORAL
    # --------------------------------------------------------

    df = df[df["event_date"] >= DATA_INICI].copy()


    # --------------------------------------------------------
    # 4.2. SELECCIÓ DELS TIPUS D'ESDEVENIMENT
    # --------------------------------------------------------

    # Conservem els mateixos tipus utilitzats en la
    # reconstrucció de la visualització de CNN.

    df = df[df["sub_event_type"].isin(TIPUS_ESDEVENIMENT)].copy()


    # --------------------------------------------------------
    # 4.3. SELECCIÓ DELS ACTORS
    # --------------------------------------------------------

    # La coincidència exacta evita incloure altres actors
    # que continguin paraules similars al seu nom.

    df = df[df["actor1"].isin(MAPA_ACTORS.keys())].copy()


    # --------------------------------------------------------
    # 4.4. SELECCIÓ GEOGRÀFICA
    # --------------------------------------------------------

    # El redisseny amplia l'àmbit a Israel, Líban i Síria.

    df = df[df["country"].isin(PAISOS)].copy()


    # --------------------------------------------------------
    # 4.5. NORMALITZACIÓ DELS ACTORS
    # --------------------------------------------------------

    # Simplifiquem els noms originals d'ACLED
    # per utilitzar etiquetes homogènies al dashboard.

    df["actor_origin"] = df["actor1"].map(MAPA_ACTORS)


    # --------------------------------------------------------
    # 4.6. RECLASSIFICACIÓ GEOGRÀFICA
    # --------------------------------------------------------

    # Creem una variable pròpia que diferencia Israel,
    # Líban, Quneitra/Golan i la resta de Síria.

    df["zona_operativa"] = df.apply(classificar_zona, axis=1)


    # --------------------------------------------------------
    # 4.7. COORDENADES
    # --------------------------------------------------------

    # Els esdeveniments sense coordenades no es poden
    # representar al mapa.

    df = df.dropna(subset=["latitude", "longitude"]).copy()


    # --------------------------------------------------------
    # 4.8. TRACTAMENT DE VALORS BUITS
    # --------------------------------------------------------

    # Evitem perdre registres durant l'agregació.

    df["admin1"] = df["admin1"].fillna("Desconegut")
    df["location"] = df["location"].fillna("Desconeguda")


    # --------------------------------------------------------
    # 4.9. DIMENSIÓ TEMPORAL
    # --------------------------------------------------------

    # Convertim cada data en un període mensual perquè
    # cada frame de l'animació representi un mes.

    df["month"] = df["event_date"].dt.to_period("M").astype(str)

    return df


# ============================================================
# 5. AGREGACIÓ ESPACIOTEMPORAL
# ============================================================

def agregar_dades(df):
    """
    Agrupa els esdeveniments per mes, actor i localització.

    Cada fila del dataset final representa el nombre
    d'esdeveniments d'un actor en una localització i mes.
    """

    columnes_agrupacio = [
        "month",
        "actor_origin",
        "zona_operativa",
        "country",
        "admin1",
        "location",
        "latitude",
        "longitude"
    ]

    df_visualitzacio = (
        df.groupby(columnes_agrupacio, as_index=False)
        .size()
        .rename(columns={"size": "events"})
    )

    df_visualitzacio = (
        df_visualitzacio
        .sort_values(["month", "actor_origin", "zona_operativa", "location"])
        .reset_index(drop=True)
    )

    return df_visualitzacio


# ============================================================
# 6. COMPROVACIONS DEL RESULTAT
# ============================================================

def mostrar_comprovacions(df_original, df_preprocessat, df_visualitzacio):
    """Mostra al terminal comprovacions bàsiques del preprocessament."""

    totals = df_preprocessat.groupby("actor_origin").size()

    israel = totals.get("Israel", 0)
    hezbollah = totals.get("Hezbollah", 0)

    print()
    print("========================================")
    print("COMPROVACIÓ DEL PREPROCESSAMENT")
    print("========================================")

    print()
    print("Files originals:", len(df_original))

    print()
    print(
        "Període:",
        df_preprocessat["event_date"].min().date(),
        "→",
        df_preprocessat["event_date"].max().date()
    )

    print()
    print("Totals:")
    print(totals)

    if hezbollah > 0:
        print()
        print("Ràtio Israel / Hezbollah:", round(israel / hezbollah, 2))

    print()
    print("Mesos:", df_visualitzacio["month"].nunique())

    print()
    print("Files del dataset final:", len(df_visualitzacio))

    print()
    print(
        "Total d'esdeveniments representats:",
        df_visualitzacio["events"].sum()
    )


    # --------------------------------------------------------
    # Validació específica de Quneitra/Golan
    # --------------------------------------------------------

    quneitra = df_visualitzacio[
        (df_visualitzacio["zona_operativa"] == "Quneitra/Golan")
        & (df_visualitzacio["actor_origin"] == "Hezbollah")
    ]

    print()
    print("Hezbollah a Quneitra/Golan:", quneitra["events"].sum())

    print()
    print("Fitxer generat:", OUTPUT_PATH)

    print("========================================")
    print()


# ============================================================
# 7. EXECUCIÓ PRINCIPAL
# ============================================================

def main():

    # 1. Carregar el dataset original.
    df_original = carregar_dades()

    # 2. Aplicar filtres i transformacions.
    df_preprocessat = preprocessar_dades(df_original)

    # 3. Crear el dataset agregat que utilitzarà el mapa.
    df_visualitzacio = agregar_dades(df_preprocessat)

    # 4. Crear la carpeta output si no existeix.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 5. Exportar el dataset final.
    df_visualitzacio.to_csv(OUTPUT_PATH, index=False)

    # 6. Mostrar comprovacions al terminal.
    mostrar_comprovacions(
        df_original,
        df_preprocessat,
        df_visualitzacio
    )


if __name__ == "__main__":
    main()