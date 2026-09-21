import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path


# ============================================================
# CONFIGURACIÓ DE L'APLICACIÓ
# ============================================================

st.set_page_config(
    page_title="Israel - Hezbollah: anàlisi d'esdeveniments",
    layout="wide"
)

st.title("Israel – Hezbollah: esdeveniments registrats per ACLED")

st.caption(
    "Comparació entre l'abast geogràfic utilitzat per CNN "
    "i una versió ampliada que incorpora també Síria."
)


# ============================================================
# 1. CARREGAR EL DATASET PREPROCESSAT
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
# 2. CONTROLS INTERACTIUS
# ============================================================

st.sidebar.header("Controls")

scope_seleccionat = st.sidebar.radio(
    "Àmbit geogràfic",
    options=["CNN", "Ampliat"],
    format_func=lambda x:
        "CNN: Israel + Líban"
        if x == "CNN"
        else "Ampliat: Israel + Líban + Síria"
)

actors_seleccionats = st.sidebar.multiselect(
    "Actors",
    options=["Israel", "Hezbollah"],
    default=["Israel", "Hezbollah"]
)

granularitat = st.sidebar.radio(
    "Granularitat temporal",
    options=["Diària", "Setmanal"],
    index=0
)


# ============================================================
# 3. FILTRAR SEGONS L'ABAST I ELS ACTORS
# ============================================================

df_visual = df[
    (df["scope"] == scope_seleccionat)
    & (df["actor_origin"].isin(actors_seleccionats))
].copy()


if len(actors_seleccionats) == 0:
    st.warning("Selecciona almenys un actor per mostrar la visualització.")
    st.stop()


# ============================================================
# 4. RECONFIGURAR LA GRANULARITAT TEMPORAL
# ============================================================

if granularitat == "Setmanal":

    df_visual["week"] = (
        df_visual["event_date"]
        .dt.to_period("W")
        .apply(lambda r: r.start_time)
    )

    df_visual = (
        df_visual
        .groupby(
            ["week", "actor_origin"],
            as_index=False
        )["events"]
        .sum()
    )

    df_visual = df_visual.rename(
        columns={"week": "date"}
    )

else:

    df_visual = df_visual.rename(
        columns={"event_date": "date"}
    )


# ============================================================
# 5. INDICADORS RESUM
# ============================================================

totals_scope = (
    df[
        df["scope"] == scope_seleccionat
    ]
    .groupby("actor_origin")["events"]
    .sum()
)


# Totals de la versió CNN per calcular diferències
totals_cnn = (
    df[
        df["scope"] == "CNN"
    ]
    .groupby("actor_origin")["events"]
    .sum()
)


col1, col2 = st.columns(2)

total_israel = totals_scope.get("Israel", 0)
total_hezbollah = totals_scope.get("Hezbollah", 0)

if scope_seleccionat == "Ampliat":

    increment_israel = (
        (total_israel - totals_cnn["Israel"])
        / totals_cnn["Israel"]
        * 100
    )

    increment_hezbollah = (
        (total_hezbollah - totals_cnn["Hezbollah"])
        / totals_cnn["Hezbollah"]
        * 100
    )

    col1.metric(
        "Israel",
        f"{int(total_israel):,}".replace(",", "."),
        f"+{increment_israel:.2f}% respecte CNN"
    )

    col2.metric(
        "Hezbollah",
        f"{int(total_hezbollah):,}".replace(",", "."),
        f"+{increment_hezbollah:.2f}% respecte CNN"
    )

else:

    col1.metric(
        "Israel",
        f"{int(total_israel):,}".replace(",", ".")
    )

    col2.metric(
        "Hezbollah",
        f"{int(total_hezbollah):,}".replace(",", ".")
    )


# ============================================================
# 6. VISUALITZACIÓ
# ============================================================

fig = px.line(
    df_visual,
    x="date",
    y="events",
    color="actor_origin",
    labels={
        "date": "Data",
        "events": "Nombre d'esdeveniments",
        "actor_origin": "Actor"
    },
    hover_data={
        "date": "|%d/%m/%Y",
        "events": True,
        "actor_origin": True
    }
)

fig.update_layout(
    title=(
        "Evolució temporal dels esdeveniments "
        f"— abast {scope_seleccionat}"
    ),
    xaxis_title="Data",
    yaxis_title="Nombre d'esdeveniments",
    legend_title="Actor",
    hovermode="x unified"
)

fig.update_yaxes(
    rangemode="tozero"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# 7. EXPLICACIÓ METODOLÒGICA
# ============================================================

if scope_seleccionat == "CNN":

    st.info(
        "Aquest abast només inclou esdeveniments registrats "
        "a Israel i el Líban, reproduint el criteri geogràfic "
        "de la visualització analitzada."
    )

else:

    st.info(
        "Aquest abast manté els mateixos actors, període temporal "
        "i tipus d'esdeveniment, però incorpora també els "
        "esdeveniments registrats a Síria."
    )