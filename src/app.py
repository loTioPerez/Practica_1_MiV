import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path


# ============================================================
# 1. CONFIGURACIÓ DE LA PÀGINA
# ============================================================

st.set_page_config(
    page_title="Israel - Hezbollah",
    layout="wide"
)

st.title("Israel – Hezbollah: evolució dels esdeveniments")

st.caption(
    "Dades ACLED. Abast geogràfic ampliat: "
    "Israel, Líban i Síria."
)


# ============================================================
# 2. CARREGAR LES DADES PREPROCESSADES
# ============================================================

csv_path = (
    Path(__file__).resolve().parents[1]
    / "output"
    / "dades_filtrades.csv"
)

df = pd.read_csv(
    csv_path,
    parse_dates=["event_date"]
)


# ============================================================
# 3. UTILITZAR NOMÉS L'ABAST AMPLIAT
# ============================================================

df = df[
    df["scope"] == "Ampliat"
].copy()


# ============================================================
# 4. CONTROLS INTERACTIUS
# ============================================================

st.sidebar.header("Filtres")

actors_seleccionats = st.sidebar.multiselect(
    "Actors",
    options=["Israel", "Hezbollah"],
    default=["Israel", "Hezbollah"]
)

granularitat = st.sidebar.radio(
    "Granularitat temporal",
    options=["Diària", "Setmanal"],
    index=1
)


# Si l'usuari elimina tots els actors, aturem el programa
if not actors_seleccionats:
    st.warning("Selecciona almenys un actor.")
    st.stop()


# ============================================================
# 5. FILTRAR ELS ACTORS
# ============================================================

df_visual = df[
    df["actor_origin"].isin(actors_seleccionats)
].copy()


# ============================================================
# 6. AGREGACIÓ TEMPORAL
# ============================================================

if granularitat == "Setmanal":

    # Convertim cada data en l'inici de la seva setmana
    df_visual["date"] = (
        df_visual["event_date"]
        .dt.to_period("W")
        .dt.start_time
    )

    # Sumem tots els esdeveniments de cada setmana
    df_visual = (
        df_visual
        .groupby(
            ["date", "actor_origin"],
            as_index=False
        )["events"]
        .sum()
    )

else:

    # En mode diari només canviem el nom de la columna
    df_visual = df_visual.rename(
        columns={"event_date": "date"}
    )


# ============================================================
# 7. CREAR EL GRÀFIC
# ============================================================

fig = px.line(
    df_visual,
    x="date",
    y="events",
    color="actor_origin",
    labels={
        "date": "Data",
        "events": "Nombre d'esdeveniments registrats",
        "actor_origin": "Actor"
    }
)


# ============================================================
# 8. CONFIGURAR EL GRÀFIC
# ============================================================

fig.update_layout(
    title="Esdeveniments registrats per ACLED",
    xaxis_title="Data",
    yaxis_title="Nombre d'esdeveniments registrats",
    legend_title="Actor",
    hovermode="x unified"
)

# L'eix vertical ha de començar a zero
fig.update_yaxes(
    rangemode="tozero"
)


# ============================================================
# 9. MOSTRAR EL GRÀFIC
# ============================================================

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 10. INFORMACIÓ SOBRE LA VISUALITZACIÓ
# ============================================================

st.caption(
    "La visualització inclou atacs aeris o amb drons i "
    "bombardejos, artilleria o atacs amb míssils registrats "
    "per ACLED entre el 8 d'octubre de 2023 i el 7 de setembre "
    "de 2026."
)