"""Hidráulica del canal rectangular: profundidad crítica y carga del agua.

Flujo crítico en sección rectangular (ancho b, caudal Q, caudal unitario q = Q/b):
    Fr = V / sqrt(g y) = 1  y  Q = b y V   =>   Q^2 = g b^2 y^3   =>   y_c = (Q^2 / (g b^2))^(1/3) = (q^2/g)^(1/3).
Ecuación escalar:  f(y) = Q^2 - g b^2 y^3 = 0 ,  f'(y) = -3 g b^2 y^2.
Dimensiones: [Q^2] = m^6/s^2 ; [g b^2 y^3] = (m/s^2)(m^2)(m^3) = m^6/s^2.  OK.

Formulación como SISTEMA 2x2 en (y, V) (no se inventan incógnitas: son las dos condiciones físicas del
flujo crítico):
    f1 = V^2 - g y = 0         (Fr = 1)
    f2 = b y V - Q = 0         (continuidad)
Se escalan para que las tolerancias sean adimensionales:  F1 = f1/(g y_ref),  F2 = f2/Q,
con y_ref = aproximación inicial de y (NO la solución).

y_c es un parámetro del régimen de flujo; NO garantiza borde libre, estabilidad ni seguridad del canal,
y no es el tirante normal ni el de operación.
"""
from __future__ import annotations

import math

import numpy as np

ALPHA_RANGO_ESCENARIO = (0.05, 0.30)   # rango de trabajo del escenario académico (supuesto, no norma)


def caudal_derivado(q_total: float, alpha: float) -> float:
    if not (math.isfinite(q_total) and q_total > 0):
        raise ValueError("El caudal total debe ser un número positivo.")
    if not (math.isfinite(alpha) and 0 < alpha <= 1):
        raise ValueError("La fracción derivada debe estar en (0, 1].")
    return alpha * q_total


def validar_parametros(Q: float, b: float, g: float = 9.81) -> None:
    for nombre, v in (("Q_d", Q), ("ancho b", b), ("gravedad g", g)):
        if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
            raise ValueError(f"{nombre} debe ser un número positivo y finito.")


def profundidad_critica_analitica(Q: float, b: float, g: float = 9.81) -> float:
    validar_parametros(Q, b, g)
    return (Q ** 2 / (g * b ** 2)) ** (1.0 / 3.0)


# ---- ecuación escalar (la propuesta del enunciado) ----
def f_escalar(y: float, Q: float, b: float, g: float = 9.81) -> float:
    return Q ** 2 - g * b ** 2 * y ** 3


def df_escalar(y: float, b: float, g: float = 9.81) -> float:
    return -3.0 * g * b ** 2 * y ** 2


def sistema_escalar(Q, b, g=9.81):
    """Devuelve (F, J) para usar el Newton de sistemas con n = 1 (mismo algoritmo, caso 1x1)."""
    F = lambda y: np.array([f_escalar(y, Q, b, g)])
    J = lambda y: np.array([[df_escalar(y, b, g)]])
    return F, J


# ---- sistema 2x2 (y, V) escalado ----
def sistema_critico(Q, b, g, y_ref):
    """Devuelve (F, J, G) del sistema escalado en (y, V). G es la iteración de punto fijo."""
    def F(y, V):
        return np.array([(V ** 2 - g * y) / (g * y_ref), (b * y * V - Q) / Q])

    def J(y, V):
        return np.array([[-1.0 / y_ref, 2.0 * V / (g * y_ref)],
                         [b * V / Q, b * y / Q]])

    def G(y, V):
        # y = Q / (b V)   (continuidad) ;  V = sqrt(g y)   (Fr = 1);  ambos con el vector ANTERIOR
        return np.array([Q / (b * V), math.sqrt(g * y)])

    return F, J, G


def aproximacion_inicial(Q, b, y0: float) -> list[float]:
    """(y0, V0) con V0 de continuidad Q = b y0 V0. y0 debe ser positivo."""
    if not (math.isfinite(y0) and y0 > 0):
        raise ValueError("La profundidad inicial debe ser positiva.")
    return [y0, Q / (b * y0)]


def dominio_positivo(x) -> bool:
    return bool(np.all(np.asarray(x) > 0) and np.all(np.isfinite(x)))


def comprobaciones_hidraulicas(y: float, Q: float, b: float, g: float = 9.81) -> dict:
    A = b * y
    V = Q / A
    Fr = V / math.sqrt(g * y)
    q = Q / b
    return {
        "area_mojada_m2": A, "velocidad_ms": V, "froude": Fr, "caudal_unitario_m2s": q,
        "energia_especifica_m": y + V ** 2 / (2 * g), "energia_minima_teorica_m": 1.5 * y,
        "y_analitica_m": profundidad_critica_analitica(Q, b, g),
        "diferencia_con_analitica_m": y - profundidad_critica_analitica(Q, b, g),
        "residual_Q_m3s": b * y * V - Q,
    }


# ---- carga del agua ----
def peso_agua_por_metro_kNm(y: float, b: float, rho: float = 1000.0, g: float = 9.81) -> dict:
    """w = rho g A  [N/m] -> kN/m. Solo peso del agua con tirante y (no incluye canal, armadura ni sobrecargas)."""
    for nombre, v in (("y", y), ("b", b), ("rho", rho), ("g", g)):
        if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
            raise ValueError(f"{nombre} debe ser positivo y finito.")
    A = b * y
    w_Nm = rho * g * A
    return {"area_m2": A, "w_N_por_m": w_Nm, "w_kN_por_m": w_Nm / 1000.0}


def carga_en_tramo_kN(w_kN_m: float, longitud_m: float) -> float:
    """Peso total del agua sobre un tramo apoyado de longitud ``longitud_m`` [kN]."""
    if not (math.isfinite(longitud_m) and longitud_m > 0):
        raise ValueError("La longitud del tramo debe ser positiva.")
    return w_kN_m * longitud_m
