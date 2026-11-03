"""Pestaña 4 · Newton (diferencias divididas) y comparación con spline cúbico, sobre los mismos datos que Lagrange."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from modulos.diferencias_divididas import agregar_nodo_newton, interpolacion_newton
from modulos.lagrange import lagrange_interpolacion
from modulos.metricas import metricas_error
from modulos.spline import spline_cubico_natural, verificar_monotonia

from .. import componentes as ui
from .. import datos_caso as dc
from .. import estado, graficas
from ..config import textos

METODOS = ["Lagrange", "Newton", "Spline cúbico natural"]


def render() -> None:
    ui.cabecera_tab("newton")
    datos = dc.datos_activos()
    if not datos.get("ok"):
        st.info("Los nodos se configuran en la pestaña 3. Corríjalos allí para comparar los métodos.")
        return
    h, Q = datos["h"], datos["Q"]
    hmin, hmax = min(h), max(h)
    h_c = float(st.session_state.get("h_consulta", (hmin + hmax) / 2))
    st.markdown(f"**Mismos datos que la pestaña 3** ({datos['modo']}): {len(h)} nodos, nivel consultado h = **{h_c:.4f} m**, "
                f"{len(datos['validacion'])} observación(es) de validación. Para cambiarlos, use la pestaña 3: así los tres métodos "
                "siempre se comparan con idénticos nodos y validación.")

    entradas = {"h": [round(x, 12) for x in h], "Q": [round(x, 12) for x in Q], "h_c": h_c}

    def calcular():
        return {"newton": interpolacion_newton(h, Q, h_c), "lagrange": lagrange_interpolacion(h, Q, h_c), "spline": spline_cubico_natural(h, Q)}

    res = ui.ejecutar("newton", entradas, calcular, "Calcular Newton y comparar")
    if not res:
        return
    d = res["datos"]
    nw, lag, sp = d["newton"], d["lagrange"], d["spline"]
    for r in (nw, lag, sp):
        if not r["exito"]:
            st.error(r["mensaje"])
            return
    vig = ui.vigente(res, entradas)

    # ------------------------------------------------------------------ Newton
    st.markdown("#### Diferencias divididas de Newton")
    st.latex(r"f[x_i,\dots,x_{i+k}]=\frac{f[x_{i+1},\dots,x_{i+k}]-f[x_i,\dots,x_{i+k-1}]}{x_{i+k}-x_i},\qquad "
             r"P_n(h)=a_0+\sum_{k=1}^{n}a_k\prod_{j=0}^{k-1}(h-h_j)")
    T = nw["tabla_completa"]
    n = len(h)
    tabla = {"i": list(range(n)), "h_i (m)": [f"{x:.5f}" for x in h], "Q_i = f[x_i]": [f"{T[i, 0]:.6f}" for i in range(n)]}
    for j in range(1, n):
        tabla[f"Orden {j}"] = [f"{T[i, j]:.6g}" if i + j < n else "" for i in range(n)]
    ui.tabla(pd.DataFrame(tabla))
    coef = nw["coeficientes_newton"]
    ui.tabla(pd.DataFrame({"k": range(n), "Coeficiente": [f"a_{k} = f[x_0..x_{k}]" for k in range(n)], "Valor": coef}).round(8))
    st.code("P(h) = " + nw["expresion_newton_str"], language="text")
    with st.expander("Forma canónica expandida"):
        st.code("P(h) = " + nw["expresion_expandida_str"], language="text")
    st.caption(f"Evaluación con el esquema anidado de Horner: P({h_c:.4f}) = {nw['valor_evaluado']:.6f} m³/s.")
    if nw["extrapolando"]:
        st.markdown(f'<div class="caja-error"><b>Extrapolación.</b> {nw["advertencia_extrapolacion"]}</div>', unsafe_allow_html=True)

    # ------------------------------------------------------------------ nodo adicional
    with st.expander("Incorporar un nodo adicional (didáctico)"):
        st.markdown("Newton es **acumulativo**: al agregar un nodo los coeficientes a₀…aₙ **no cambian** y solo aparece un coeficiente nuevo; "
                    "en Lagrange habría que recalcular todas las bases. El nodo adicional se usa **solo aquí**: la comparación de los tres "
                    "métodos de más abajo sigue usando los nodos originales.")
        c1, c2 = st.columns(2)
        h_x = c1.number_input("h del nodo adicional (m)", min_value=0.0, value=None, format="%.4f", key="nw_hx", placeholder="p. ej. 2.59")
        q_x = c2.number_input("Q del nodo adicional (m³/s)", min_value=0.0, value=None, format="%.4f", key="nw_qx",
                              placeholder="valor real de la curva de descarga")
        st.caption("No se propone un valor por defecto: inventar un caudal sería fabricar un dato. Ingrese un par nivel–caudal real.")
        if h_x is not None and q_x is not None:
            if any(abs(h_x - x) < 1e-9 for x in h):
                st.error("Ese nivel ya es un nodo: los nodos repetidos no están permitidos.")
            else:
                ex = agregar_nodo_newton(h, Q, h_x, q_x, h_c)
                if not ex["exito"]:
                    st.error(ex["mensaje"])
                else:
                    ca = ex["antes"]["coeficientes_newton"]
                    cd = ex["despues"]["coeficientes_newton"]
                    ui.tabla(pd.DataFrame({"k": range(len(cd)), "a_k antes": list(ca) + [None], "a_k después": cd}).round(8))
                    st.markdown(f"- Coeficientes previos conservados: **{'sí' if ex['coeficientes_previos_conservados'] else 'NO'}**.\n"
                                f"- Coeficiente nuevo a_{len(cd) - 1} = {ex['coeficiente_nuevo']:.6g}.\n"
                                f"- Estimación en h = {h_c:.4f} m: {ex['antes']['valor_evaluado']:.6f} → {ex['despues']['valor_evaluado']:.6f} m³/s "
                                f"(corrección {ex['correccion_en_x_eval']:+.4e}).")
                    if ex["despues"]["extrapolando"]:
                        st.warning(ex["despues"]["advertencia_extrapolacion"])

    # ------------------------------------------------------------------ comparación
    st.markdown("#### Comparación: Lagrange · Newton · Spline (mismos nodos)")
    st.markdown("**Lagrange y Newton representan el mismo polinomio** cuando usan los mismos nodos; solo cambia la forma de escribirlo "
                "y de calcularlo, y las diferencias son redondeo. El **spline cúbico natural** (S″ = 0 en los extremos) es otra cosa: "
                "una interpolación **por tramos** de clase C².")
    f_lag, f_new, f_spl = lag["P_poly"], nw["P_poly"], sp["eval_func"]
    curvas = {"Lagrange": f_lag, "Newton": f_new, "Spline cúbico natural": f_spl}
    hh = np.linspace(hmin, hmax, 400)
    dif_ln = float(np.max(np.abs(f_new(hh) - f_lag(hh))))
    esc = max(1.0, float(np.max(np.abs(Q))))
    st.caption(f"Máx |Newton − Lagrange| sobre el intervalo = {ui.cient(dif_ln, 2)} m³/s ({ui.cient(dif_ln / esc, 1)} relativo al caudal máximo): redondeo de punto flotante.")

    preds = {m: float(f(h_c)) for m, f in curvas.items()}
    ui.tabla(pd.DataFrame([{"Método": m, f"Q(h = {h_c:.4f} m) (m³/s)": v, "Diferencia con Lagrange (m³/s)": v - preds["Lagrange"]} for m, v in preds.items()]).round(6))
    if nw["extrapolando"]:
        st.warning("El nivel consultado está fuera del intervalo: las tres cifras son extrapolaciones y el spline usa el polinomio cúbico de su tramo extremo.")

    vals = datos["validacion"]
    st.markdown("**Predicciones y errores en las observaciones de validación**")
    if not vals:
        st.info("No hay observaciones de validación (agréguelas en la pestaña 3, modo «Mis propios nodos»).")
    else:
        filas = []
        for v in vals:
            fila = {"Obs.": v["id"], "h (m)": v["h_m"], "Q observado (m³/s)": v["Q_m3s"]}
            for m, f in curvas.items():
                q = float(f(v["h_m"]))
                fila[f"{m} (m³/s)"] = q
                fila[f"Error {m} (m³/s)"] = q - v["Q_m3s"]
            filas.append(fila)
        ui.tabla(pd.DataFrame(filas).round(5))
        met = []
        for m, f in curvas.items():
            mt = metricas_error([v["Q_m3s"] for v in vals], [float(f(v["h_m"])) for v in vals])
            met.append({"Método": m, "n": mt["n"], "MAE (m³/s)": mt["MAE"], "RMSE (m³/s)": mt["RMSE"], "Error máximo (m³/s)": mt["error_max"]})
        ui.tabla(pd.DataFrame(met).round(5))
        if len(vals) < 3:
            st.caption(f"Solo hay {len(vals)} observación(es) de validación: MAE, RMSE y error máximo coinciden o son poco representativos. "
                       "No se simulan observaciones adicionales y **no se declara un método ganador** con tan pocos datos.")

    mono = []
    for m, f in curvas.items():
        mo = verificar_monotonia(f, hmin, hmax)
        mono.append({"Representación": m, "¿Creciente en todo el intervalo?": "sí" if mo["creciente"] else "NO",
                     "Tramos decrecientes (malla de 2001 puntos)": mo["n_tramos_decrecientes"]})
    ui.tabla(pd.DataFrame(mono))
    st.caption("La monotonía se comprueba numéricamente con estos datos; no se asume. Una curva de descarga físicamente debería ser creciente.")

    ui.grafica(graficas.fig_interpolacion(h, Q, curvas, h_c, preds["Newton"], vals, "Lagrange, Newton y spline sobre los mismos nodos"), "fig_comp")
    ui.grafica(graficas.fig_diferencias(hh, {"Newton − Lagrange": f_new(hh) - f_lag(hh), "Spline − Lagrange": f_spl(hh) - f_lag(hh)}), "fig_dif")

    st.markdown("#### Interpretación y límites")
    st.markdown(
        "- Newton y Lagrange coinciden hasta el redondeo; la diferencia práctica está en el cálculo: Newton permite añadir nodos sin rehacer lo anterior.\n"
        "- El spline sigue localmente los datos y evita las oscilaciones de un polinomio de grado alto, pero eso se **comprueba** (tabla de monotonía), "
        "no se da por sentado.\n"
        "- Los nodos y la validación son los mismos para los tres métodos: no se eligieron para favorecer a ninguno.\n"
        "- Los nodos del caso son preliminares y la validación es una sola lectura provisional: estas métricas ilustran el procedimiento, no certifican la curva de descarga.")

    st.markdown("#### Publicar al flujo integrado")
    metodo = st.selectbox("Estimación a usar como $Q_{total}$", ["Newton (= Lagrange)", "Spline cúbico natural"], key="pub4_met")
    q_pub = preds["Newton"] if metodo.startswith("Newton") else preds["Spline cúbico natural"]
    puede = vig and not nw["extrapolando"] and q_pub > 0
    if st.button(f"Usar {q_pub:.3f} m³/s como $Q_{{total}}$", key="pub_q4", disabled=not puede, type="primary"):
        estado.publicar("q_total", q_pub, "m³/s", f"Pestaña 4 · {metodo.split(' (')[0]}", {"h": h_c}, f"h = {h_c:.4f} m · nodos: {datos.get('procedencia', '—')}")
        estado.invalidar("q_d")
        st.success("$Q_{total}$ publicado. La pestaña 2 lo usará para calcular $Q_d$ y la profundidad crítica.")
    if not vig:
        st.caption("Recalcule para poder publicar (las entradas cambiaron).")
    elif not puede:
        st.caption("No se puede publicar: el nivel está fuera del intervalo de los nodos o el caudal no es positivo.")
