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

# El CSV conserva tant la reconstrucció de CNN
# com l'abast ampliat.
#
# Per al redisseny final només utilitzem:
# Israel + Líban + Síria.

df = df[
    df["scope"] == "Ampliat"
].copy()


# ============================================================
# 4. VALORS INICIALS DELS FILTRES
# ============================================================

# session_state permet que Streamlit recordi els valors
# seleccionats entre una actualització i la següent.

if "actors" not in st.session_state:
    st.session_state["actors"] = [
        "Israel",
        "Hezbollah"
    ]

if "granularitat" not in st.session_state:
    st.session_state["granularitat"] = "Setmanal"


# ============================================================
# 5. CONTROLS INTERACTIUS
# ============================================================

st.sidebar.header("Filtres")


# ------------------------------------------------------------
# Botó per tornar als valors inicials
# ------------------------------------------------------------

# El botó es processa abans de crear els widgets.
# Així podem modificar session_state sense conflictes.

if st.sidebar.button("Restablir filtres"):

    st.session_state["actors"] = [
        "Israel",
        "Hezbollah"
    ]

    st.session_state["granularitat"] = "Setmanal"


# ------------------------------------------------------------
# Selecció d'actors
# ------------------------------------------------------------

actors_seleccionats = st.sidebar.multiselect(
    "Actors",
    options=[
        "Israel",
        "Hezbollah"
    ],
    key="actors"
)


# ------------------------------------------------------------
# Selecció de granularitat temporal
# ------------------------------------------------------------

granularitat = st.sidebar.radio(
    "Granularitat temporal",
    options=[
        "Diària",
        "Setmanal"
    ],
    key="granularitat"
)


# Si l'usuari elimina tots els actors,
# evitem mostrar una visualització sense dades.

if not actors_seleccionats:

    st.warning(
        "Selecciona almenys un actor."
    )

    st.stop()


# ============================================================
# 6. FILTRAR ELS ACTORS
# ============================================================

# isin() comprova si actor_origin es troba
# dins de la llista seleccionada per l'usuari.

df_filtrat = df[
    df["actor_origin"].isin(
        actors_seleccionats
    )
].copy()


# ============================================================
# 7. CALCULAR ELS KPIs
# ============================================================

# Calculem els totals abans de l'agregació setmanal.
# Això evita que la granularitat temporal modifiqui
# els totals reals.

totals = (
    df_filtrat
    .groupby("actor_origin")["events"]
    .sum()
)


# get() retorna 0 si aquell actor
# no està seleccionat.

total_israel = totals.get(
    "Israel",
    0
)

total_hezbollah = totals.get(
    "Hezbollah",
    0
)

total_general = (
    total_israel
    + total_hezbollah
)


# ------------------------------------------------------------
# Variable derivada
# ------------------------------------------------------------

# Calculem el percentatge dels esdeveniments visibles
# corresponents a Hezbollah.

if total_general > 0:

    percentatge_hezbollah = (
        total_hezbollah
        / total_general
        * 100
    )

else:

    percentatge_hezbollah = 0


# ============================================================
# 8. MOSTRAR ELS KPIs
# ============================================================

col1, col2, col3 = st.columns(3)


col1.metric(
    "Esdeveniments Israel",
    f"{int(total_israel):,}".replace(
        ",",
        "."
    )
)


col2.metric(
    "Esdeveniments Hezbollah",
    f"{int(total_hezbollah):,}".replace(
        ",",
        "."
    )
)


col3.metric(
    "% Hezbollah sobre el total",
    f"{percentatge_hezbollah:.1f}%"
)


# ============================================================
# 9. PREPARAR LA SÈRIE TEMPORAL
# ============================================================

df_visual = df_filtrat.copy()


if granularitat == "Setmanal":

    # Convertim cada dia en l'inici
    # de la setmana a la qual pertany.

    df_visual["date"] = (
        df_visual["event_date"]
        .dt.to_period("W")
        .dt.start_time
    )

    # Agrupem les files de la mateixa setmana
    # i del mateix actor i sumem els esdeveniments.

    df_visual = (
        df_visual
        .groupby(
            [
                "date",
                "actor_origin"
            ],
            as_index=False
        )["events"]
        .sum()
    )


else:

    # En mode diari no cal tornar a agregar.
    # Només canviem el nom de la columna
    # perquè Plotly utilitzi sempre "date".

    df_visual = df_visual.rename(
        columns={
            "event_date": "date"
        }
    )


# ============================================================
# 10. COLORS I ESTILS DELS ACTORS
# ============================================================

# Utilitzem una combinació blau/taronja
# amb bon contrast i adequada per a persones
# amb diferents tipus de visió cromàtica.

colors = {
    "Israel": "#0072B2",
    "Hezbollah": "#D55E00"
}


# Els actors també es diferencien pel patró
# de la línia. Així la identificació
# no depèn exclusivament del color.

estils_linia = {
    "Israel": "solid",
    "Hezbollah": "dash"
}


# ============================================================
# 11. CREAR EL GRÀFIC TEMPORAL
# ============================================================

fig_linia = px.line(
    df_visual,
    x="date",
    y="events",
    color="actor_origin",
    line_dash="actor_origin",

    color_discrete_map=colors,
    line_dash_map=estils_linia,

    labels={
        "date": "Data",
        "events":
            "Nombre d'esdeveniments registrats",
        "actor_origin": "Actor"
    }
)


# ============================================================
# 12. CONFIGURAR EL GRÀFIC TEMPORAL
# ============================================================

fig_linia.update_layout(

    title="Evolució temporal dels esdeveniments",

    xaxis_title="Data",

    yaxis_title=(
        "Nombre d'esdeveniments registrats"
    ),

    legend_title="Actor",

    # Mostra els valors dels actors
    # corresponents a una mateixa data.
    hovermode="x unified"
)


# L'eix Y representa valors absoluts,
# per tant ha de començar a 0.

fig_linia.update_yaxes(
    rangemode="tozero",

    # Retícula lleugera per facilitar la lectura
    # sense afegir massa soroll visual.
    showgrid=True,
    gridwidth=0.5
)


# Eliminem la retícula vertical,
# ja que no és necessària.

fig_linia.update_xaxes(
    showgrid=False
)


# ============================================================
# 13. MOSTRAR EL GRÀFIC TEMPORAL
# ============================================================

st.plotly_chart(
    fig_linia,
    use_container_width=True
)


# ============================================================
# 14. PREPARAR EL GRÀFIC RESUM
# ============================================================

# El gràfic de barres utilitza exactament
# el mateix subconjunt filtrat.
#
# Per tant, quan canvia la selecció d'actors,
# també s'actualitza aquesta visualització.

df_totals = (
    df_filtrat
    .groupby(
        "actor_origin",
        as_index=False
    )["events"]
    .sum()
)


# ============================================================
# 15. CREAR EL GRÀFIC DE BARRES
# ============================================================

fig_barres = px.bar(
    df_totals,

    x="actor_origin",
    y="events",

    color="actor_origin",
    color_discrete_map=colors,

    labels={
        "actor_origin": "Actor",
        "events":
            "Nombre total d'esdeveniments"
    }
)


# ============================================================
# 16. CONFIGURAR EL GRÀFIC DE BARRES
# ============================================================

fig_barres.update_layout(

    title="Total d'esdeveniments per actor",

    xaxis_title="Actor",

    yaxis_title=(
        "Nombre total d'esdeveniments"
    ),

    # El color ja queda identificat
    # directament per cada barra.
    showlegend=False
)


# Com que les barres representen
# magnituds absolutes, l'eix Y també
# ha de començar necessàriament a 0.

fig_barres.update_yaxes(
    rangemode="tozero",
    showgrid=True,
    gridwidth=0.5
)

fig_barres.update_xaxes(
    showgrid=False
)


# ============================================================
# 17. MOSTRAR EL GRÀFIC RESUM
# ============================================================

st.plotly_chart(
    fig_barres,
    use_container_width=True
)


# ============================================================
# 18. INFORMACIÓ SOBRE LA VISUALITZACIÓ
# ============================================================

st.caption(
    "La visualització inclou atacs aeris o amb drons i "
    "bombardejos, artilleria o atacs amb míssils registrats "
    "per ACLED entre el 8 d'octubre de 2023 i el 7 de setembre "
    "de 2026."
)