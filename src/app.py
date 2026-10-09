from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. CONFIGURACIÓ DE LA PÀGINA
# ============================================================

st.set_page_config(page_title="Israel - Hezbollah", layout="wide")

st.title("Israel – Hezbollah: distribució espaciotemporal dels esdeveniments")


# ============================================================
# 2. CARREGAR EL DATASET PREPROCESSAT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "output" / "dades_visualitzacio.csv"

df_complet = pd.read_csv(CSV_PATH)


# ============================================================
# 3. PREPARAR LES ETIQUETES TEMPORALS
# ============================================================

MESOS_CA = {
    1: "Gen",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ag",
    9: "Set",
    10: "Oct",
    11: "Nov",
    12: "Des"
}

# Convertim el mes YYYY-MM en una data real
# per poder ordenar-lo cronològicament.
df_complet["month_date"] = pd.to_datetime(df_complet["month"] + "-01")

# Creem una etiqueta més llegible per mostrar-la al slider.
df_complet["month_label"] = df_complet["month_date"].apply(
    lambda data: f"{MESOS_CA[data.month]} {str(data.year)[2:]}"
)

# Guardem l'ordre cronològic correcte de les etiquetes.
ordre_mesos = (
    df_complet[["month", "month_label"]]
    .drop_duplicates()
    .sort_values("month")["month_label"]
    .tolist()
)


# ============================================================
# 4. ESTAT INICIAL DELS FILTRES
# ============================================================

if "actor_israel" not in st.session_state:
    st.session_state["actor_israel"] = True

if "actor_hezbollah" not in st.session_state:
    st.session_state["actor_hezbollah"] = True

if "seleccionar_tots" not in st.session_state:
    st.session_state["seleccionar_tots"] = True


# ============================================================
# 5. FUNCIONS DELS FILTRES
# ============================================================

def canviar_seleccionar_tots():
    """Activa o desactiva simultàniament els dos actors."""

    valor = st.session_state["seleccionar_tots"]

    st.session_state["actor_israel"] = valor
    st.session_state["actor_hezbollah"] = valor


def actualitzar_seleccionar_tots():
    """Sincronitza el checkbox general amb els dos actors."""

    st.session_state["seleccionar_tots"] = (
        st.session_state["actor_israel"]
        and st.session_state["actor_hezbollah"]
    )


# ============================================================
# 6. FUNCIÓ PER FORMATAR ELS NOMBRES
# ============================================================

def format_num(valor):
    """Mostra els milers amb punt: 16534 -> 16.534."""

    return f"{int(valor):,}".replace(",", ".")


# ============================================================
# 7. BARRA LATERAL
# ============================================================

st.sidebar.header("Filtres")

if st.sidebar.button("Restablir filtres"):
    st.session_state["actor_israel"] = True
    st.session_state["actor_hezbollah"] = True
    st.session_state["seleccionar_tots"] = True

st.sidebar.divider()
st.sidebar.subheader("Actors")

st.sidebar.checkbox(
    "Seleccionar tots",
    key="seleccionar_tots",
    on_change=canviar_seleccionar_tots
)

st.sidebar.checkbox(
    "Israel",
    key="actor_israel",
    on_change=actualitzar_seleccionar_tots
)

st.sidebar.checkbox(
    "Hezbollah",
    key="actor_hezbollah",
    on_change=actualitzar_seleccionar_tots
)


# ============================================================
# 8. ACTORS SELECCIONATS
# ============================================================

actors_seleccionats = []

if st.session_state["actor_israel"]:
    actors_seleccionats.append("Israel")

if st.session_state["actor_hezbollah"]:
    actors_seleccionats.append("Hezbollah")

# Evitem crear una visualització sense cap actor.
if not actors_seleccionats:
    st.warning("Selecciona almenys un actor.")
    st.stop()


# ============================================================
# 9. FILTRAR LES DADES
# ============================================================

# El mateix subconjunt alimentarà els KPIs i el mapa.
df = df_complet[
    df_complet["actor_origin"].isin(actors_seleccionats)
].copy()


# ============================================================
# 10. KPIs DEL PERÍODE COMPLET
# ============================================================

# Sumem la columna events de totes les localitzacions
# i mesos per obtenir el total de cada actor.
totals = df.groupby("actor_origin")["events"].sum()

# get() retorna 0 si l'actor no existeix al subconjunt.
total_israel = totals.get("Israel", 0)
total_hezbollah = totals.get("Hezbollah", 0)

# Si un actor està filtrat, mostrem "—" en lloc de 0
# per no confondre absència de selecció amb absència d'esdeveniments.
text_israel = format_num(total_israel) if st.session_state["actor_israel"] else "—"
text_hezbollah = format_num(total_hezbollah) if st.session_state["actor_hezbollah"] else "—"

# La ràtio només té sentit si els dos actors estan seleccionats
# i el denominador és diferent de zero.
if (
    st.session_state["actor_israel"]
    and st.session_state["actor_hezbollah"]
    and total_hezbollah > 0
):
    text_ratio = f"{total_israel / total_hezbollah:.2f}×"
else:
    text_ratio = "—"


# Distribuïm els tres indicadors en columnes independents.
col1, col2, col3 = st.columns(3)

col1.metric("Total període · Israel", text_israel)
col2.metric("Total període · Hezbollah", text_hezbollah)

col3.metric(
    "Ràtio global",
    text_ratio,
    help="Nombre d'esdeveniments atribuïts a Israel per cada esdeveniment atribuït a Hezbollah."
)


# ============================================================
# 11. RESUM NUMÈRIC DE CADA MES
# ============================================================

# Agrupem per mes i actor per obtenir els totals mensuals.
resum_mes = (
    df.groupby(["month_label", "actor_origin"])["events"]
    .sum()
    .unstack(fill_value=0)
    .reindex(ordre_mesos, fill_value=0)
)

# Després de l'unstack, cada actor passa a ser una columna:
#
#            Israel   Hezbollah
# Oct 23       ...        ...
# Nov 23       ...        ...


def text_resum_mes(mes):
    """Crea el text comparatiu corresponent a un mes."""

    # Seleccionem una sola fila del resum mensual.
    fila = resum_mes.loc[mes]

    israel = int(fila.get("Israel", 0))
    hezbollah = int(fila.get("Hezbollah", 0))

    # Respectem els filtres actius també en el resum mensual.
    text_israel_mes = format_num(israel) if st.session_state["actor_israel"] else "—"
    text_hezbollah_mes = format_num(hezbollah) if st.session_state["actor_hezbollah"] else "—"

    # Calculem la ràtio mensual amb el mateix criteri
    # que utilitzem per a la ràtio global.
    if (
        st.session_state["actor_israel"]
        and st.session_state["actor_hezbollah"]
        and hezbollah > 0
    ):
        ratio_mes = f"{israel / hezbollah:.2f}×"
    else:
        ratio_mes = "—"

    return (
        f"{mes} · Israel: {text_israel_mes} · "
        f"Hezbollah: {text_hezbollah_mes} · "
        f"Ràtio: {ratio_mes}"
    )


def crear_anotacio_mes(mes):
    """Defineix la caixa informativa que apareix sobre el mapa."""

    # Les coordenades x/y són relatives a la figura,
    # no coordenades geogràfiques del mapa.
    return {
        "text": text_resum_mes(mes),
        "x": 0.99,
        "y": 0.98,
        "xref": "paper",
        "yref": "paper",
        "xanchor": "right",
        "yanchor": "top",
        "showarrow": False,
        "bgcolor": "rgba(255,255,255,0.80)",
        "bordercolor": "rgba(0,0,0,0.25)",
        "borderpad": 6,
        "font": {"size": 13, "color": "#222"}
    }


# ============================================================
# 12. IDENTIFICADOR DELS PUNTS
# ============================================================

# Plotly necessita un identificador estable per relacionar
# una mateixa bombolla entre diferents frames temporals.
df["map_id"] = (
    df["actor_origin"].astype(str)
    + "_"
    + df["location"].astype(str)
    + "_"
    + df["latitude"].astype(str)
    + "_"
    + df["longitude"].astype(str)
)


# ============================================================
# 13. EXTENSIÓ GEOGRÀFICA
# ============================================================

# Obtenim els extrems geogràfics del dataset complet.
lat_min = df_complet["latitude"].min()
lat_max = df_complet["latitude"].max()

lon_min = df_complet["longitude"].min()
lon_max = df_complet["longitude"].max()

# Afegim un petit marge perquè els punts extrems
# no quedin enganxats als límits del mapa.
MARGE_LAT = 0.4
MARGE_LON = 0.4

south = lat_min - MARGE_LAT
north = lat_max + MARGE_LAT
west = lon_min - MARGE_LON
east = lon_max + MARGE_LON


# ============================================================
# 14. CENTRE DEL MAPA
# ============================================================

# Punt mig de l'extensió geogràfica.
centre_lat = (lat_min + lat_max) / 2
centre_lon = (lon_min + lon_max) / 2


# ============================================================
# 15. CODIFICACIÓ VISUAL
# ============================================================

# Mateix color per actor en tota la visualització.
COLORS = {
    "Israel": "#0072B2",
    "Hezbollah": "#D55E00"
}

# Limitem la mida màxima per evitar bombolles excessives.
SIZE_MAX = 28


# ============================================================
# 16. CREAR EL MAPA ESPACIOTEMPORAL
# ============================================================

fig = px.scatter_map(
    df,

    # Cada fila agregada es posiciona amb les seves coordenades.
    lat="latitude",
    lon="longitude",

    # Variable categòrica: diferencia els actors.
    color="actor_origin",

    # Variable quantitativa: controla l'àrea de la bombolla.
    size="events",
    size_max=SIZE_MAX,

    # Permet veure millor punts que se superposen.
    opacity=0.65,

    # Plotly crea un frame independent per cada mes.
    animation_frame="month_label",

    # Manté la identitat del mateix punt entre frames.
    animation_group="map_id",

    # location apareix com a capçalera del tooltip.
    hover_name="location",

    # Seleccionem quines variables apareixen al hover.
    hover_data={
        "month_label": True,
        "actor_origin": True,
        "events": True,
        "zona_operativa": True,

        # Variables necessàries per al mapa però
        # poc útils per a l'usuari final.
        "country": False,
        "admin1": False,
        "latitude": False,
        "longitude": False,
        "map_id": False,
        "month": False,
        "month_date": False
    },

    # Traducció de noms interns a etiquetes visibles.
    labels={
        "actor_origin": "Actor",
        "zona_operativa": "Zona",
        "events": "Esdeveniments",
        "month_label": "Mes"
    },

    color_discrete_map=COLORS,

    # Fixem l'ordre dels actors i dels frames temporals.
    category_orders={
        "actor_origin": ["Israel", "Hezbollah"],
        "month_label": ordre_mesos
    },

    center={"lat": centre_lat, "lon": centre_lon},
    zoom=5.0,
    map_style="carto-positron",
    height=700
)


# ============================================================
# 17. CONFIGURACIÓ DEL MAPA
# ============================================================

fig.update_layout(
    map={
        # Vista inicial.
        "center": {"lat": centre_lat, "lon": centre_lon},
        "zoom": 5.0,
        "style": "carto-positron",

        # Limitem la navegació a l'àrea de les dades.
        "bounds": {
            "west": west,
            "east": east,
            "south": south,
            "north": north
        }
    },

    # Llegenda horitzontal dels actors.
    legend={
        "title": {"text": "Actor"},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.01,
        "xanchor": "left",
        "x": 0
    },

    # Reduïm espai buit al voltant de la figura.
    margin={"l": 0, "r": 0, "t": 25, "b": 0},

    # Intenta conservar la vista del mapa durant actualitzacions.
    uirevision="mapa_constant"
)


# ============================================================
# 18. COMPARACIÓ DEL MES ACTUAL
# ============================================================

# El slider d'animació és intern de Plotly.
# Per això el resum mensual s'incorpora a cada frame,
# en lloc de calcular-lo amb un component extern de Streamlit.

if fig.frames:
    # Mostrem el resum del primer mes en carregar la figura.
    primer_mes = fig.frames[0].name
    fig.add_annotation(**crear_anotacio_mes(primer_mes))

    # Cada frame rep la seva pròpia anotació.
    # Quan canvia el mes, també canvia el resum numèric.
    for frame in fig.frames:
        frame.layout.annotations = [crear_anotacio_mes(frame.name)]


# ============================================================
# 19. CONFIGURACIÓ DE L'ANIMACIÓ
# ============================================================

if fig.layout.updatemenus:
    # Plotly crea automàticament els botons Play/Pause.
    botons = fig.layout.updatemenus[0].buttons

    if len(botons) >= 1:
        botons[0].label = "▶"

        # Temps que cada frame roman visible.
        botons[0].args[1]["frame"] = {
            "duration": 900,
            "redraw": True
        }

        # Duració visual del canvi entre frames.
        botons[0].args[1]["transition"] = {
            "duration": 300
        }

    if len(botons) >= 2:
        botons[1].label = "❚❚"


# ============================================================
# 20. CONFIGURACIÓ DEL SLIDER TEMPORAL
# ============================================================

if fig.layout.sliders:
    # Text que identifica el mes que s'està mostrant.
    fig.layout.sliders[0].currentvalue = {
        "prefix": "Mes: ",
        "font": {"size": 14}
    }

    fig.layout.sliders[0].pad = {"t": 20}


# ============================================================
# 21. MOSTRAR EL MAPA
# ============================================================

st.plotly_chart(fig, use_container_width=True)


# ============================================================
# 22. INFORMACIÓ DE SUPORT
# ============================================================

st.caption(
    "Mida de la bombolla: petita = menys esdeveniments · "
    "gran = més esdeveniments"
)

st.caption(
    "Font: ACLED · "
    "Període analitzat: 08/10/2023 – 14/09/2025 · "
    "Àmbit geogràfic: Israel, Líban i Síria"
)