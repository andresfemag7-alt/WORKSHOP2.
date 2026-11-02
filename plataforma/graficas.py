"""Gráficas (Plotly) con ejes, títulos, leyendas y unidades. Estilo desde config/tema.py."""
from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go

from .config.tema import PALETA, layout_grafica

COLOR_ESTADO = {"tracción": PALETA["traccion"], "compresión": PALETA["compresion"], "fuerza nula": PALETA["nula"]}


def fig_armadura(sis: dict, res: dict) -> go.Figure:
    nodos = sis["nodos"]
    L, H = sis["L"], sis["H"]
    fig = go.Figure()
    fmax = max(abs(f) for f in res["fuerzas_kN"].values()) or 1.0
    for nom, a, b in sis["barras"]:
        f = res["fuerzas_kN"][nom]
        est = res["estado_barras"][nom]
        (x0, y0), (x1, y1) = nodos[a], nodos[b]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines", showlegend=False,
            line=dict(color=COLOR_ESTADO[est], width=2 + 6 * abs(f) / fmax, dash="dash" if est == "compresión" else "solid"),
            hovertemplate=f"Barra {nom}: {f:+.2f} kN ({est})<extra></extra>"))
        fig.add_annotation(x=(x0 + x1) / 2, y=(y0 + y1) / 2 + (0.09 * H if y0 == y1 and y0 > 0 else -0.09 * H if y0 == y1 else 0.0),
                           text=f"<b>{nom}</b><br>{f:+.1f} kN", showarrow=False, font=dict(size=11, color=COLOR_ESTADO[est]),
                           bgcolor="rgba(255,255,255,0.85)")
    for nom, (x, y) in nodos.items():
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text", text=[nom], textposition="top center" if y > 0 else "bottom center",
                                 marker=dict(size=10, color=PALETA["nodo"]), showlegend=False,
                                 hovertemplate=f"Nudo {nom} ({x:.2f}, {y:.2f}) m<extra></extra>"))
    for nudo, (cx, cy) in sis["cargas"].items():
        x, y = nodos[nudo]
        fig.add_annotation(x=x, y=y, ax=x, ay=y + 0.55 * H, xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                           arrowhead=3, arrowwidth=2.5, arrowcolor=PALETA["agua"], text=f"{abs(cy):.1f} kN", font=dict(color=PALETA["agua"]), yshift=0)
    for key, val in res["reacciones_kN"].items():
        eje, nudo = key[1], key.split("_")[1]
        x, y = nodos[nudo]
        if eje == "y" and abs(val) > 1e-9:
            fig.add_annotation(x=x, y=y, ax=x, ay=y - 0.55 * H, xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                               arrowhead=3, arrowwidth=2.5, arrowcolor=PALETA["ok"], text=f"R{eje}={val:.1f} kN", font=dict(color=PALETA["ok"]))
    for tr in [("Tracción (+)", PALETA["traccion"], "solid"), ("Compresión (−)", PALETA["compresion"], "dash"), ("Fuerza nula", PALETA["nula"], "solid")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name=tr[0], line=dict(color=tr[1], dash=tr[2], width=4)))
    fig.add_trace(go.Scatter(x=[0, L], y=[0, 0], mode="markers", name="Apoyos (A fijo, C móvil)",
                             marker=dict(symbol=["triangle-up", "circle-open"], size=15, color=PALETA["texto"],
                                         line=dict(width=2, color=PALETA["texto"]))))
    fig.update_layout(**layout_grafica("Armadura Warren — fuerzas axiales", "x (m)", "y (m)", alto=430))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, range=[-0.9 * H, 1.8 * H])
    fig.update_xaxes(range=[-0.1 * L, 1.1 * L])
    return fig


def fig_funcion_critica(Q, b, g, y_sol, y_hist) -> go.Figure:
    ys = np.linspace(0.05 * y_sol, 2.2 * y_sol, 300)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ys, y=Q ** 2 - g * b ** 2 * ys ** 3, mode="lines", name="f(y) = Q² − g·b²·y³",
                             line=dict(color=PALETA["primario"], width=3)))
    fig.add_hline(y=0, line=dict(color=PALETA["suave"], dash="dot"))
    if y_hist:
        fig.add_trace(go.Scatter(x=y_hist, y=[Q ** 2 - g * b ** 2 * y ** 3 for y in y_hist], mode="markers+lines",
                                 name="Iterados de Newton (caso 1×1)", marker=dict(size=8, color=PALETA["acento"]),
                                 line=dict(color=PALETA["acento"], dash="dot")))
    fig.add_trace(go.Scatter(x=[y_sol], y=[0], mode="markers", name="Raíz y_c", marker=dict(size=13, symbol="star", color=PALETA["validacion"])))
    fig.update_layout(**layout_grafica("Función de la profundidad crítica", "Profundidad y (m)", "f(y) (m⁶/s²)"))
    return fig


def fig_convergencia(series: dict) -> go.Figure:
    """series: {nombre: {'cambio': [...], 'residual': [...]}} — dos paneles: cambio y residual, escala log."""
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Cambio entre iteraciones ‖Δx‖∞", "Residual ‖F(x)‖∞ (escalado)"))
    colores = [PALETA["primario"], PALETA["acento"], PALETA["ok"]]
    for i, (nom, s) in enumerate(series.items()):
        it = list(range(1, len(s["cambio"]) + 1))
        fig.add_trace(go.Scatter(x=it, y=np.maximum(s["cambio"], 1e-18), mode="lines+markers", name=nom, legendgroup=nom,
                                 line=dict(color=colores[i % 3])), row=1, col=1)
        fig.add_trace(go.Scatter(x=it, y=np.maximum(s["residual"], 1e-18), mode="lines+markers", name=nom, legendgroup=nom,
                                 showlegend=False, line=dict(color=colores[i % 3])), row=1, col=2)
    fig.update_yaxes(type="log", gridcolor="#E3EAEF")
    fig.update_xaxes(title_text="Iteración", gridcolor="#E3EAEF")
    fig.update_layout(**layout_grafica("Convergencia (el cambio NO es el error verdadero)", "", "", alto=380))
    fig.update_layout(xaxis=dict(title="Iteración"), yaxis=dict(title="‖Δx‖∞ (m, m/s)", type="log"),
                      xaxis2=dict(title="Iteración"), yaxis2=dict(title="‖F‖∞ (adim.)", type="log"))
    return fig


def fig_interpolacion(h_nodos, q_nodos, curvas: dict, h_consulta=None, q_consulta=None, validaciones=None, titulo="Curva nivel–caudal") -> go.Figure:
    hh = np.linspace(min(h_nodos), max(h_nodos), 300)
    fig = go.Figure()
    estilos = {"Lagrange": (PALETA["lagrange"], "solid", 4), "Newton": (PALETA["newton"], "dash", 2.5), "Spline cúbico natural": (PALETA["spline"], "dot", 3)}
    for nom, f in curvas.items():
        c, d, w = estilos.get(nom, (PALETA["primario"], "solid", 3))
        fig.add_trace(go.Scatter(x=hh, y=f(hh), mode="lines", name=nom, line=dict(color=c, dash=d, width=w)))
    fig.add_trace(go.Scatter(x=h_nodos, y=q_nodos, mode="markers", name="Nodos de construcción",
                             marker=dict(size=11, color=PALETA["nodo"], symbol="circle")))
    if validaciones:
        fig.add_trace(go.Scatter(x=[v["h_m"] for v in validaciones], y=[v["Q_m3s"] for v in validaciones], mode="markers",
                                 name="Validación (no usada en la construcción)",
                                 marker=dict(size=14, color=PALETA["validacion"], symbol="diamond-open", line=dict(width=3))))
    if h_consulta is not None and q_consulta is not None:
        fig.add_trace(go.Scatter(x=[h_consulta], y=[q_consulta], mode="markers", name="Consulta",
                                 marker=dict(size=15, color=PALETA["acento"], symbol="star")))
    fig.update_layout(**layout_grafica(titulo, "Nivel del río h (m)", "Caudal Q (m³/s)", alto=440))
    return fig


def fig_diferencias(hh, dif: dict) -> go.Figure:
    fig = go.Figure()
    for nom, v in dif.items():
        fig.add_trace(go.Scatter(x=hh, y=v, mode="lines", name=nom))
    fig.update_layout(**layout_grafica("Diferencias entre representaciones", "Nivel h (m)", "Diferencia de Q (m³/s)", alto=320))
    return fig
