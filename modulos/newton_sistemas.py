"""Newton-Raphson multivariable.

En cada iteración se resuelve J(x^k) dx = -F(x^k) con una factorización LU (numpy.linalg.solve);
NUNCA se forma la inversa de J. Se distingue la corrección dx de la nueva aproximación
x^(k+1) = x^k + dx. El cambio ||dx|| NO es el error verdadero; se reporta aparte del residual.
"""
from __future__ import annotations

import numpy as np

COND_MAX = 1e14


def jacobiano_numerico(F, x, h: float | None = None) -> np.ndarray:
    """Jacobiano por diferencias centrales (alternativa cuando no hay J analítico)."""
    x = np.asarray(x, dtype=float).reshape(-1)
    n = x.size
    f0 = np.asarray(F(*x), dtype=float).reshape(-1)
    Jn = np.zeros((f0.size, n))
    for j in range(n):
        paso = (h if h is not None else np.cbrt(np.finfo(float).eps)) * max(1.0, abs(x[j]))
        xp, xm = x.copy(), x.copy()
        xp[j] += paso
        xm[j] -= paso
        Jn[:, j] = (np.asarray(F(*xp), dtype=float).reshape(-1) - np.asarray(F(*xm), dtype=float).reshape(-1)) / (2 * paso)
    return Jn


def newton_raphson_sistemas(F, x0, J=None, tol_cambio: float = 1e-4, tol_residual: float = 1e-4,
                            max_iter: int = 100, dominio=None) -> dict:
    """``F(*x)`` y ``J(*x)`` (opcional; si falta se usa jacobiano_numerico).
    ``dominio(x)`` (opcional) devuelve False si x sale del dominio admisible."""
    try:
        x = np.array(x0, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        return _fallo("La aproximación inicial debe ser numérica.")
    if x.size == 0 or not np.all(np.isfinite(x)):
        return _fallo("La aproximación inicial no puede estar vacía ni contener valores no finitos.")
    if max_iter < 1 or tol_cambio <= 0 or tol_residual <= 0:
        return _fallo("El máximo de iteraciones debe ser >= 1 y las tolerancias deben ser positivas.")
    if dominio is not None and not dominio(x):
        return _fallo("La aproximación inicial está fuera del dominio admisible.")

    historial = []
    motivo = f"Se alcanzó el máximo de iteraciones ({max_iter}) sin cumplir el criterio de parada."
    convergio = False
    for k in range(1, max_iter + 1):
        Fk = np.asarray(F(*x), dtype=float).reshape(-1)
        Jk = np.asarray(J(*x), dtype=float) if J is not None else jacobiano_numerico(F, x)
        if not (np.all(np.isfinite(Fk)) and np.all(np.isfinite(Jk))):
            motivo = f"F o J no son finitos en la iteración {k}."
            break
        cond = float(np.linalg.cond(Jk))
        if not np.isfinite(cond) or cond > COND_MAX:
            motivo = (f"Jacobiano singular o casi singular en la iteración {k} (cond = {cond:.2e}): "
                      "cambie la aproximación inicial.")
            break
        try:
            dx = np.linalg.solve(Jk, -Fk)  # sin inversa explícita
        except np.linalg.LinAlgError:
            motivo = f"Jacobiano singular en la iteración {k}."
            break
        x_new = x + dx
        if not np.all(np.isfinite(x_new)):
            motivo = f"La corrección no es finita en la iteración {k}."
            break
        if dominio is not None and not dominio(x_new):
            motivo = f"La aproximación salió del dominio admisible en la iteración {k}."
            break
        Fn = np.asarray(F(*x_new), dtype=float).reshape(-1)
        cambio = float(np.max(np.abs(dx)))
        nr_new = float(np.max(np.abs(Fn)))
        historial.append({
            "iteracion": k,
            "x_k": x.tolist(),
            "F_k": Fk.tolist(),
            "norma_residual_k": float(np.max(np.abs(Fk))),
            "jacobiano": Jk.tolist(),
            "cond_J": cond,
            "delta_x": dx.tolist(),
            "norma_cambio": cambio,
            "x_nuevo": x_new.tolist(),
            "residual_nuevo": Fn.tolist(),
            "norma_residual_nuevo": nr_new,
        })
        x = x_new
        if cambio <= tol_cambio and nr_new <= tol_residual:
            convergio = True
            motivo = (f"Convergió en {k} iteraciones: ||dx||_inf = {cambio:.2e} <= {tol_cambio:.1e} "
                      f"y ||F||_inf = {nr_new:.2e} <= {tol_residual:.1e}.")
            break
    return {
        "exito": True,
        "convergio": convergio,
        "motivo_parada": motivo,
        "x_sol": x.tolist(),
        "iteraciones": len(historial),
        "historial": historial,
    }


def comparar_con_libreria_no_lineal(F, x0, x_sol) -> dict:
    """Contraste con scipy.optimize.root (MINPACK hybrd) desde el mismo punto inicial."""
    from scipy.optimize import root
    sol = root(lambda v: np.asarray(F(*v), dtype=float), np.asarray(x0, dtype=float), method="hybr", tol=1e-12)
    x_lib = np.asarray(sol.x, dtype=float)
    dif = float(np.max(np.abs(np.asarray(x_sol, dtype=float) - x_lib)))
    return {
        "libreria_usada": "scipy.optimize.root (hybr / MINPACK)",
        "x_libreria": x_lib.tolist(),
        "converge_libreria": bool(sol.success),
        "max_diferencia_absoluta": dif,
        "nota": ("Las tolerancias del método propio (p. ej. 1e-4) son mucho más laxas que las de la biblioteca (1e-12), "
                 "por eso la diferencia refleja la tolerancia, no un error del algoritmo."),
    }


def _fallo(msg: str) -> dict:
    return {"exito": False, "convergio": False, "motivo_parada": msg, "mensaje": msg,
            "x_sol": None, "iteraciones": 0, "historial": []}
