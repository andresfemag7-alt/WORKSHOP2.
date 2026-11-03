"""Utilidades de interfaz: configuración de página, fondo por página y figuras con estilo oscuro."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

RAIZ = Path(__file__).resolve().parent
IMG = RAIZ / "docs" / "img"

TEAL, AMBAR, HIELO, CORAL = "#2dd4bf", "#f5b942", "#cfe8f1", "#ff7a6b"


@lru_cache(maxsize=None)
def _imagen_b64(nombre: str) -> str:
    ruta = IMG / f"fondo_{nombre}.png"
    return base64.b64encode(ruta.read_bytes()).decode("ascii")


def iniciar(titulo: str, fondo: str, icono: str = "🌊") -> None:
    """Debe ser la primera llamada de cada página: config + imagen de fondo propia de la página."""
    st.set_page_config(page_title=f"{titulo} · Workshop 2", page_icon=icono, layout="wide")
    try:
        datos = _imagen_b64(fondo)
        fondo_css = f'url("data:image/png;base64,{datos}")'
    except OSError:          # si falta la imagen, la página sigue funcionando con el color base
        fondo_css = "none"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(7,26,38,.35), rgba(7,26,38,.55)), {fondo_css};
            background-size: cover; background-position: center; background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] > div:first-child {{ background: rgba(7,26,38,.82); backdrop-filter: blur(6px); }}
        .block-container {{
            background: rgba(7,26,38,.72); backdrop-filter: blur(6px);
            border: 1px solid rgba(207,232,241,.14); border-radius: 16px;
            padding: 2rem 2.4rem !important; margin-top: 1.2rem; max-width: 1100px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title(titulo)


def figura(ancho: float = 8.0, alto: float = 4.2):
    """Figura transparente con texto claro, para que se lea sobre el panel oscuro."""
    fig, ax = plt.subplots(figsize=(ancho, alto))
    fig.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    for lado in ax.spines.values():
        lado.set_color(HIELO)
        lado.set_alpha(0.4)
    ax.tick_params(colors=HIELO)
    ax.xaxis.label.set_color(HIELO)
    ax.yaxis.label.set_color(HIELO)
    ax.title.set_color(HIELO)
    ax.grid(alpha=0.12, color=HIELO)
    return fig, ax
