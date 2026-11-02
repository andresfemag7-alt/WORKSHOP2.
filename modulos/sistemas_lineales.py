"""Eliminación gaussiana con pivoteo parcial por columnas y sustitución regresiva.

Algoritmo del notebook ``1_sistemas_lineales``: para cada etapa k se escoge como pivote el mayor |M_ik|
(i >= k); se intercambian filas si hace falta; se anulan los elementos inferiores con los
multiplicadores m_ik = M_ik / M_kk; finalmente se sustituye hacia atrás.
Los índices de etapas, filas y columnas del historial son 1-based (como en el manuscrito).
"""
from __future__ import annotations

import numpy as np

from .metricas import evaluar_condicionamiento

EPS_SINGULAR = 1e-14


def gauss_pivoteo_parcial(A, b, eps: float = EPS_SINGULAR) -> dict:
    """Resuelve A x = b. Nunca lanza excepciones por datos inválidos: devuelve ``exito=False``."""
    try:
        A0 = np.array(A, dtype=float)
        b0 = np.array(b, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        return {"exito": False, "mensaje": "A y b deben contener solo números."}
    if A0.ndim != 2 or A0.shape[0] != A0.shape[1]:
        return {"exito": False, "mensaje": f"A debe ser cuadrada; se recibió forma {A0.shape}."}
    n = A0.shape[0]
    if n == 0 or b0.shape[0] != n:
        return {"exito": False, "mensaje": f"Dimensiones incompatibles: A es {n}x{n} y b tiene {b0.shape[0]} elementos."}
    if not (np.all(np.isfinite(A0)) and np.all(np.isfinite(b0))):
        return {"exito": False, "mensaje": "A y b no pueden contener valores vacíos, NaN o infinitos."}

    # Umbral de singularidad: eps escalado por la magnitud de A (eps absoluto si |A| <= 1).
    umbral = eps * max(1.0, float(np.max(np.abs(A0))))

    M = np.hstack([A0, b0.reshape(-1, 1)])
    historial = []
    matrices_etapas = [M.copy()]  # [A|b] inicial y tras cada etapa

    for k in range(n - 1):
        col = np.abs(M[k:, k])
        p = k + int(np.argmax(col))
        pivote = M[p, k]
        if abs(pivote) < umbral:
            return {
                "exito": False,
                "mensaje": (f"Matriz singular o de rango deficiente: el pivote máximo de la columna {k + 1} es "
                            f"{abs(pivote):.2e} (< {umbral:.1e}). El sistema no tiene solución única."),
                "historial_pasos": historial,
            }
        hubo = p != k
        if hubo:
            M[[k, p]] = M[[p, k]]
        paso = {
            "paso_k": k + 1,
            "columna": k + 1,
            "valor_pivote": float(M[k, k]),
            "hubo_intercambio": bool(hubo),
            "filas_intercambiadas": (k + 1, p + 1) if hubo else None,
            "multiplicadores": [],
        }
        for i in range(k + 1, n):
            m = M[i, k] / M[k, k]
            M[i, k:] = M[i, k:] - m * M[k, k:]
            M[i, k] = 0.0
            paso["multiplicadores"].append({"fila_afectada": i + 1, "fila_pivote": k + 1, "factor_m": float(m)})
        historial.append(paso)
        matrices_etapas.append(M.copy())

    if abs(M[n - 1, n - 1]) < umbral:
        return {
            "exito": False,
            "mensaje": (f"Matriz singular: el último pivote es {abs(M[n - 1, n - 1]):.2e} (< {umbral:.1e}). "
                        "El sistema no tiene solución única."),
            "historial_pasos": historial,
        }

    x = np.zeros(n)
    x[n - 1] = M[n - 1, n] / M[n - 1, n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = (M[i, n] - M[i, i + 1:n] @ x[i + 1:n]) / M[i, i]

    r = A0 @ x - b0
    nb = float(np.max(np.abs(b0)))
    cond = evaluar_condicionamiento(A0)
    return {
        "exito": True,
        "mensaje": "Solución obtenida.",
        "x": x,
        "historial_pasos": historial,
        "matriz_triangular": M.copy(),
        "matrices_etapas": matrices_etapas,
        "residuo": r,
        "norma_residuo_2": float(np.linalg.norm(r, 2)),
        "norma_residuo_inf": float(np.linalg.norm(r, np.inf)),
        "residuo_relativo": float(np.linalg.norm(r, np.inf) / nb) if nb > 0 else float(np.linalg.norm(r, np.inf)),
        "condicion_A": cond["kappa"],
        "estado_condicion": cond["estado"],
        "advertencia_condicion": cond["advertencia"],
    }


def comparar_con_libreria_lineal(A, b, x_propio) -> dict:
    """Contraste con LAPACK (scipy.linalg.solve; numpy.linalg.solve si SciPy no está disponible)."""
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float).reshape(-1)
    try:
        from scipy.linalg import solve as _solve
        nombre = "scipy.linalg.solve (LAPACK)"
    except Exception:  # pragma: no cover
        _solve = np.linalg.solve
        nombre = "numpy.linalg.solve (LAPACK)"
    x_lib = np.asarray(_solve(A, b), dtype=float)
    dif = float(np.max(np.abs(np.asarray(x_propio, dtype=float) - x_lib)))
    return {
        "libreria_usada": nombre,
        "x_libreria": x_lib,
        "max_diferencia_absoluta": dif,
        "interpretacion": (
            "La solución propia coincide con la de la biblioteca hasta el redondeo de punto flotante."
            if dif <= 1e-9 * max(1.0, float(np.max(np.abs(x_lib)))) else
            "ATENCIÓN: hay una diferencia apreciable respecto a la biblioteca; revisar el condicionamiento de A."
        ),
    }
