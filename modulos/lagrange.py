"""Interpolación polinomial de Lagrange.

P_n(x) = sum_i y_i L_i(x),   L_i(x) = prod_{j != i} (x - x_j) / (x_i - x_j).
La evaluación numérica usa la forma de Lagrange directa (estable); el polinomio expandido en la base
canónica se entrega solo para mostrarlo (puede estar mal condicionado para grados altos).
"""
from __future__ import annotations

import numpy as np


def validar_nodos(xs, ys) -> tuple[np.ndarray, np.ndarray]:
    """Valida nodos; lanza ValueError con mensaje claro (nodos repetidos, no finitos, tamaños)."""
    try:
        x = np.array(xs, dtype=float).reshape(-1)
        y = np.array(ys, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        raise ValueError("Los nodos deben ser números.")
    if x.size != y.size:
        raise ValueError(f"Hay {x.size} valores de x y {y.size} de y: deben coincidir.")
    if x.size < 2:
        raise ValueError("Se necesitan al menos 2 nodos.")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        raise ValueError("Los nodos no pueden contener valores vacíos, NaN o infinitos.")
    xs_sorted = np.sort(x)
    escala = max(1.0, float(np.max(np.abs(x))))
    if np.any(np.diff(xs_sorted) <= 1e-12 * escala):
        raise ValueError("Hay nodos x repetidos (o prácticamente iguales): la interpolación no está definida.")
    return x, y


def bases_lagrange(xs) -> list[np.poly1d]:
    """Polinomios base L_i(x) como numpy.poly1d."""
    x = np.asarray(xs, dtype=float)
    bases = []
    for i in range(x.size):
        p = np.poly1d([1.0])
        den = 1.0
        for j in range(x.size):
            if j != i:
                p = p * np.poly1d([1.0, -x[j]])
                den *= x[i] - x[j]
        bases.append(p / den)
    return bases


def texto_polinomio(p: np.poly1d, var: str = "x", decimales: int = 6) -> str:
    """Texto legible de un poly1d, p. ej. '5.333333 x^2 - 19.333333 x + 16.000000'."""
    c = np.atleast_1d(p.coeffs)
    grado = len(c) - 1
    partes = []
    for k, a in enumerate(c):
        pot = grado - k
        if abs(a) < 10 ** (-decimales - 3) and len(c) > 1:
            continue
        signo = "-" if a < 0 else "+"
        mag = f"{abs(a):.{decimales}f}"
        if pot == 0:
            term = mag
        elif pot == 1:
            term = f"{mag} {var}"
        else:
            term = f"{mag} {var}^{pot}"
        partes.append((signo, term))
    if not partes:
        return f"{0:.{decimales}f}"
    s = ("-" if partes[0][0] == "-" else "") + partes[0][1]
    for signo, term in partes[1:]:
        s += f" {signo} {term}"
    return s


def lagrange_evaluar_directo(xs, ys, x) -> np.ndarray | float:
    """Evalúa P_n en x (escalar o arreglo) con la fórmula de Lagrange, sin expandir el polinomio."""
    x_n = np.asarray(xs, dtype=float)
    y_n = np.asarray(ys, dtype=float)
    xe = np.asarray(x, dtype=float)
    res = np.zeros_like(xe, dtype=float)
    for i in range(x_n.size):
        Li = np.ones_like(xe, dtype=float)
        for j in range(x_n.size):
            if j != i:
                Li = Li * (xe - x_n[j]) / (x_n[i] - x_n[j])
        res = res + y_n[i] * Li
    return float(res) if res.ndim == 0 else res


class PolinomioLagrange:
    """Callable vectorizado; guarda los nodos para poder avisar de extrapolación."""

    def __init__(self, xs, ys):
        self.xs = np.asarray(xs, dtype=float)
        self.ys = np.asarray(ys, dtype=float)

    def __call__(self, x):
        return lagrange_evaluar_directo(self.xs, self.ys, x)


def lagrange_interpolacion(xs, ys, x_eval=None) -> dict:
    """Construye P_n, sus bases, evalúa en ``x_eval`` y comprueba reproducción de nodos."""
    try:
        x, y = validar_nodos(xs, ys)
    except ValueError as exc:
        return {"exito": False, "mensaje": str(exc)}

    bases = bases_lagrange(x)
    P_exp = np.poly1d([0.0])
    for yi, Li in zip(y, bases):
        P_exp = P_exp + yi * Li
    P = PolinomioLagrange(x, y)

    from .metricas import verificar_reproduccion_nodos
    res = {
        "exito": True,
        "mensaje": "Polinomio construido.",
        "nodos_x": x.tolist(),
        "nodos_y": y.tolist(),
        "grado": int(x.size - 1),
        "bases_L": bases,
        "P_expandido": P_exp,
        "P_poly": P,
        "expresion_algebraica": texto_polinomio(P_exp),
        "reproduccion_nodos": verificar_reproduccion_nodos(x, y, P),
        "x_eval": None, "valor_evaluado": None, "extrapolando": False, "advertencia_extrapolacion": None,
        "valores_bases_en_x_eval": None,
        "comparacion_libreria": None,
    }

    if x_eval is not None:
        xe = float(x_eval)
        if not np.isfinite(xe):
            return {"exito": False, "mensaje": "El valor a evaluar debe ser un número finito."}
        res["x_eval"] = xe
        res["valor_evaluado"] = float(P(xe))
        res["valores_bases_en_x_eval"] = [float(Li(xe)) for Li in bases]
        if xe < x.min() or xe > x.max():
            res["extrapolando"] = True
            res["advertencia_extrapolacion"] = (
                f"x = {xe:g} está FUERA del intervalo de los nodos [{x.min():g}, {x.max():g}]: es extrapolación; "
                "los polinomios de grado alto pueden oscilar fuertemente fuera de los nodos.")

    # Contraste con SciPy
    try:
        # scipy.interpolate.lagrange está obsoleta (se retira en SciPy 1.20); BarycentricInterpolator
        # construye el mismo polinomio único de forma numéricamente estable.
        from scipy.interpolate import BarycentricInterpolator
        sp = BarycentricInterpolator(x, y)
        comp = {"libreria": "scipy.interpolate.BarycentricInterpolator (mismo polinomio que scipy.interpolate.lagrange)"}
        if x_eval is not None:
            v = float(sp(float(x_eval)))
            d = abs(v - res["valor_evaluado"])
            comp.update({"eval_scipy": v, "diferencia_eval": d,
                         "coincidencia": bool(d <= 1e-8 * max(1.0, abs(v)))})
        res["comparacion_libreria"] = comp
    except Exception as exc:  # pragma: no cover
        res["comparacion_libreria"] = {"error": str(exc)}
    return res
