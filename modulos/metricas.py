"""Métricas y diagnósticos comunes: residuales, condicionamiento, reproducción de nodos, errores."""
from __future__ import annotations

import numpy as np


def vector_residual_lineal(A, b, x) -> np.ndarray:
    """Residual r = A x - b (mismas unidades que b)."""
    A = np.asarray(A, dtype=float)
    return A @ np.asarray(x, dtype=float) - np.asarray(b, dtype=float)


def evaluar_condicionamiento(A) -> dict:
    """Número de condición kappa_2(A) y diagnóstico en lenguaje claro."""
    kappa = float(np.linalg.cond(np.asarray(A, dtype=float), 2))
    if not np.isfinite(kappa):
        estado = "singular"
        adv = "La matriz es singular o numéricamente singular: el sistema no tiene solución única."
    elif kappa < 1e2:
        estado = "bien condicionada"
        adv = "Un residual pequeño indica una solución fiable (kappa bajo)."
    elif kappa < 1e6:
        estado = "moderadamente condicionada"
        adv = "Se pierden algunas cifras significativas; un residual pequeño no garantiza el mismo error en x."
    else:
        estado = "mal condicionada"
        adv = ("kappa(A) es muy alto: un residual pequeño puede coexistir con un error grande en x. "
               "Conviene revisar el modelo o reescalar el sistema.")
    return {"kappa": kappa, "estado": estado, "advertencia": adv}


def evaluar_cambio_y_residual_no_lineal(x_anterior, x_nuevo, F) -> dict:
    """Cambio entre iteraciones y residual F(x_nuevo), por separado (el cambio NO es el error verdadero)."""
    xa = np.asarray(x_anterior, dtype=float)
    xn = np.asarray(x_nuevo, dtype=float)
    r = np.asarray(F(*xn), dtype=float)
    return {
        "norma_cambio": float(np.max(np.abs(xn - xa))),
        "residual_vector": r,
        "norma_residual": float(np.max(np.abs(r))),
    }


def verificar_reproduccion_nodos(xs, ys, f, tol_rel: float = 1e-9) -> dict:
    """Comprueba |P(x_i) - y_i| en cada nodo. ``f`` es un callable vectorizado."""
    xs = np.asarray(xs, dtype=float)
    ys = np.asarray(ys, dtype=float)
    yi = np.asarray(f(xs), dtype=float)
    err = np.abs(yi - ys)
    tol = tol_rel * max(1.0, float(np.max(np.abs(ys))))
    detalles = [
        {"nodo_x": float(x), "y_real": float(y), "y_interp": float(p), "error_absoluto": float(e)}
        for x, y, p, e in zip(xs, ys, yi, err)
    ]
    ok = bool(np.all(err <= tol))
    max_err = float(np.max(err))
    concl = (
        f"El polinomio reproduce todos los nodos (error máximo {max_err:.2e} <= tolerancia {tol:.1e}; "
        "diferencias atribuibles a redondeo de punto flotante)."
        if ok else
        f"ATENCIÓN: el error máximo en los nodos es {max_err:.2e} > tolerancia {tol:.1e}."
    )
    return {"detalles": detalles, "max_error": max_err, "tolerancia": tol, "reproduce": ok, "conclusion": concl}


def metricas_error(y_real, y_pred) -> dict:
    """MAE, RMSE y error máximo absoluto. Devuelve también n y una nota si n es pequeño."""
    y_real = np.atleast_1d(np.asarray(y_real, dtype=float))
    y_pred = np.atleast_1d(np.asarray(y_pred, dtype=float))
    e = y_pred - y_real
    n = int(e.size)
    nota = None
    if n == 0:
        return {"n": 0, "MAE": None, "RMSE": None, "error_max": None,
                "nota": "No hay observaciones de validación."}
    if n < 3:
        nota = (f"Solo hay {n} observación(es) de validación: MAE, RMSE y error máximo "
                "coinciden o son poco representativos. No se simulan más observaciones.")
    return {
        "n": n,
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e ** 2))),
        "error_max": float(np.max(np.abs(e))),
        "nota": nota,
    }
