"""Identidad visual centralizada: paleta, tipografía, espaciados, estilos de gráficas y CSS.
Cualquier cambio de apariencia se hace SOLO aquí (y en .streamlit/config.toml para el tema base)."""
import streamlit as st

PALETA = {
    "primario": "#0B5C8E",     # azul de ingeniería
    "agua": "#2E86C1",
    "acento": "#C98B00",
    "ok": "#2E7D32",
    "alerta": "#9A5B00",
    "error": "#B3261E",
    "texto": "#1D2731",
    "suave": "#5B6B79",
    "borde": "#CAD6DF",
    "fondo_tarjeta": "#FFFFFF",
    "traccion": "#1565C0",
    "compresion": "#C62828",
    "nula": "#7A8791",
    "lagrange": "#0B5C8E",
    "newton": "#C98B00",
    "spline": "#2E7D32",
    "validacion": "#B3261E",
    "nodo": "#1D2731",
}
FUENTE = "Segoe UI, Roboto, Helvetica, Arial, sans-serif"
ESPACIADO = {"s": "0.4rem", "m": "0.8rem", "l": "1.4rem"}

# Etiquetas de procedencia: clave -> (texto, color)
PROCEDENCIA = {
    "fuente": ("Fuente primaria (USGS)", "#1B5E20"),
    "preliminar": ("Preliminar · no verificado", "#9A5B00"),
    "supuesto": ("Supuesto del escenario", "#7A5C00"),
    "calculado": ("Calculado", "#0B5C8E"),
    "editado": ("Editado por el usuario", "#6A1B9A"),
    "constante": ("Constante física", "#455A64"),
}

ICONOS = {"lineales": "🏗️", "no_lineales": "🌊", "lagrange": "📈", "newton": "📉",
          "ok": "✅", "alerta": "⚠️", "error": "⛔", "info": "ℹ️"}

PLOTLY_BASE = dict(
    template="plotly_white",
    font=dict(family=FUENTE, size=13, color=PALETA["texto"]),
    # t=110: franja superior reservada. El título va arriba del todo y la leyenda justo encima del área
    # de trazado, de modo que ya no compiten por el mismo espacio (antes t=50 y se superponían).
    margin=dict(l=60, r=20, t=110, b=55),
    legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0),
    hovermode="closest",
)


def layout_grafica(titulo: str, x: str, y: str, alto: int = 420, **extra) -> dict:
    d = dict(PLOTLY_BASE)
    d.update(title=dict(text=titulo, font=dict(size=15), x=0, xanchor="left", y=0.97, yanchor="top", yref="container"),
             height=alto,
             xaxis=dict(title=x, gridcolor="#E3EAEF", zeroline=False),
             yaxis=dict(title=y, gridcolor="#E3EAEF", zeroline=False))
    d.update(extra)
    return d


def insignia(clave: str) -> str:
    texto, color = PROCEDENCIA[clave]
    return (f'<span class="ins" style="background:{color}1A;color:{color};border:1px solid {color}66">{texto}</span>')


CSS = f"""
<style>
html, body, [class*="css"] {{ font-family: {FUENTE}; }}
.block-container {{ padding-top: 1.4rem; max-width: 1180px; }}
.app-titulo {{ font-size: 1.55rem; font-weight: 700; color: {PALETA['primario']}; margin: 0; }}
.app-sub {{ color: {PALETA['suave']}; margin: 0 0 {ESPACIADO['m']} 0; }}
.ins {{ display:inline-block; padding:1px 8px; border-radius:10px; font-size:.74rem; font-weight:600; white-space:nowrap; }}
table.vars {{ border-collapse: collapse; width:100%; font-size:.9rem; }}
table.vars th {{ text-align:left; background:#E6EEF3; padding:6px 8px; border-bottom:2px solid {PALETA['borde']}; }}
table.vars td {{ padding:6px 8px; border-bottom:1px solid {PALETA['borde']}; vertical-align:top; }}
.ficha {{ background:{PALETA['fondo_tarjeta']}; border:1px solid {PALETA['borde']}; border-left:5px solid {PALETA['primario']};
          border-radius:6px; padding:.7rem 1rem; margin-bottom:{ESPACIADO['m']}; }}
.ficha b {{ color:{PALETA['primario']}; }}
.ficha div {{ margin:.15rem 0; }}
.caja-res {{ background:#EAF4EC; border:1px solid #9CC9A3; border-radius:6px; padding:.6rem 1rem; margin:.4rem 0; }}
.caja-aviso {{ background:#FFF6E0; border:1px solid #E0C070; border-radius:6px; padding:.6rem 1rem; margin:.4rem 0; }}
.caja-error {{ background:#FDECEA; border:1px solid #E5A19B; border-radius:6px; padding:.6rem 1rem; margin:.4rem 0; }}
@media (max-width: 640px) {{ .app-titulo {{ font-size: 1.2rem; }} table.vars {{ font-size:.8rem; }} }}
</style>
"""


def aplicar_tema() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    fondo_app()


@st.cache_data(show_spinner=False)
def _collage_b64() -> str:
    import base64
    from pathlib import Path
    ruta = Path(__file__).resolve().parents[2] / "assets" / "collage.jpg"
    return base64.b64encode(ruta.read_bytes()).decode()


def fondo_app() -> None:
    """Collage simétrico 2x2 (lineales, no lineales, Lagrange, Newton+Spline) como fondo fijo de toda la app."""
    st.markdown(
        '<style>'
        '.stApp {background-image: linear-gradient(rgba(246,249,251,.15), rgba(246,249,251,.15)), '
        f'url("data:image/jpeg;base64,{_collage_b64()}");'
        'background-size: 100% 100%; background-position: center; background-attachment: fixed; background-repeat: no-repeat;}'
        '[data-testid="stHeader"] {background: transparent;}'
        '.block-container {background: rgba(255,255,255,.80); border-radius: 10px; padding: 1.4rem 1.6rem 2rem 1.6rem;}'
        '</style>', unsafe_allow_html=True)
