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


# Aquesta variable ens permet reiniciar també
# la selecció interactiva del gràfic de barres.

if "barres_version" not in st.session_state:
    st.session_state["barres_version"] = 0


# ============================================================
# 5. CONTROLS INTERACTIUS
# ============================================================

st.sidebar.header("Filtres")


# ------------------------------------------------------------
# Botó per tornar als valors inicials
# ------------------------------------------------------------

if st.sidebar.button("Restablir filtres"):

    st.session_state["actors"] = [
        "Israel",
        "Hezbollah"
    ]

    st.session_state["granularitat"] = "Setmanal"

    # Canviem la clau del gràfic de barres.
    # Això elimina una possible selecció anterior.
    st.session_state["barres_version"] += 1


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


# ------------------------------------------------------------
# Variable derivada:
# ràtio Israel / Hezbollah
# ------------------------------------------------------------

# Indica quants esdeveniments atribuïts a Israel
# hi ha per cada esdeveniment atribuït a Hezbollah.
#
# Només es calcula quan els dos actors
# estan seleccionats.

if total_israel > 0 and total_hezbollah > 0:

    ratio_israel_hezbollah = (
        total_israel
        / total_hezbollah
    )

    text_ratio = (
        f"{ratio_israel_hezbollah:.2f}×"
    )

else:

    text_ratio = "—"


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
    "Ràtio Israel / Hezbollah",
    text_ratio,
    help=(
        "Nombre d'esdeveniments atribuïts a Israel "
        "per cada esdeveniment atribuït a Hezbollah."
    )
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

# Blau i taronja amb bon contrast.
#
# Els actors també utilitzen patrons de línia diferents,
# de manera que la identificació no depèn només del color.

colors = {
    "Israel": "#0072B2",
    "Hezbollah": "#D55E00"
}


estils_linia = {
    "Israel": "solid",
    "Hezbollah": "dash"
}


# ============================================================
# 11. PREPARAR EL GRÀFIC DE BARRES
# ============================================================

# Aquest gràfic utilitza el mateix subconjunt
# seleccionat amb els filtres globals.

df_totals = (
    df_filtrat
    .groupby(
        "actor_origin",
        as_index=False
    )["events"]
    .sum()
)


# Mantenim sempre el mateix ordre visual.

ordre_actors = [
    "Israel",
    "Hezbollah"
]


# ============================================================
# 12. CREAR EL GRÀFIC DE BARRES
# ============================================================

fig_barres = px.bar(
    df_totals,

    x="actor_origin",
    y="events",

    color="actor_origin",

    color_discrete_map=colors,

    category_orders={
        "actor_origin": ordre_actors
    },

    labels={
        "actor_origin": "Actor",
        "events":
            "Nombre total d'esdeveniments"
    }
)


fig_barres.update_layout(

    title="Total d'esdeveniments per actor",

    xaxis_title="Actor",

    yaxis_title=(
        "Nombre total d'esdeveniments"
    ),

    showlegend=False
)


# L'eix representa magnituds absolutes:
# ha de començar a zero.

# Eliminem la retícula perquè, amb només dues barres,
# no aporta informació suficient per justificar el soroll visual.

fig_barres.update_yaxes(
    rangemode="tozero",
    showgrid=False
)

fig_barres.update_xaxes(
    showgrid=False
)


# ============================================================
# 13. CREAR ELS ESPAIS DE LES DUES VISUALITZACIONS
# ============================================================

# Creem primer els espais perquè el gràfic temporal
# aparegui visualment abans que el gràfic de barres.
#
# Internament processem primer les barres,
# ja que necessitem saber si l'usuari n'ha seleccionat una.

espai_linia = st.empty()

espai_barres = st.empty()


# ============================================================
# 14. MOSTRAR EL GRÀFIC DE BARRES INTERACTIU
# ============================================================

# on_select="rerun" fa que clicar una barra
# torni a executar l'aplicació amb la selecció disponible.
#
# Això permet connectar aquesta vista
# amb el gràfic temporal.

seleccio_barres = espai_barres.plotly_chart(

    fig_barres,

    use_container_width=True,

    on_select="rerun",

    selection_mode="points",

    key=(
        "barres_"
        f"{st.session_state['barres_version']}"
    )
)


# ============================================================
# 15. DETECTAR SI S'HA SELECCIONAT UNA BARRA
# ============================================================

actor_connectat = None


# Plotly retorna una llista de punts seleccionats.
# En aquest cas només ens interessa el primer,
# perquè cada barra representa un actor.

if seleccio_barres is not None:

    punts = (
        seleccio_barres
        .selection
        .get(
            "points",
            []
        )
    )

    if punts:

        actor_connectat = (
            punts[0]
            .get("x")
        )


# Comprovem que l'actor seleccionat també
# formi part dels filtres globals actuals.

if (
    actor_connectat
    not in actors_seleccionats
):

    actor_connectat = None


# ============================================================
# 16. CONNECTAR LES DUES VISTES
# ============================================================

# Si l'usuari ha clicat una barra,
# el gràfic temporal mostra només aquell actor.
#
# Si no hi ha cap selecció, mostra tots els actors
# seleccionats al filtre lateral.

if actor_connectat:

    df_linia = df_visual[
        df_visual["actor_origin"]
        == actor_connectat
    ].copy()

else:

    df_linia = df_visual.copy()


# ============================================================
# 17. CREAR EL GRÀFIC TEMPORAL
# ============================================================

fig_linia = px.line(

    df_linia,

    x="date",
    y="events",

    color="actor_origin",
    line_dash="actor_origin",

    color_discrete_map=colors,
    line_dash_map=estils_linia,

    category_orders={
        "actor_origin": ordre_actors
    },

    labels={
        "date": "Data",
        "events":
            "Nombre d'esdeveniments registrats",
        "actor_origin": "Actor"
    }
)


# ============================================================
# 18. CONFIGURAR EL GRÀFIC TEMPORAL
# ============================================================

if actor_connectat:

    titol_linia = (
        "Evolució temporal dels esdeveniments "
        f"— {actor_connectat}"
    )

else:

    titol_linia = (
        "Evolució temporal dels esdeveniments"
    )


fig_linia.update_layout(

    title=titol_linia,

    xaxis_title="Data",

    yaxis_title=(
        "Nombre d'esdeveniments registrats"
    ),

    legend_title="Actor",

    # Mostra els valors exactes
    # corresponents a la mateixa data.
    hovermode="x unified"
)


# L'eix Y representa valors absoluts,
# per tant ha de començar a 0.

fig_linia.update_yaxes(

    rangemode="tozero",

    # Retícula horitzontal lleugera.
    showgrid=True,

    gridwidth=0.5
)


# Eliminem la retícula vertical i mostrem
# una referència temporal cada tres mesos.

fig_linia.update_xaxes(

    showgrid=False,

    dtick="M3",

    tickformat="%b %Y"
)


# ============================================================
# 19. MOSTRAR EL GRÀFIC TEMPORAL
# ============================================================

# Omplim ara el primer espai creat anteriorment.
#
# Visualment apareix abans del gràfic de barres,
# encara que aquest últim s'hagi processat primer.

espai_linia.plotly_chart(
    fig_linia,
    use_container_width=True
)


# ============================================================
# 20. INFORMACIÓ SOBRE LA VISUALITZACIÓ
# ============================================================

st.caption(
    "La visualització inclou atacs aeris o amb drons i "
    "bombardejos, artilleria o atacs amb míssils registrats "
    "per ACLED entre el 8 d'octubre de 2023 i el 14 de setembre "
    "de 2025."
)