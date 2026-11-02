"""Interpolación de Newton por diferencias divididas.

T[i, j] = f[x_i, ..., x_{i+j}] ;  a_k = T[0, k] ;
P_n(x) = a_0 + a_1 (x - x_0) + a_2 (x - x_0)(x - x_1) + ...   (evaluación anidada de Horner).
"""
from __future__ import annotations

import numpy as np

from .lagrange import texto_polinomio, validar_nodos


def tabla_diferencias_divididas(xs, ys) -> np.ndarray:
    x = np.asarray(xs, dtype=float)
    n = x.size
    T = np.zeros((n, n))
    T[:, 0] = np.asarray(ys, dtype=float)
    for j in range(1, n):
        for i in range(n - j):
            T[i, j] = (T[i + 1, j - 1] - T[i, j - 1]) / (x[i + j] - x[i])
    return T


def newton_evaluar_horner(coef, xs, x):
    """P(x) = a0 + (x-x0)(a1 + (x-x1)(a2 + ... + (x-x_{n-1}) a_n))."""
    a = np.asarray(coef, dtype=float)
    x_n = np.asarray(xs, dtype=float)
    xe = np.asarray(x, dtype=float)
    p = np.full_like(xe, a[-1], dtype=float)
    for k in range(a.size - 2, -1, -1):
        p = a[k] + (xe - x_n[k]) * p
    return float(p) if p.ndim == 0 else p


def texto_formula_newton(coef, xs, decimales: int = 6) -> str:
    a = np.asarray(coef, dtype=float)
    partes = [f"{a[0]:.{decimales}f}"]
    for k in range(1, a.size):
        factores = "".join(f"(x - {xs[j]:g})" for j in range(k))
        signo = "-" if a[k] < 0 else "+"
        partes.append(f"{signo} {abs(a[k]):.{decimales}f}{factores}")
    return " ".join(partes)


def polinomio_expandido(coef, xs) -> np.poly1d:
    a = np.asarray(coef, dtype=float)
    P = np.poly1d([a[0]])
    base = np.poly1d([1.0])
    for k in range(1, a.size):
        base = base * np.poly1d([1.0, -float(xs[k - 1])])
        P = P + a[k] * base
    return P


class PolinomioNewton:
    def __init__(self, coef, xs):
        self.coef = np.asarray(coef, dtype=float)
        self.xs = np.asarray(xs, dtype=float)

    def __call__(self, x):
        return newton_evaluar_horner(self.coef, self.xs, x)


def interpolacion_newton(xs, ys, x_eval=None) -> dict:
    try:
        x, y = validar_nodos(xs, ys)
    except ValueError as exc:
        return {"exito": False, "mensaje": str(exc)}
    T = tabla_diferencias_divididas(x, y)
    coef = T[0, :].copy()
    P = PolinomioNewton(coef, x)
    P_exp = polinomio_expandido(coef, x)

    from .metricas import verificar_reproduccion_nodos
    res = {
        "exito": True,
        "mensaje": "Polinomio construido.",
        "nodos_x": x.tolist(), "nodos_y": y.tolist(),
        "grado": int(x.size - 1),
        "tabla_completa": T,
        "coeficientes_newton": coef,
        "P_poly": P,
        "P_expandido": P_exp,
        "expresion_newton_str": texto_formula_newton(coef, x),
        "expresion_expandida_str": texto_polinomio(P_exp),
        "reproduccion_nodos": verificar_reproduccion_nodos(x, y, P),
        "x_eval": None, "valor_evaluado": None, "extrapolando": False, "advertencia_extrapolacion": None,
        "comparacion_libreria": None,
    }
    if x_eval is not None:
        xe = float(x_eval)
        if not np.isfinite(xe):
            return {"exito": False, "mensaje": "El valor a evaluar debe ser un número finito."}
        res["x_eval"] = xe
        res["valor_evaluado"] = float(P(xe))
        if xe < x.min() or xe > x.max():
            res["extrapolando"] = True
            res["advertencia_extrapolacion"] = (
                f"x = {xe:g} está FUERA del intervalo de los nodos [{x.min():g}, {x.max():g}]: es extrapolación.")
    try:
        from scipy.interpolate import BarycentricInterpolator
        bi = BarycentricInterpolator(x, y)
        comp = {"libreria": "scipy.interpolate.BarycentricInterpolator"}
        if x_eval is not None:
            v = float(bi(float(x_eval)))
            d = abs(v - res["valor_evaluado"])
            comp.update({"eval_libreria": v, "diferencia_eval": d,
                         "coincidencia": bool(d <= 1e-8 * max(1.0, abs(v)))})
        res["comparacion_libreria"] = comp
    except Exception as exc:  # pragma: no cover
        res["comparacion_libreria"] = {"error": str(exc)}
    return res


def agregar_nodo_newton(xs, ys, x_nuevo: float, y_nuevo: float, x_eval: float | None = None) -> dict:
    """Propiedad acumulativa: al añadir un nodo, a_0..a_n NO cambian y solo aparece un coeficiente nuevo.
    Devuelve ambos polinomios y la corrección a_{n+1} * prod (x - x_j) en x_eval."""
    antes = interpolacion_newton(xs, ys, x_eval)
    if not antes["exito"]:
        return antes
    xs2 = list(antes["nodos_x"]) + [float(x_nuevo)]
    ys2 = list(antes["nodos_y"]) + [float(y_nuevo)]
    despues = interpolacion_newton(xs2, ys2, x_eval)
    if not despues["exito"]:
        return despues
    n = len(antes["coeficientes_newton"])
    conservados = bool(np.allclose(despues["coeficientes_newton"][:n], antes["coeficientes_newton"], rtol=0, atol=1e-12))
    out = {
        "exito": True,
        "antes": antes, "despues": despues,
        "coeficientes_previos_conservados": conservados,
        "coeficiente_nuevo": float(despues["coeficientes_newton"][-1]),
        "correccion_en_x_eval": None,
    }
    if x_eval is not None:
        out["correccion_en_x_eval"] = float(despues["valor_evaluado"] - antes["valor_evaluado"])
    return out
