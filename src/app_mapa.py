import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path


st.set_page_config(
    page_title="Israel - Hezbollah | Mapa",
    layout="wide"
)

st.title(
    "Israel – Hezbollah: distribució espaciotemporal "
    "dels esdeveniments"
)

st.caption(
    "Cada frame representa un mes independent. "
    "La posició indica la localització, el color l'actor "
    "i la mida de la bombolla el nombre d'esdeveniments."
)


BASE_DIR = Path(__file__).resolve().parents[1]

CSV_PATH = (
    BASE_DIR
    / "output"
    / "dades_visualitzacio.csv"
)

df_complet = pd.read_csv(CSV_PATH)


if "actor_israel" not in st.session_state:
    st.session_state["actor_israel"] = True

if "actor_hezbollah" not in st.session_state:
    st.session_state["actor_hezbollah"] = True

if "seleccionar_tots" not in st.session_state:
    st.session_state["seleccionar_tots"] = True


def canviar_seleccionar_tots():

    valor = st.session_state["seleccionar_tots"]

    st.session_state["actor_israel"] = valor
    st.session_state["actor_hezbollah"] = valor


def actualitzar_seleccionar_tots():

    st.session_state["seleccionar_tots"] = (
        st.session_state["actor_israel"]
        and st.session_state["actor_hezbollah"]
    )


st.sidebar.header("Filtres")


if st.sidebar.button("Restablir filtres"):

    st.session_state["actor_israel"] = True
    st.session_state["actor_hezbollah"] = True
    st.session_state["seleccionar_tots"] = True


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


actors_seleccionats = []


if st.session_state["actor_israel"]:
    actors_seleccionats.append("Israel")

if st.session_state["actor_hezbollah"]:
    actors_seleccionats.append("Hezbollah")


if not actors_seleccionats:

    st.warning(
        "Selecciona almenys un actor."
    )

    st.stop()


df = df_complet[
    df_complet["actor_origin"].isin(
        actors_seleccionats
    )
].copy()


mesos = sorted(
    df_complet["month"].unique()
)


df["map_id"] = (
    df["actor_origin"].astype(str)
    + "_"
    + df["location"].astype(str)
    + "_"
    + df["latitude"].astype(str)
    + "_"
    + df["longitude"].astype(str)
)


lat_min = df_complet["latitude"].min()
lat_max = df_complet["latitude"].max()

lon_min = df_complet["longitude"].min()
lon_max = df_complet["longitude"].max()


MARGE_LAT = 0.4
MARGE_LON = 0.4


south = lat_min - MARGE_LAT
north = lat_max + MARGE_LAT

west = lon_min - MARGE_LON
east = lon_max + MARGE_LON


total_events = df_complet["events"].sum()


centre_lat = (
    (
        df_complet["latitude"]
        * df_complet["events"]
    ).sum()
    / total_events
)


centre_lon = (
    (
        df_complet["longitude"]
        * df_complet["events"]
    ).sum()
    / total_events
)


COLORS = {
    "Israel": "#0072B2",
    "Hezbollah": "#D55E00"
}


fig = px.scatter_map(

    df,

    lat="latitude",
    lon="longitude",

    color="actor_origin",
    size="events",

    animation_frame="month",
    animation_group="map_id",

    hover_name="location",

    hover_data={
        "actor_origin": True,
        "zona_operativa": True,
        "country": True,
        "admin1": True,
        "events": True,
        "latitude": False,
        "longitude": False,
        "map_id": False
    },

    labels={
        "actor_origin": "Actor",
        "zona_operativa": "Zona",
        "country": "País",
        "admin1": "Regió",
        "events": "Esdeveniments",
        "month": "Mes"
    },

    color_discrete_map=COLORS,

    category_orders={
        "actor_origin": [
            "Israel",
            "Hezbollah"
        ],
        "month": mesos
    },

    size_max=35,

    center={
        "lat": centre_lat,
        "lon": centre_lon
    },

    zoom=5.0,

    map_style="carto-positron",

    height=720
)


fig.update_layout(

    map={
        "center": {
            "lat": centre_lat,
            "lon": centre_lon
        },

        "zoom": 5.0,

        "style": "carto-positron",

        "bounds": {
            "west": west,
            "east": east,
            "south": south,
            "north": north
        }
    },

    legend={
        "title": {
            "text": "Actor"
        },

        "orientation": "h",

        "yanchor": "bottom",
        "y": 1.01,

        "xanchor": "left",
        "x": 0
    },

    margin={
        "l": 0,
        "r": 0,
        "t": 30,
        "b": 0
    },

    uirevision="mapa_constant"
)


if fig.layout.updatemenus:

    botons = fig.layout.updatemenus[0].buttons

    if len(botons) >= 1:

        botons[0].label = "▶"

        botons[0].args[1]["frame"] = {
            "duration": 900,
            "redraw": True
        }

        botons[0].args[1]["transition"] = {
            "duration": 300
        }

    if len(botons) >= 2:

        botons[1].label = "❚❚"


st.plotly_chart(
    fig,
    use_container_width=True
)