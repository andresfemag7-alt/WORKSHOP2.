"""Armadura plana: equilibrio estático por el método de los nudos como sistema lineal A x = b.

Convenciones (explícitas):
  * Ejes: x a la derecha, y hacia arriba. Cargas hacia abajo = Fy negativo.
  * Fuerza axial de una barra: POSITIVA = TRACCIÓN, NEGATIVA = COMPRESIÓN.
  * Una barra i-j en tracción jala al nudo i hacia j: aporta  +u_ij  al nudo i  y  -u_ij  al nudo j.
  * Para cada nudo: sum(T_k u_k) + R + P_ext = 0   =>   A x = -P_ext.
  * Incógnitas: fuerzas de las m barras y las r componentes de reacción. Determinada si m + r = 2 j.

Escenario académico (ver docs): armadura Warren de 5 nudos y 7 barras que soporta el canal
    D(L/4, H) ----- E(3L/4, H)        cargas = peso del agua del tramo, mitad en D y mitad en E
    /  \\           /  \\
   A -- B ------- C                  apoyo fijo en A (Rx, Ry) y apoyo móvil en C (Ry)
Solo se considera el PESO DEL AGUA: no hay peso propio de canal/armadura, ni sobrecarga, ni factores de seguridad.
"""
from __future__ import annotations

import math

import numpy as np

from ..sistemas_lineales import gauss_pivoteo_parcial


def construir_sistema_armadura(nodos: dict, barras: list, apoyos: list, cargas: dict) -> dict:
    """nodos {nombre: (x, y)}; barras [(nombre, nudo_i, nudo_j)]; apoyos [(nudo, 'x'|'y')];
    cargas {nudo: (Fx, Fy)} [kN, positivo = hacia +x / +y]."""
    nombres = list(nodos)
    idx = {n: i for i, n in enumerate(nombres)}
    m, r, j = len(barras), len(apoyos), len(nombres)
    if m + r != 2 * j:
        raise ValueError(
            f"Armadura no determinada por este método: {m} barras + {r} reacciones = {m + r} incógnitas, "
            f"pero hay {2 * j} ecuaciones (2 por nudo).")
    A = np.zeros((2 * j, m + r))
    longitudes = {}
    for k, (nom, a, b) in enumerate(barras):
        if a not in idx or b not in idx:
            raise ValueError(f"La barra {nom} usa un nudo inexistente.")
        dx = nodos[b][0] - nodos[a][0]
        dy = nodos[b][1] - nodos[a][1]
        L = math.hypot(dx, dy)
        if L <= 0:
            raise ValueError(f"La barra {nom} tiene longitud cero.")
        longitudes[nom] = L
        ux, uy = dx / L, dy / L
        A[2 * idx[a], k] += ux
        A[2 * idx[a] + 1, k] += uy
        A[2 * idx[b], k] -= ux
        A[2 * idx[b] + 1, k] -= uy
    etiquetas = [nom for nom, _, _ in barras]
    for q, (nudo, eje) in enumerate(apoyos):
        col = m + q
        A[2 * idx[nudo] + (0 if eje == "x" else 1), col] = 1.0
        etiquetas.append(f"R{eje}_{nudo}")
    b_vec = np.zeros(2 * j)
    for nudo, (fx, fy) in cargas.items():
        b_vec[2 * idx[nudo]] -= fx
        b_vec[2 * idx[nudo] + 1] -= fy
    filas = [f"{n}:{e}" for n in nombres for e in ("Fx", "Fy")]
    return {"A": A, "b": b_vec, "incognitas": etiquetas, "ecuaciones": filas,
            "n_barras": m, "n_reacciones": r, "longitudes": longitudes,
            "rango": int(np.linalg.matrix_rank(A))}


def armadura_warren_canal(L: float, H: float, W_total_kN: float) -> dict:
    """Escenario del caso: luz L [m], altura H [m], peso del agua W_total [kN] sobre el tramo (50/50 en D y E)."""
    if not (L > 0 and H > 0 and math.isfinite(L) and math.isfinite(H)):
        raise ValueError("La luz L y la altura H deben ser positivas.")
    if not (math.isfinite(W_total_kN) and W_total_kN >= 0):
        raise ValueError("La carga total debe ser un número finito no negativo.")
    nodos = {"A": (0.0, 0.0), "B": (L / 2, 0.0), "C": (L, 0.0), "D": (L / 4, H), "E": (3 * L / 4, H)}
    barras = [("AB", "A", "B"), ("BC", "B", "C"), ("AD", "A", "D"), ("DB", "D", "B"),
              ("BE", "B", "E"), ("EC", "E", "C"), ("DE", "D", "E")]
    apoyos = [("A", "x"), ("A", "y"), ("C", "y")]
    cargas = {"D": (0.0, -W_total_kN / 2), "E": (0.0, -W_total_kN / 2)}
    sis = construir_sistema_armadura(nodos, barras, apoyos, cargas)
    sis.update({"nodos": nodos, "barras": barras, "apoyos": apoyos, "cargas": cargas,
                "L": L, "H": H, "W_total_kN": W_total_kN})
    return sis


def resolver_armadura(sistema: dict) -> dict:
    """Resuelve con la eliminación de Gauss del notebook 1 y verifica el equilibrio global."""
    res = gauss_pivoteo_parcial(sistema["A"], sistema["b"])
    if not res["exito"]:
        return {"exito": False, "mensaje": "No se pudo resolver el equilibrio: " + res["mensaje"], "gauss": res}
    x = res["x"]
    m = sistema["n_barras"]
    fuerzas = {nom: float(x[k]) for k, (nom, _, _) in enumerate(sistema["barras"])}
    reacciones = {sistema["incognitas"][m + q]: float(x[m + q]) for q in range(sistema["n_reacciones"])}
    escala = max(1e-12, max(abs(v) for v in fuerzas.values()))
    tol = 1e-9 * max(1.0, escala)
    estado = {n: ("tracción" if f > tol else "compresión" if f < -tol else "fuerza nula") for n, f in fuerzas.items()}
    eq = verificar_equilibrio_global(sistema, reacciones)
    return {"exito": True, "mensaje": "Equilibrio resuelto.", "gauss": res, "x": x,
            "fuerzas_kN": fuerzas, "estado_barras": estado, "reacciones_kN": reacciones, "equilibrio_global": eq}


def verificar_equilibrio_global(sistema: dict, reacciones: dict) -> dict:
    """Suma de fuerzas y de momentos respecto al origen entre cargas y reacciones (independiente de A x = b)."""
    nodos = sistema["nodos"]
    fx = fy = mom = 0.0
    for nudo, (cx, cy) in sistema["cargas"].items():
        x, y = nodos[nudo]
        fx += cx; fy += cy; mom += x * cy - y * cx
    for (nudo, eje) in sistema["apoyos"]:
        R = reacciones[f"R{eje}_{nudo}"]
        x, y = nodos[nudo]
        if eje == "x":
            fx += R; mom += -y * R
        else:
            fy += R; mom += x * R
    esc = max(1.0, abs(sistema["W_total_kN"]) if "W_total_kN" in sistema else 1.0)
    return {"suma_Fx_kN": fx, "suma_Fy_kN": fy, "suma_M_kNm": mom,
            "cumple": bool(abs(fx) < 1e-9 * esc and abs(fy) < 1e-9 * esc and abs(mom) < 1e-8 * esc * max(1.0, sistema.get("L", 1.0)))}


def solucion_analitica_warren(L: float, H: float, W_total_kN: float) -> dict:
    """Método de los nudos a mano (simetría) para contrastar la solución numérica."""
    P = W_total_kN / 2.0
    d1 = math.hypot(L / 4, H)
    T = P * (L / 4) / H
    return {"AB": T, "BC": T, "DE": -T, "AD": -P * d1 / H, "EC": -P * d1 / H, "DB": 0.0, "BE": 0.0,
            "Ay": P, "Cy": P, "Ax": 0.0}


def auditar_matriz_gemini(theta_rad: float, P_kN: float) -> dict:
    """Contrasta la matriz 3x3 propuesta por Gemini con un triángulo de referencia bien planteado.

    Gemini:  [[cos, cos, -1], [sin, -sin, 0], [0, 0, 1]] [T_AC, T_BC, T_AB] = [0, P, 0]
    Referencia: triángulo A(0,0), B(2a,0), C(a,h) con tan(theta) = h/a, carga P hacia abajo en C,
    apoyo fijo en A y móvil en B  (6 incógnitas = 6 ecuaciones). Solución analítica (compresión < 0):
        T_AC = T_BC = -P / (2 sin theta),   T_AB = +P / (2 tan theta),   Ay = By = P/2.
    Problemas de la matriz de Gemini: (i) la fila 3 (T_AB = 0) no es una ecuación de equilibrio de ningún nudo;
    (ii) no incluye reacciones; (iii) con T_AB = 0 se viola el equilibrio horizontal del apoyo A.
    """
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    Mg = np.array([[c, c, -1.0], [s, -s, 0.0], [0.0, 0.0, 1.0]])
    bg = np.array([0.0, P_kN, 0.0])
    xg = np.linalg.solve(Mg, bg)
    a = 1.0
    h = a * math.tan(theta_rad)
    sis = construir_sistema_armadura(
        {"A": (0.0, 0.0), "B": (2 * a, 0.0), "C": (a, h)},
        [("AB", "A", "B"), ("AC", "A", "C"), ("BC", "B", "C")],
        [("A", "x"), ("A", "y"), ("B", "y")], {"C": (0.0, -P_kN)})
    x = np.linalg.solve(sis["A"], sis["b"])
    ref = {"AB": float(x[0]), "AC": float(x[1]), "BC": float(x[2])}
    analitica = {"AB": P_kN / (2 * math.tan(theta_rad)),
                 "AC": -P_kN / (2 * math.sin(theta_rad)), "BC": -P_kN / (2 * math.sin(theta_rad))}
    return {"gemini": {"T_AC": float(xg[0]), "T_BC": float(xg[1]), "T_AB": float(xg[2])},
            "referencia_numerica": ref, "referencia_analitica": analitica}
