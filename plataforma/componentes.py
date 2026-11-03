"""Componentes de interfaz reutilizables (sin lógica numérica)."""
from __future__ import annotations

import datetime as dt
import re

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


def cient_corto(x: float) -> str:
    """6e-8 → 6×10⁻⁸ (sin ceros sobrantes en la mantisa)."""
    mant, exp = f"{float(x):.6e}".split("e")
    mant = mant.rstrip("0").rstrip(".")
    return f"{mant.replace('-', '−')}×10{str(int(exp)).translate(_SUP)}"


_SUP_A_NORMAL = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")


def _leer_numero(texto: str) -> float:
    """Acepta 6e-8, 6x10^-8, 6×10^-8, 6*10^-8, 6×10⁻⁸, 10^-8 o un decimal normal."""
    t = texto.strip().lower().replace(",", ".").replace("−", "-").replace(" ", "")
    t = re.sub(r"10([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "10^" + m.group(1).translate(_SUP_A_NORMAL), t)
    m = re.fullmatch(r"([+-]?\d*\.?\d+)[x×*]10\^?\(?([+-]?\d+)\)?", t)
    if m:
        return float(f"{m.group(1)}e{int(m.group(2))}")
    m = re.fullmatch(r"10\^\(?([+-]?\d+)\)?", t)
    if m:
        return 10.0 ** int(m.group(1))
    return float(t)


def tolerancia(col, etiqueta: str, defecto: float, clave: str, ayuda: str, minimo: float = 1e-14, maximo: float = 1e-1) -> float:
    """Campo de texto para tolerancias: se escribe 6x10^-8 / 6e-8 y se muestra como 6×10⁻⁸. Si es inválido, se conserva el último valor válido."""
    ok = f"{clave}_ok"
    st.session_state.setdefault(ok, defecto)
    txt = col.text_input(etiqueta, value=f"{defecto:.0e}".replace("e-0", "e-"), key=clave, help=ayuda)
    try:
        v = _leer_numero(txt)
        if not (minimo <= v <= maximo):
            raise ValueError("rango")
        st.session_state[ok] = v
        col.caption(f"Se usa: **{cient_corto(v)}**")
    except Exception:
        col.error(f"Valor no válido. Escriba, por ejemplo, 6x10^-8 o 6e-8 (entre {cient_corto(minimo)} y {cient_corto(maximo)}). "
                  f"Se sigue usando {cient_corto(st.session_state[ok])}.")
    return float(st.session_state[ok])


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


_VAR = re.compile(r"([A-Za-zρα])(?:_(\w+))?")


def _var_html(m) -> str:
    return f"<i>{m.group(1)}</i>" + (f"<sub>{m.group(2)}</sub>" if m.group(2) else "")


def simbolo_html(texto: str) -> str:
    """Columna «Símbolo»: variables en cursiva y con subíndice real (Q_total → Q<sub>total</sub>)."""
    return _VAR.sub(_var_html, str(texto))


def descripcion_html(texto: str) -> str:
    """Columna «Descripción»: solo las fórmulas (A = b·y_c, w = ρ·g·A…) y condiciones (y > 0) pasan a notación matemática."""
    t = re.sub(r"\b[A-Za-zρα](?:_\w+)?\s*=\s*[\w·.]+", lambda m: _VAR.sub(_var_html, m.group(0)), str(texto))
    return re.sub(r"\b([yV])\s*>\s*0", r"<i>\1</i> &gt; 0", t)


def tabla_variables(filas: list[dict]) -> None:
    """filas: simbolo, descripcion, valor (str), unidad, proc (clave de tema.PROCEDENCIA)."""
    h = ("<table class='vars'><tr><th>Símbolo</th><th>Descripción</th><th>Valor</th><th>Unidad</th>"
         "<th>Procedencia / condición</th></tr>")
    for f in filas:
        h += (f"<tr><td><b>{simbolo_html(f['simbolo'])}</b></td><td>{descripcion_html(f['descripcion'])}</td><td>{f['valor']}</td>"
              f"<td>{f['unidad']}</td><td>{tema.insignia(f['proc'])}</td></tr>")
    st.markdown(h + "</table>", unsafe_allow_html=True)


def tabla_html(filas: list[dict]) -> None:
    """Tabla con el estilo de la app que admite símbolos con <i>, <sub> y <sup> (st.dataframe no los admite)."""
    cols = list(filas[0].keys())
    h = "<table class='vars'><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"
    for f in filas:
        celdas = []
        for c in cols:
            v = str(f.get(c, "—"))
            num = re.fullmatch(r"[−-]?[\d.,]+(×10[⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹]+)?", v) is not None
            celdas.append(f"<td class='n'>{v}</td>" if num else f"<td>{v}</td>")
        h += "<tr>" + "".join(celdas) + "</tr>"
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
