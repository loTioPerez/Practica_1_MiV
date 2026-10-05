import pandas as pd
from pathlib import Path


# ============================================================
# 1. CONFIGURACIÓ
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = BASE_DIR / "data" / "acled_raw.csv"

OUTPUT_TEMPORAL = (
    BASE_DIR / "output" / "dades_filtrades.csv"
)

OUTPUT_VISUALITZACIO = (
    BASE_DIR / "output" / "dades_visualitzacio.csv"
)


DATA_INICI = pd.Timestamp("2023-10-08")


TIPUS_CNN = [
    "Air/drone strike",
    "Shelling/artillery/missile attack"
]


MAPA_ACTORS = {
    "Military Forces of Israel (2022-)": "Israel",
    "Hezbollah": "Hezbollah"
}


PAISOS_CNN = [
    "Israel",
    "Lebanon"
]


# Admetem les dues denominacions per evitar
# problemes segons la versió del fitxer d'ACLED.
PAISOS_AMPLIATS = [
    "Israel",
    "Lebanon",
    "Syria",
    "Syrian Arab Republic"
]


# ============================================================
# 2. CARREGAR I PREPARAR LES DADES COMUNES
# ============================================================

def carregar_dades():

    df = pd.read_csv(
        INPUT_PATH,
        low_memory=False
    )

    df["event_date"] = pd.to_datetime(
        df["event_date"],
        errors="coerce"
    )

    return df


def preparar_dades(df):

    # --------------------------------------------------------
    # Filtre temporal
    # --------------------------------------------------------

    df = df[
        df["event_date"] >= DATA_INICI
    ].copy()


    # --------------------------------------------------------
    # Mateixos tipus d'esdeveniment utilitzats
    # en la reconstrucció de CNN
    # --------------------------------------------------------

    df = df[
        df["sub_event_type"].isin(
            TIPUS_CNN
        )
    ].copy()


    # --------------------------------------------------------
    # Només els dos actors que volem comparar
    # --------------------------------------------------------

    df = df[
        df["actor1"].isin(
            MAPA_ACTORS.keys()
        )
    ].copy()


    # --------------------------------------------------------
    # Normalització dels noms dels actors
    # --------------------------------------------------------

    df["actor_origin"] = (
        df["actor1"]
        .map(MAPA_ACTORS)
    )


    # --------------------------------------------------------
    # Classificació geogràfica
    # --------------------------------------------------------

    df["zona_operativa"] = df.apply(
        classificar_zona,
        axis=1
    )

    return df


# ============================================================
# 3. CLASSIFICACIÓ GEOGRÀFICA
# ============================================================

def classificar_zona(row):

    country = row["country"]
    admin1 = row["admin1"]

    if country == "Israel":
        return "Israel"

    if country == "Lebanon":
        return "Lebanon"

    if (
        country in ["Syria", "Syrian Arab Republic"]
        and admin1 == "Quneitra"
    ):
        return "Quneitra/Golan"

    if country in ["Syria", "Syrian Arab Republic"]:
        return "Syria-other"

    return "Other"


# ============================================================
# 4. DATASET TEMPORAL ANTIC
# ============================================================

def crear_dataset_temporal(df):

    # --------------------------------------------------------
    # Abast equivalent al de CNN
    # --------------------------------------------------------

    df_cnn = df[
        df["country"].isin(
            PAISOS_CNN
        )
    ].copy()


    # --------------------------------------------------------
    # Abast ampliat:
    # Israel + Líban + Síria
    # --------------------------------------------------------

    df_ampliat = df[
        df["country"].isin(
            PAISOS_AMPLIATS
        )
    ].copy()


    # --------------------------------------------------------
    # Agregació diària
    # --------------------------------------------------------

    def agregar_per_dia(
        dataframe,
        scope
    ):

        resultat = (
            dataframe
            .groupby(
                [
                    "event_date",
                    "actor_origin"
                ],
                as_index=False
            )
            .size()
            .rename(
                columns={
                    "size": "events"
                }
            )
        )

        resultat["scope"] = scope

        return resultat


    df_cnn_diari = agregar_per_dia(
        df_cnn,
        "CNN"
    )

    df_ampliat_diari = agregar_per_dia(
        df_ampliat,
        "Ampliat"
    )


    df_temporal = pd.concat(
        [
            df_cnn_diari,
            df_ampliat_diari
        ],
        ignore_index=True
    )


    # --------------------------------------------------------
    # Completar dies sense esdeveniments
    # --------------------------------------------------------

    data_fi = df_ampliat[
        "event_date"
    ].max()


    dates = pd.date_range(
        start=DATA_INICI,
        end=data_fi,
        freq="D"
    )


    index_complet = pd.MultiIndex.from_product(
        [
            dates,
            ["Israel", "Hezbollah"],
            ["CNN", "Ampliat"]
        ],
        names=[
            "event_date",
            "actor_origin",
            "scope"
        ]
    )


    df_temporal = (
        df_temporal
        .set_index(
            [
                "event_date",
                "actor_origin",
                "scope"
            ]
        )
        .reindex(
            index_complet,
            fill_value=0
        )
        .reset_index()
    )


    df_temporal.to_csv(
        OUTPUT_TEMPORAL,
        index=False
    )


    return df_temporal, df_cnn, df_ampliat


# ============================================================
# 5. NOU DATASET ESPACIOTEMPORAL
# ============================================================

def crear_dataset_visualitzacio(df):

    # El mapa final treballarà únicament
    # amb l'abast ampliat.

    df_mapa = df[
        df["country"].isin(
            PAISOS_AMPLIATS
        )
    ].copy()


    # --------------------------------------------------------
    # Crear la dimensió temporal mensual
    # --------------------------------------------------------

    df_mapa["month"] = (
        df_mapa["event_date"]
        .dt.to_period("M")
        .astype(str)
    )


    # --------------------------------------------------------
    # Comprovar coordenades
    # --------------------------------------------------------

    sense_coordenades = df_mapa[
        df_mapa["latitude"].isna()
        | df_mapa["longitude"].isna()
    ]


    # Els esdeveniments sense coordenades no es poden
    # representar espacialment al mapa.

    df_mapa = df_mapa[
        df_mapa["latitude"].notna()
        & df_mapa["longitude"].notna()
    ].copy()


    # --------------------------------------------------------
    # Evitar que valors buits facin desaparèixer files
    # durant el groupby
    # --------------------------------------------------------

    df_mapa["admin1"] = (
        df_mapa["admin1"]
        .fillna("Desconegut")
    )

    df_mapa["location"] = (
        df_mapa["location"]
        .fillna("Desconeguda")
    )


    # --------------------------------------------------------
    # Agregació:
    #
    # una fila = un actor en una localització
    # durant un mes concret
    # --------------------------------------------------------

    df_visualitzacio = (
        df_mapa
        .groupby(
            [
                "month",
                "actor_origin",
                "zona_operativa",
                "country",
                "admin1",
                "location",
                "latitude",
                "longitude"
            ],
            as_index=False
        )
        .size()
        .rename(
            columns={
                "size": "events"
            }
        )
    )


    # Ordre cronològic per facilitar
    # l'animació posterior.

    df_visualitzacio = (
        df_visualitzacio
        .sort_values(
            [
                "month",
                "actor_origin",
                "zona_operativa",
                "location"
            ]
        )
        .reset_index(drop=True)
    )


    df_visualitzacio.to_csv(
        OUTPUT_VISUALITZACIO,
        index=False
    )


    return (
        df_visualitzacio,
        sense_coordenades
    )


# ============================================================
# 6. COMPROVACIONS
# ============================================================

def mostrar_comprovacions(
    df_temporal,
    df_cnn,
    df_ampliat,
    df_visualitzacio,
    sense_coordenades
):

    print()
    print("========================================")
    print("COMPROVACIÓ DEL PREPROCESSAMENT")
    print("========================================")


    # --------------------------------------------------------
    # Període
    # --------------------------------------------------------

    print()
    print(
        "Període disponible:",
        df_ampliat["event_date"].min().date(),
        "→",
        df_ampliat["event_date"].max().date()
    )


    # --------------------------------------------------------
    # Totals CNN
    # --------------------------------------------------------

    totals_cnn = (
        df_cnn
        .groupby("actor_origin")
        .size()
    )

    print()
    print("Abast CNN:")
    print(totals_cnn)


    # --------------------------------------------------------
    # Totals ampliats
    # --------------------------------------------------------

    totals_ampliats = (
        df_ampliat
        .groupby("actor_origin")
        .size()
    )

    print()
    print("Abast ampliat:")
    print(totals_ampliats)


    # --------------------------------------------------------
    # Ràtio
    # --------------------------------------------------------

    israel = totals_ampliats.get(
        "Israel",
        0
    )

    hezbollah = totals_ampliats.get(
        "Hezbollah",
        0
    )

    if hezbollah > 0:

        ratio = israel / hezbollah

        print()
        print(
            "Ràtio Israel / Hezbollah:",
            round(ratio, 2)
        )


    # --------------------------------------------------------
    # Comprovació del dataset geogràfic
    # --------------------------------------------------------

    total_mapa = (
        df_visualitzacio[
            "events"
        ].sum()
    )

    total_ampliat = len(
        df_ampliat
    )


    print()
    print(
        "Esdeveniments abast ampliat:",
        total_ampliat
    )

    print(
        "Esdeveniments representables al mapa:",
        total_mapa
    )

    print(
        "Esdeveniments sense coordenades:",
        len(sense_coordenades)
    )


    # --------------------------------------------------------
    # Mesos disponibles
    # --------------------------------------------------------

    print()
    print(
        "Nombre de mesos:",
        df_visualitzacio[
            "month"
        ].nunique()
    )


    # --------------------------------------------------------
    # Validació de Quneitra/Golan
    # --------------------------------------------------------

    quneitra = df_visualitzacio[
        (
            df_visualitzacio[
                "zona_operativa"
            ] == "Quneitra/Golan"
        )
        &
        (
            df_visualitzacio[
                "actor_origin"
            ] == "Hezbollah"
        )
    ]


    print()
    print(
        "Hezbollah a Quneitra/Golan:",
        quneitra["events"].sum()
    )


    print()
    print(
        f"Generat: {OUTPUT_TEMPORAL.name}"
    )

    print(
        f"Generat: {OUTPUT_VISUALITZACIO.name}"
    )

    print("========================================")
    print()


# ============================================================
# 7. EXECUCIÓ
# ============================================================

def main():

    # 1. Dataset original
    df = carregar_dades()


    # 2. Preprocessament comú
    df = preparar_dades(df)


    # 3. Sortida del dashboard actual
    (
        df_temporal,
        df_cnn,
        df_ampliat
    ) = crear_dataset_temporal(df)


    # 4. Nova sortida per al mapa
    (
        df_visualitzacio,
        sense_coordenades
    ) = crear_dataset_visualitzacio(df)


    # 5. Validacions
    mostrar_comprovacions(
        df_temporal,
        df_cnn,
        df_ampliat,
        df_visualitzacio,
        sense_coordenades
    )


if __name__ == "__main__":
    main()