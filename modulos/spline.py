"""Spline cúbico natural (S'' = 0 en los extremos), implementado con el sistema tridiagonal de
segundas derivadas. Es una interpolación POR TRAMOS (C2), distinta del polinomio único de Lagrange/Newton.
"""
from __future__ import annotations

import numpy as np

from .lagrange import validar_nodos


def spline_cubico_natural(xs, ys) -> dict:
    try:
        x, y = validar_nodos(xs, ys)
    except ValueError as exc:
        return {"exito": False, "mensaje": str(exc)}
    orden = np.argsort(x)
    x, y = x[orden], y[orden]
    n = x.size
    h = np.diff(x)

    if n == 2:  # un solo tramo: recta
        M = np.zeros(2)
    else:
        A = np.zeros((n, n))
        r = np.zeros(n)
        A[0, 0] = A[-1, -1] = 1.0  # condición natural: M_0 = M_{n-1} = 0
        for i in range(1, n - 1):
            A[i, i - 1] = h[i - 1]
            A[i, i] = 2.0 * (h[i - 1] + h[i])
            A[i, i + 1] = h[i]
            r[i] = 6.0 * ((y[i + 1] - y[i]) / h[i] - (y[i] - y[i - 1]) / h[i - 1])
        M = np.linalg.solve(A, r)

    # S_i(x) = a + b t + c t^2 + d t^3,  t = x - x_i
    a = y[:-1].copy()
    b = (y[1:] - y[:-1]) / h - h * (2 * M[:-1] + M[1:]) / 6.0
    c = M[:-1] / 2.0
    d = (M[1:] - M[:-1]) / (6.0 * h)

    def evaluar(xq):
        xq = np.asarray(xq, dtype=float)
        idx = np.clip(np.searchsorted(x, xq, side="right") - 1, 0, n - 2)
        t = xq - x[idx]
        v = a[idx] + b[idx] * t + c[idx] * t ** 2 + d[idx] * t ** 3
        return float(v) if np.ndim(xq) == 0 else v

    def derivada(xq):
        xq = np.asarray(xq, dtype=float)
        idx = np.clip(np.searchsorted(x, xq, side="right") - 1, 0, n - 2)
        t = xq - x[idx]
        v = b[idx] + 2 * c[idx] * t + 3 * d[idx] * t ** 2
        return float(v) if np.ndim(xq) == 0 else v

    res = {
        "exito": True, "mensaje": "Spline construido.",
        "tipo": "Spline cúbico natural (S''=0 en los extremos)",
        "nodos_x": x.tolist(), "nodos_y": y.tolist(),
        "coef_a": a.tolist(), "coef_b": b.tolist(), "coef_c": c.tolist(), "coef_d": d.tolist(),
        "segundas_derivadas": M.tolist(),
        "eval_func": evaluar, "deriv_func": derivada,
    }
    try:
        from scipy.interpolate import CubicSpline
        cs = CubicSpline(x, y, bc_type="natural")
        grid = np.linspace(x.min(), x.max(), 501)
        res["comparacion_libreria"] = {
            "libreria": "scipy.interpolate.CubicSpline(bc_type='natural')",
            "max_diferencia_absoluta": float(np.max(np.abs(cs(grid) - evaluar(grid)))),
        }
    except Exception as exc:  # pragma: no cover
        res["comparacion_libreria"] = {"error": str(exc)}
    return res


def verificar_monotonia(f, x_min: float, x_max: float, puntos: int = 2001) -> dict:
    """Comprueba numéricamente (sobre una malla) si una función es monótona creciente. No asume nada."""
    g = np.linspace(x_min, x_max, puntos)
    v = np.asarray(f(g), dtype=float)
    dv = np.diff(v)
    return {
        "creciente": bool(np.all(dv >= -1e-12)),
        "n_tramos_decrecientes": int(np.sum(dv < -1e-12)),
        "x_primer_decrecimiento": float(g[np.argmax(dv < -1e-12)]) if np.any(dv < -1e-12) else None,
    }
