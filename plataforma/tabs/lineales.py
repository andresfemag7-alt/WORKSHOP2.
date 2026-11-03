"""Pestaña 1 · Sistemas lineales: equilibrio estático de la armadura que soporta el canal."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import streamlit as st

from modulos.caso import estructura as es
from modulos.caso import hidraulica as hy
from modulos.sistemas_lineales import comparar_con_libreria_lineal, gauss_pivoteo_parcial

from .. import componentes as ui
from .. import estado, graficas
from ..config import textos

DESCRIPCION_ECUACION = {"Fx": "Σ Fx = 0", "Fy": "Σ Fy = 0"}
EJEMPLOS = {
    "Caso 1 · 3×3 con pivote nulo (Clase 07)": ([[0, 2, 3], [4, 6, 7], [2, 1, 6]], [8, -3, 5]),
    "Caso 2 · 2×2 bien condicionado": ([[3, -2], [-1, 4]], [5, 15]),
    "Caso 3 · 4×4 tridiagonal": ([[1, 1, 0, 0], [-1, 2, 1, 0], [0, -1, 2, 1], [0, 0, -1, 2]], [3, 6, 8, 5]),
}
PERSONALIZADO = "Personalizado n×n"


def render() -> None:
    ui.cabecera_tab("lineales")
    modo = st.radio("Modo de trabajo", ["Armadura del caso integrador", "Sistema lineal propio (A·x = b)"],
                    horizontal=True, key="lin_modo")
    if modo.startswith("Armadura"):
        _armadura()
    else:
        _propio()


# ----------------------------------------------------------------------------- armadura del caso
def _armadura() -> None:
    yc_item = estado.obtener("y_c")
    st.markdown("**Esquema del escenario (supuestos académicos).** Armadura Warren de 5 nudos y 7 barras; el canal con agua "
                "se apoya en los nudos superiores D y E (la mitad del peso en cada uno). Apoyo fijo en A, móvil en C. "
                "Solo se considera el **peso del agua**.")
    usar_flujo = False
    if yc_item is not None:
        fuente = st.radio("Origen del peso del agua", ["Desde el flujo integrado (y_c de la pestaña 2)", "Carga manual"],
                          horizontal=True, key="lin_fuente")
        usar_flujo = fuente.startswith("Desde")
    else:
        st.info(textos.MSG_SIN_FLUJO + " Mientras tanto se usa la carga manual.")

    c1, c2, c3 = st.columns(3)
    L = c1.number_input("Luz del tramo L (m)", 0.5, 100.0, 5.0, 0.5, key="lin_L",
                        help="Longitud de canal soportada por la armadura = luz entre apoyos A y C. Supuesto del escenario (propuesta original: 5 m).")
    H = c2.number_input("Altura de la armadura H (m)", 0.2, 50.0, 1.5, 0.1, key="lin_H", help="Supuesto del escenario.")
    rho = c3.number_input("Densidad del agua ρ (kg/m³)", 900.0, 1100.0, 1000.0, 10.0, key="lin_rho",
                          help="Supuesto: agua dulce a ~4–20 °C. Se admite variar por temperatura o sedimentos.")

    filas = [
        {"simbolo": "L", "descripcion": "Luz del tramo soportado", "valor": ui.fmt(L, 2), "unidad": "m",
         "proc": "editado" if L != 5.0 else "supuesto"},
        {"simbolo": "H", "descripcion": "Altura de la armadura", "valor": ui.fmt(H, 2), "unidad": "m",
         "proc": "editado" if H != 1.5 else "supuesto"},
        {"simbolo": "ρ", "descripcion": "Densidad del agua", "valor": ui.fmt(rho, 0), "unidad": "kg/m³",
         "proc": "editado" if rho != 1000.0 else "supuesto"},
    ]
    if usar_flujo:
        yc = yc_item["valor"]
        b = yc_item["entradas"]["b"]
        g = yc_item["entradas"]["g"]
        w = hy.peso_agua_por_metro_kNm(yc, b, rho, g)
        W = hy.carga_en_tramo_kN(w["w_kN_por_m"], L)
        obsoleto = estado.obtener("q_total") and not estado.iguales({"Q": yc_item["entradas"].get("Q_total", -1.0)},
                                                                    {"Q": estado.valor("q_total")})
        if obsoleto:
            st.warning(" El caudal total publicado cambió después de calcular y_c: **y_c está desactualizado**. "
                       "Recalcule la pestaña 2 antes de confiar en esta carga.")
        filas += [
            {"simbolo": "y_c", "descripcion": f"Profundidad crítica (calculada en {yc_item['modulo']} a las {yc_item['hora']})",
             "valor": ui.fmt(yc, 4), "unidad": "m", "proc": "calculado"},
            {"simbolo": "b", "descripcion": "Ancho del canal (de la pestaña 2)", "valor": ui.fmt(b, 2), "unidad": "m", "proc": "calculado"},
            {"simbolo": "A", "descripcion": "Área mojada A = b·y_c", "valor": ui.fmt(w["area_m2"], 4), "unidad": "m²", "proc": "calculado"},
            {"simbolo": "w", "descripcion": "Peso del agua por metro, w = ρ·g·A", "valor": ui.fmt(w["w_kN_por_m"], 3), "unidad": "kN/m", "proc": "calculado"},
            {"simbolo": "W", "descripcion": "Peso del agua en el tramo, W = w·L", "valor": ui.fmt(W, 3), "unidad": "kN", "proc": "calculado"},
        ]
    else:
        W = st.number_input("Peso total del agua sobre el tramo W (kN)", 0.0, 1e6, 200.0, 10.0, key="lin_W",
                            help="Modo manual e independiente de las otras pestañas. W = w·L, con w = ρ·g·b·y.")
        filas.append({"simbolo": "W", "descripcion": "Peso del agua en el tramo (manual)", "valor": ui.fmt(W, 3), "unidad": "kN", "proc": "editado"})
    ui.tabla_variables(filas)
    if usar_flujo:
        st.caption("Cadena de transferencia: w = ρ·g·b·y_c [N/m → kN/m]; W = w·L [kN] (carga **tributaria** del tramo, no carga de diseño); "
                   "reparto 50 % en D y 50 % en E por simetría del apoyo del canal.")

    entradas = {"L": L, "H": H, "W": W}

    def calcular():
        try:
            sis = es.armadura_warren_canal(L, H, W)
        except ValueError as exc:
            return {"error": str(exc)}
        return {"sis": sis, "res": es.resolver_armadura(sis)}

    res = ui.ejecutar("lin_arm", entradas, calcular, "Resolver equilibrio")
    if not res:
        return
    d = res["datos"]
    if "error" in d:
        st.error(d["error"])
        return
    sis, r = d["sis"], d["res"]
    if not r["exito"]:
        st.error(r["mensaje"])
        return
    if W == 0:
        st.info("Con W = 0 todas las fuerzas son nulas: es el resultado correcto del modelo.")

    st.markdown("#### Sistema de equilibrio A·x = b")
    cA, cB = st.columns([3, 2])
    with cA:
        etq = sis["incognitas"]
        dfA = pd.DataFrame(sis["A"], columns=etq)
        dfA.insert(0, "Ecuación", [f"{e.split(':')[0]}: {DESCRIPCION_ECUACION[e.split(':')[1]]}" for e in sis["ecuaciones"]])
        ui.tabla(dfA.round(4))
    with cB:
        dfb = pd.DataFrame({"Ecuación": dfA["Ecuación"], "b = −P_ext (kN)": sis["b"]})
        ui.tabla(dfb.round(4))
        st.caption("Incógnitas x: fuerzas axiales de las 7 barras (kN; **+ tracción, − compresión**) y 3 reacciones (kN). "
                   f"10 ecuaciones, 10 incógnitas, rango = {sis['rango']} → armadura **estáticamente determinada y estable**.")

    mostrar_gauss(r["gauss"], sis["incognitas"], "arm")

    st.markdown("#### Resultados")
    barras = pd.DataFrame([{"Barra": n, "Nudos": f"{a}–{b_}", "Longitud (m)": sis["longitudes"][n],
                            "Fuerza axial (kN)": r["fuerzas_kN"][n], "Estado": r["estado_barras"][n]} for n, a, b_ in sis["barras"]])
    c1, c2 = st.columns([3, 2])
    with c1:
        ui.tabla(barras.round(4))
    with c2:
        ui.tabla(pd.DataFrame([{"Reacción": k, "Valor (kN)": v} for k, v in r["reacciones_kN"].items()]).round(4))
    ui.grafica(graficas.fig_armadura(sis, r), "fig_armadura")

    g = r["gauss"]
    eq = r["equilibrio_global"]
    st.markdown("#### Comprobaciones")
    ref = es.solucion_analitica_warren(L, H, W)
    dif = max(abs(r["fuerzas_kN"][k] - ref[k]) for k in r["fuerzas_kN"])
    comp = comparar_con_libreria_lineal(sis["A"], sis["b"], g["x"])
    ui.tabla(pd.DataFrame([
        {"Comprobación": "Residual ‖A·x − b‖∞ (kN)", "Valor": f"{ui.cient(g['norma_residuo_inf'], 2)}", "Lectura": "≈ 0: se satisface cada ecuación de equilibrio"},
        {"Comprobación": "Σ Fx, Σ Fy global (kN)", "Valor": f"{ui.cient(eq['suma_Fx_kN'], 1)}, {ui.cient(eq['suma_Fy_kN'], 1)}", "Lectura": "Cargas + reacciones en equilibrio"},
        {"Comprobación": "Σ M respecto al origen (kN·m)", "Valor": f"{ui.cient(eq['suma_M_kNm'], 1)}", "Lectura": "Equilibrio de momentos"},
        {"Comprobación": "Máx |x − solución analítica| (kN)", "Valor": f"{ui.cient(dif, 1)}", "Lectura": "Método de los nudos a mano (simetría)"},
        {"Comprobación": f"Máx |x − {comp['libreria_usada']}|", "Valor": f"{ui.cient(comp['max_diferencia_absoluta'], 1)}", "Lectura": comp["interpretacion"]},
        {"Comprobación": "κ₂(A)", "Valor": f"{ui.cient(g['condicion_A'], 2)}", "Lectura": f"{g['estado_condicion']}. {g['advertencia_condicion']}"},
    ]))
    st.markdown("#### Interpretación")
    ab, bc = r["fuerzas_kN"]["AB"], r["fuerzas_kN"]["DE"]
    st.markdown(
        f"- Las barras **inferiores (AB, BC)** trabajan en **tracción** (~{ab:.1f} kN) y la **cuerda superior DE** en **compresión** "
        f"(~{abs(bc):.1f} kN), como en una viga biapoyada; las diagonales AD y EC están en compresión y las barras DB y BE resultan de fuerza nula para esta carga simétrica.\n"
        f"- Cada apoyo vertical toma W/2 = {W / 2:.1f} kN y la reacción horizontal es nula (sin cargas horizontales).\n"
        "- **Límites:** es solo el peso del agua. No incluye peso propio del canal y de la armadura, sobrecargas, viento, sismo, pandeo de barras en compresión, "
        "ni factores de seguridad: **no es una verificación estructural**.")

    with st.expander("Auditoría: por qué no se usó la matriz 3×3 de la propuesta inicial"):
        theta = st.slider("Ángulo θ del triángulo de referencia (°)", 15, 75, 30, key="aud_theta")
        a = es.auditar_matriz_gemini(math.radians(theta), 100.0)
        ui.tabla(pd.DataFrame([
            {"Barra": "AB", "Propuesta (T_AB)": a["gemini"]["T_AB"], "Triángulo bien planteado (numérico)": a["referencia_numerica"]["AB"], "Analítica": a["referencia_analitica"]["AB"]},
            {"Barra": "AC", "Propuesta (T_AC)": a["gemini"]["T_AC"], "Triángulo bien planteado (numérico)": a["referencia_numerica"]["AC"], "Analítica": a["referencia_analitica"]["AC"]},
            {"Barra": "BC", "Propuesta (T_BC)": a["gemini"]["T_BC"], "Triángulo bien planteado (numérico)": a["referencia_numerica"]["BC"], "Analítica": a["referencia_analitica"]["BC"]},
        ]).round(4))
        st.markdown("La matriz propuesta no es una armadura determinada: su 3.ª fila (T_AB = 0) no corresponde a ningún equilibrio de nudo, "
                    "omite las reacciones y obliga a T_AB = 0, lo que viola el equilibrio horizontal en A. Resultados con P = 100 kN.")


# ----------------------------------------------------------------------------- sistema propio
def _propio() -> None:
    st.markdown("Resuelva **cualquier** sistema A·x = b de forma independiente (no depende de las otras pestañas).")
    preset = st.selectbox("Sistema", list(EJEMPLOS) + [PERSONALIZADO], key="lin_preset")
    if preset == PERSONALIZADO:
        n = int(st.number_input("Orden n", 2, 8, 3, 1, key="lin_n"))
        A0 = (2 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)).tolist()
        b0 = [1.0] * n
    else:
        A0, b0 = EJEMPLOS[preset]
        n = len(b0)
    cols = [f"x{i + 1}" for i in range(n)]
    st.caption("Edite los coeficientes; los cambios no se pierden al recalcular.")
    key = f"{preset}_{n}"
    ea = st.data_editor(pd.DataFrame(A0, columns=cols), key=f"ed_A_{key}", num_rows="fixed", hide_index=True, width="stretch")
    eb = st.data_editor(pd.DataFrame({"b": b0}), key=f"ed_b_{key}", num_rows="fixed", hide_index=True, width="stretch")
    A = ea.apply(pd.to_numeric, errors="coerce")
    bb = pd.to_numeric(eb["b"], errors="coerce")
    if A.isna().any(axis=None) or bb.isna().any():
        st.error("Hay celdas vacías o no numéricas en A o en b. Complete todos los valores.")
        return
    A_np, b_np = A.to_numpy(float), bb.to_numpy(float)
    entradas = {"A": A_np.round(12).tolist().__repr__(), "b": b_np.round(12).tolist().__repr__()}
    res = ui.ejecutar("lin_propio", entradas, lambda: gauss_pivoteo_parcial(A_np, b_np), "Resolver sistema")
    if not res:
        return
    g = res["datos"]
    if not g["exito"]:
        st.error(g["mensaje"])
        return
    mostrar_gauss(g, cols, "propio")
    st.markdown("#### Solución")
    ui.tabla(pd.DataFrame({"Variable": cols, "Valor": g["x"], "Residual r_i = (A·x − b)_i": g["residuo"]}).round(10))
    comp = comparar_con_libreria_lineal(A_np, b_np, g["x"])
    ui.tabla(pd.DataFrame([
        {"Diagnóstico": "‖r‖∞ / ‖b‖∞", "Valor": f"{ui.cient(g['residuo_relativo'], 2)}"},
        {"Diagnóstico": "κ₂(A)", "Valor": f"{ui.cient(g['condicion_A'], 3)} — {g['estado_condicion']}"},
        {"Diagnóstico": f"Máx |x − {comp['libreria_usada']}|", "Valor": f"{ui.cient(comp['max_diferencia_absoluta'], 2)}"},
    ]))
    st.caption(g["advertencia_condicion"] + " Un residual pequeño NO garantiza un error pequeño en x si κ(A) es grande.")


# ----------------------------------------------------------------------------- procedimiento
def mostrar_gauss(g: dict, etiquetas: list[str], clave: str) -> None:
    if not g["exito"]:
        st.error(g["mensaje"])
        return
    with st.expander("Procedimiento: pivoteo parcial, multiplicadores y matriz tras cada etapa", expanded=False):
        encab = list(etiquetas) + ["b"]
        st.markdown("Matriz aumentada inicial [A | b]:")
        ui.tabla(pd.DataFrame(g["matrices_etapas"][0], columns=encab).round(4))
        for paso, M in zip(g["historial_pasos"], g["matrices_etapas"][1:]):
            sw = (f"intercambio F{paso['filas_intercambiadas'][0]} ↔ F{paso['filas_intercambiadas'][1]}"
                  if paso["hubo_intercambio"] else "sin intercambio de filas")
            st.markdown(f"**Etapa k = {paso['paso_k']}** — columna {paso['columna']}, pivote = {paso['valor_pivote']:+.4f}, {sw}.")
            if paso["multiplicadores"]:
                ui.tabla(pd.DataFrame([{"Operación": f"F{m['fila_afectada']} ← F{m['fila_afectada']} − ({m['factor_m']:.4f})·F{m['fila_pivote']}",
                                        "m_ik": m["factor_m"]} for m in paso["multiplicadores"]]).round(6))
            ui.tabla(pd.DataFrame(M, columns=encab).round(4))
        st.markdown("**Sustitución regresiva** sobre la matriz triangular [U | c] de la última etapa: "
                    "x_n = c_n / u_nn;  x_i = (c_i − Σ_{j>i} u_ij·x_j) / u_ii.")
