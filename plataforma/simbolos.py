"""Notación matemática legible: símbolos con subíndice (LaTeX) en los textos y notación científica limpia.
Solo cambia la presentación; no toca ningún cálculo."""
from __future__ import annotations

import functools
import re

_MAPA = {"Q_total": r"$Q_{total}$", "Q_d": r"$Q_d$", "y_c": r"$y_c$", "V_c": r"$V_c$"}
_PAT = re.compile(r"(?<![\w$\\])(Q_total|Q_d|y_c|V_c)(?!\w)")
_SUP = str.maketrans("0123456789-+", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺")


def sim(texto):
    """Q_total → $Q_{total}$, y_c → $y_c$… (solo si el texto no trae ya LaTeX)."""
    if not isinstance(texto, str) or "$" in texto:
        return texto
    return _PAT.sub(lambda m: _MAPA[m.group(1)], texto)


def bonito(texto: str) -> str:
    """Mensajes de los métodos numéricos: ||dx||_inf → ‖Δx‖∞, <= → ≤, 2.73e-16 → 2.73×10⁻¹⁶."""
    if not isinstance(texto, str):
        return texto
    texto = re.sub(r"\|\|(.+?)\|\|_inf", lambda m: "‖" + m.group(1).replace("dx", "Δx") + "‖∞", texto)
    texto = texto.replace("<=", "≤")

    def _cient(m):
        if float(m.group(0)) == 0:
            return "0"
        return f"{m.group(1)}×10{str(int(m.group(2))).translate(_SUP)}"

    return re.sub(r"(\d+(?:\.\d+)?)e([+-]\d+)", _cient, texto)


def instalar() -> None:
    """Aplica `sim` al texto de markdown/caption/success/info/warning/error/metric (una sola vez)."""
    try:
        from streamlit.delta_generator import DeltaGenerator as DG
    except Exception:  # pragma: no cover
        return
    if getattr(DG, "_simbolos_ok", False):
        return

    def _envolver(orig, nombre):
        @functools.wraps(orig)
        def w(self, *a, **k):
            try:
                if not (nombre == "markdown" and k.get("unsafe_allow_html")):
                    if a:
                        a = (sim(a[0]),) + tuple(a[1:])
                    elif isinstance(k.get("label"), str):
                        k["label"] = sim(k["label"])
            except Exception:  # pragma: no cover
                pass
            return orig(self, *a, **k)
        return w

    for nombre in ("markdown", "caption", "success", "info", "warning", "error", "metric"):
        orig = getattr(DG, nombre, None)
        if orig is not None:
            setattr(DG, nombre, _envolver(orig, nombre))
    DG._simbolos_ok = True
