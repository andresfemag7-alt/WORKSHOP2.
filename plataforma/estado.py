"""Estado de sesión del flujo integrado: cada valor lleva módulo de origen, hora y entradas con que se calculó."""
from __future__ import annotations

import datetime as dt
import math

import streamlit as st

CLAVE = "flujo"
ETIQUETAS = {
    "q_total": ("Q_total", "m³/s"), "q_d": ("Q_d", "m³/s"), "y_c": ("y_c", "m"),
    "w": ("w (peso agua/long.)", "kN/m"), "W": ("W (peso en el tramo)", "kN"),
}


def _d() -> dict:
    return st.session_state.setdefault(CLAVE, {})


def publicar(clave: str, valor: float, unidad: str, modulo: str, entradas: dict | None = None, detalle: str = "") -> None:
    _d()[clave] = {"valor": float(valor), "unidad": unidad, "modulo": modulo, "detalle": detalle,
                   "hora": dt.datetime.now().strftime("%H:%M:%S"), "entradas": entradas or {}}


def obtener(clave: str) -> dict | None:
    return _d().get(clave)


def valor(clave: str, defecto=None):
    it = _d().get(clave)
    return it["valor"] if it else defecto


def invalidar(*claves: str) -> None:
    for c in claves:
        _d().pop(c, None)


def restablecer_todo() -> None:
    st.session_state[CLAVE] = {}
    for k in [k for k in st.session_state if k.startswith("res_")]:
        del st.session_state[k]


def iguales(a, b, rtol: float = 1e-9) -> bool:
    """Compara diccionarios de entradas (números con tolerancia relativa)."""
    if a.keys() != b.keys():
        return False
    for k in a:
        x, y = a[k], b[k]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
            if not math.isclose(x, y, rel_tol=rtol, abs_tol=1e-12):
                return False
        elif x != y:
            return False
    return True


def vigente(resultado: dict | None, entradas_actuales: dict) -> bool:
    return bool(resultado) and iguales(resultado["entradas"], entradas_actuales)
