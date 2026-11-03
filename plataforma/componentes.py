"""Componentes de interfaz reutilizables (sin lógica numérica)."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

from .config import textos, tema
from .estado import iguales


_SUP = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")


def cient(x, n: int = 2) -> str:
    """Notación científica limpia: 1.42e-14 → 1.42×10⁻¹⁴ (el cero se muestra como 0)."""
    if x is None:
        return "—"
    x = float(x)
    if x == 0:
        return "0"
    mant, exp = f"{x:.{n}e}".split("e")
    return f"{mant.replace('-', '−')}×10{str(int(exp)).translate(_SUP)}"


def fmt(x, n: int = 4) -> str:
    if x is None:
        return "—"
    try:
        if x != 0 and (abs(x) < 10 ** (-n) or abs(x) >= 1e7):
            return cient(x, 3)
        return f"{x:,.{n}f}"
    except (TypeError, ValueError):
        return str(x)


def ficha(clave: str) -> None:
    t = textos.TABS[clave]
    st.markdown(
        f'<div class="ficha"><div><b>Problema físico:</b> {t["problema"]}</div>'
        f'<div><b>Método numérico:</b> {t["metodo"]}</div>'
        f'<div><b>Datos que entran:</b> {t["entradas"]}</div>'
        f'<div><b>Resultado:</b> {t["resultado"]}</div>'
        f'<div><b>Límites:</b> {t["limites"]}</div></div>', unsafe_allow_html=True)


def cabecera_tab(clave: str) -> None:
    t = textos.TABS[clave]
    st.subheader(t["titulo"])
    st.caption(t["descripcion"])
    ficha(clave)


def tabla_variables(filas: list[dict]) -> None:
    """filas: simbolo, descripcion, valor (str), unidad, proc (clave de tema.PROCEDENCIA)."""
    h = ("<table class='vars'><tr><th>Símbolo</th><th>Descripción</th><th>Valor</th><th>Unidad</th>"
         "<th>Procedencia / condición</th></tr>")
    for f in filas:
        h += (f"<tr><td><b>{f['simbolo']}</b></td><td>{f['descripcion']}</td><td>{f['valor']}</td>"
              f"<td>{f['unidad']}</td><td>{tema.insignia(f['proc'])}</td></tr>")
    st.markdown(h + "</table>", unsafe_allow_html=True)


def tabla_html(filas: list[dict]) -> None:
    """Tabla con el estilo de la app que admite símbolos con <i>, <sub> y <sup> (st.dataframe no los admite)."""
    cols = list(filas[0].keys())
    h = "<table class='vars'><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"
    for f in filas:
        h += "<tr>" + "".join(f"<td>{f.get(c, '—')}</td>" for c in cols) + "</tr>"
    st.markdown(h + "</table>", unsafe_allow_html=True)


def tabla(df: pd.DataFrame, **kw) -> None:
    st.dataframe(df, hide_index=kw.pop("hide_index", True), width="stretch", **kw)


def grafica(fig, key: str) -> None:
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})


def ejecutar(clave: str, entradas: dict, fn, etiqueta: str = "Calcular", auto: bool = True):
    """Patrón común: botón de ejecución + cálculo inicial automático + aviso si las entradas cambiaron."""
    k = f"res_{clave}"
    pulsado = st.button(etiqueta, key=f"btn_{clave}", type="primary")
    if pulsado or (auto and k not in st.session_state):
        st.session_state[k] = {"entradas": entradas, "datos": fn(), "hora": dt.datetime.now().strftime("%H:%M:%S")}
    res = st.session_state.get(k)
    if res and not iguales(res["entradas"], entradas):
        st.warning("⚠️ Los resultados mostrados se calcularon con entradas anteriores y están **desactualizados**. "
                   f"Pulse «{etiqueta}» para recalcular.")
    return res


def vigente(res, entradas: dict) -> bool:
    return bool(res) and iguales(res["entradas"], entradas)
