"""Punto fijo multivariable con ACTUALIZACIÓN SIMULTÁNEA: x^(k+1) = G(x^(k)).

Todas las componentes de x^(k+1) se calculan solo con el vector anterior x^(k).
Criterio de parada (Clase 08): ||dx||_inf <= tol_cambio  Y  ||F(x^(k+1))||_inf <= tol_residual.
El cambio entre iteraciones NO es el error verdadero.
"""
from __future__ import annotations

import numpy as np

LIMITE_DIVERGENCIA = 1e12


def punto_fijo_sistemas(G, x0, tol_cambio: float = 1e-4, tol_residual: float = 1e-4,
                        max_iter: int = 100, F=None) -> dict:
    """``G(*x)`` devuelve el nuevo vector; ``F(*x)`` (opcional) devuelve el vector de residuales."""
    try:
        x = np.array(x0, dtype=float).reshape(-1)
    except (TypeError, ValueError):
        return _fallo("La aproximación inicial debe ser numérica.")
    if x.size == 0 or not np.all(np.isfinite(x)):
        return _fallo("La aproximación inicial no puede estar vacía ni contener valores no finitos.")
    if max_iter < 1 or tol_cambio <= 0 or tol_residual <= 0:
        return _fallo("El máximo de iteraciones debe ser >= 1 y las tolerancias deben ser positivas.")

    historial = []
    motivo = f"Se alcanzó el máximo de iteraciones ({max_iter}) sin cumplir el criterio de parada."
    convergio = False
    for k in range(1, max_iter + 1):
        try:
            x_new = np.asarray(G(*x), dtype=float).reshape(-1)
        except (ZeroDivisionError, FloatingPointError, ValueError, OverflowError) as exc:
            motivo = f"Falló la evaluación de G en la iteración {k}: {exc}"
            break
        if x_new.shape != x.shape or not np.all(np.isfinite(x_new)):
            motivo = f"G produjo valores no finitos o de dimensión incorrecta en la iteración {k} (fuera de dominio)."
            break
        cambio = float(np.max(np.abs(x_new - x)))
        if F is not None:
            r = np.asarray(F(*x_new), dtype=float).reshape(-1)
            nr = float(np.max(np.abs(r)))
        else:
            r, nr = np.array([]), None
        historial.append({
            "iteracion": k,
            "x_k": x.copy().tolist(),
            "x_nuevo": x_new.tolist(),
            "norma_cambio": cambio,
            "residual_vector": r.tolist(),
            "norma_residual": nr,
        })
        x = x_new
        if np.max(np.abs(x)) > LIMITE_DIVERGENCIA:
            motivo = f"Divergencia: |x| superó {LIMITE_DIVERGENCIA:.0e} en la iteración {k}."
            break
        if cambio <= tol_cambio and (nr is None or nr <= tol_residual):
            convergio = True
            motivo = (f"Convergió en {k} iteraciones: ||dx||_inf = {cambio:.2e} <= {tol_cambio:.1e}"
                      + (f" y ||F||_inf = {nr:.2e} <= {tol_residual:.1e}." if nr is not None else "."))
            break
    return {
        "exito": True,
        "convergio": convergio,
        "motivo_parada": motivo,
        "x_sol": x.tolist(),
        "iteraciones": len(historial),
        "historial": historial,
    }


def _fallo(msg: str) -> dict:
    return {"exito": False, "convergio": False, "motivo_parada": msg, "mensaje": msg,
            "x_sol": None, "iteraciones": 0, "historial": []}
