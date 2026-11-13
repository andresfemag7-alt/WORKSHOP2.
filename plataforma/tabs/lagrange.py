"""Pestaña 3 · Interpolación de Lagrange: caudal del río a partir del nivel."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from modulos.caso import datos_rio as dr
from modulos.lagrange import lagrange_interpolacion, texto_polinomio
from modulos.metricas import metricas_error

from .. import componentes as ui
from .. import datos_caso as dc
from .. import estado, graficas


def render() -> None:
    ui.cabecera_tab("lagrange")

    with st.expander("Estación, fuente y limitaciones de los datos", expanded=False):
        e = dr.ESTACION
        st.markdown(f"**{e['id']} — {e['nombre']}** · {e['entidad']}  \n"
                    f"Página oficial: [{e['url']}]({e['url']}) · Hoja técnica: [{e['url_hoja_tecnica']}]({e['url_hoja_tecnica']}) · "
                    f"consultado el {e['fecha_consulta']}.")
        for a in e["advertencias"]:
            st.markdown(f"- {a}")
        st.markdown("Variable independiente: **h** = nivel del río (m). Variable dependiente: **Q** = caudal total (m³/s).")

    st.markdown("#### Nodos de construcción")
    datos = dc.selector_datos()
    if not datos["ok"]:
        st.info("Corrija los nodos indicados arriba para poder interpolar.")
        return
    h, Q = datos["h"], datos["Q"]
    hmin, hmax = min(h), max(h)

    st.markdown("#### Consulta")
    defecto = datos["validacion"][0]["h_m"] if datos["validacion"] else (hmin + hmax) / 2
    h_c = st.number_input("Nivel consultado h (m)", min_value=0.0, value=float(defecto), step=0.01, format="%.4f", key="h_consulta",
                          help=f"Dentro del intervalo de los nodos [{hmin:.4f}, {hmax:.4f}] m para interpolar. Fuera de él es extrapolación.")
    st.caption(f"Equivale a {h_c / dr.FT_A_M:.3f} ft. Intervalo válido de interpolación: {hmin:.4f} – {hmax:.4f} m "
               f"({hmin / dr.FT_A_M:.2f} – {hmax / dr.FT_A_M:.2f} ft).")

    entradas = {"h": [round(x, 12) for x in h], "Q": [round(x, 12) for x in Q], "h_c": h_c}
    res = ui.ejecutar("lagrange", entradas, lambda: lagrange_interpolacion(h, Q, h_c), "Interpolar con Lagrange")
    if not res:
        return
    r = res["datos"]
    if not r["exito"]:
        st.error(r["mensaje"])
        return
    vig = ui.vigente(res, entradas)
    Qhat = r["valor_evaluado"]

    st.markdown("#### Resultado")
    m1, m2, m3 = st.columns(3)
    m1.metric("$Q_{total}$ estimado", f"{Qhat:.4f} m³/s")
    m2.metric("En pies cúbicos por segundo", f"{Qhat / dr.CFS_A_M3S:,.0f} cfs")
    m3.metric("Grado del polinomio", f"{r['grado']}")
    if r["extrapolando"]:
        st.markdown(f'<div class="caja-error"><b>Extrapolación.</b> {r["advertencia_extrapolacion"]} '
                    "No se permite publicar este valor al flujo integrado.</div>", unsafe_allow_html=True)
    if datos.get("procedencia") == "preliminar":
        st.markdown('<div class="caja-aviso"><b>Fuente de los datos.</b> Los nodos nivel–caudal están tomados de la estación USGS 09380000 '
                    "y se usan aquí únicamente para practicar el método de interpolación de Lagrange.</div>", unsafe_allow_html=True)

    st.markdown("**Polinomio y bases de Lagrange**")
    st.latex(r"P_n(h)=\sum_{i=0}^{n} Q_i\,L_i(h),\qquad L_i(h)=\prod_{j\neq i}\frac{h-h_j}{h_i-h_j}")
    Li = r["valores_bases_en_x_eval"]
    I = lambda x: f"<i>{x}</i>"
    hi, Qi, Li_ = I("h") + "<sub>i</sub>", I("Q") + "<sub>i</sub>", I("L") + "<sub>i</sub>"
    hc = f"({I('h')}<sub>c</sub>)"
    _f = lambda x: ui.fmt(x, 4).replace("-", "−")
    ui.tabla_html([{"<i>i</i>": k, f"{hi} (m)": _f(h[k]), f"{Qi} (m³/s)": _f(Q[k]), f"{Li_}{hc}": _f(Li[k]),
                    f"{Qi}·{Li_}{hc} (m³/s)": _f(Q[k] * Li[k])} for k in range(len(h))], izquierda=True)
    st.caption(rf"Comprobación: $\sum_i L_i(h_c) = {sum(Li):.10f}$ (debe ser 1) · $\sum_i Q_i\,L_i(h_c) = {Qhat:.6f}$ m³/s $= P(h_c)$.")
    with st.expander("Expresiones algebraicas (variable $h$ en metros)"):
        for i, b in enumerate(r["bases_L"]):
            st.code(f"L{str(i).translate(str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉'))}(h) = {texto_polinomio(b)}", language="text")
        st.code(f"P(h) = {r['expresion_algebraica']}", language="text")
        st.caption("Los coeficientes de la forma expandida pueden estar mal condicionados y se muestran solo como referencia; "
                   "la evaluación numérica usa la fórmula de Lagrange directa.")

    st.markdown("**Reproducción de los nodos**")
    rn = r["reproduccion_nodos"]
    ui.tabla_html([{f"{hi} (m)": _f(d_["nodo_x"]), f"{Qi} (m³/s)": _f(d_["y_real"]), f"{I('P')}({hi})": _f(d_["y_interp"]),
                    f"|{I('P')}({hi}) − {Qi}|": ui.cient(d_["error_absoluto"], 1)} for d_ in rn["detalles"]], izquierda=True)
    st.caption(rn["conclusion"])
    comp = r.get("comparacion_libreria") or {}
    if "coincidencia" in comp:
        st.caption(f"Contraste con {comp['libreria']}: diferencia {ui.cient(comp['diferencia_eval'], 1)} m³/s · coincide: {'sí' if comp['coincidencia'] else 'NO'}.")

    st.markdown("#### Gráfica")
    ui.grafica(graficas.fig_interpolacion(h, Q, {"Lagrange": r["P_poly"]}, h_c, Qhat, datos["validacion"],
                                          "Interpolación de Lagrange: caudal vs. nivel"), "fig_lagrange")

    st.markdown("#### Validación con observación reservada (no usada en la construcción)")
    vals = datos["validacion"]
    if not vals:
        st.info("No hay observaciones de validación. Puede agregar las suyas en el modo «Mis propios nodos».")
    else:
        filas, y_obs, y_hat = [], [], []
        for v in vals:
            q_hat = float(r["P_poly"](v["h_m"]))
            y_obs.append(v["Q_m3s"])
            y_hat.append(q_hat)
            e = q_hat - v["Q_m3s"]
            F = lambda x: f"{x:.5f}".replace("-", "−")
            filas.append({"Obs.": v["id"], "<i>h</i> (m)": F(v["h_m"]), "<i>Q</i><sub>obs</sub> (m³/s)": F(v["Q_m3s"]),
                          "<i>Q̂</i><sub>Lagrange</sub> (m³/s)": F(q_hat), "Error <i>e</i> (m³/s)": F(e),
                          "Error relativo (%)": F(100 * e / v["Q_m3s"]),
                          "Dentro del intervalo": "sí" if hmin <= v["h_m"] <= hmax else "NO (extrapolación)"})
        ui.tabla_html(filas, izquierda=True)
        for v in vals:
            if v.get("fecha"):
                st.caption(f"{v['id']}: {v['nivel_ft']} ft / {v['caudal_cfs']} cfs · {v['fecha']} · {v['calificador']}. {v['tipo']}")
        mt = metricas_error(y_obs, y_hat)
        ui.tabla_html([{"<i>n</i>": mt["n"], "MAE (m³/s)": f"{mt['MAE']:.5f}", "RMSE (m³/s)": f"{mt['RMSE']:.5f}",
                        "Error máximo (m³/s)": f"{mt['error_max']:.5f}"}], izquierda=True)
        if mt["nota"]:
            st.caption(mt["nota"])
    if datos.get("pendiente"):
        with st.expander("Observación pendiente de verificación (excluida de todos los cálculos)"):
            p = datos["pendiente"]
            st.markdown(f"h = {p['nivel_ft']} ft ({p['h_m']:.4f} m), Q = {p['caudal_cfs']} cfs ({p['Q_m3s']:.2f} m³/s) · {p['fecha']}")
            st.markdown(p["estado"])

    st.markdown("#### Interpretación y límites")
    st.markdown(
        f"- Para h = {h_c:.4f} m el polinomio de Lagrange estima $Q_{{total}}$ ≈ **{Qhat:.2f} m³/s**.\n"
        "- Reproducir los nodos **no garantiza** exactitud entre ellos; un polinomio de grado alto puede oscilar (fenómeno de Runge).\n"
        "- Una curva de descarga cambia con el tiempo (sedimentación, erosión, actualización del rating) y el caudal en Lees Ferry está "
        "regulado por la presa de Glen Canyon: no es un régimen natural.\n"
        "- La observación de validación es una lectura provisional cuyo caudal USGS calcula con su propio rating: no es una medición "
        "independiente de caudal.")

    st.markdown("#### Publicar al flujo integrado")
    puede = vig and not r["extrapolando"] and Qhat > 0
    if st.button("Usar esta estimación como $Q_{total}$", key="pub_q3", disabled=not puede, type="primary"):
        estado.publicar("q_total", Qhat, "m³/s", "Pestaña 3 · Lagrange", {"h": h_c},
                        f"h = {h_c:.4f} m · nodos: {datos.get('procedencia', '—')}")
        estado.invalidar("q_d")
        st.success("$Q_{total}$ publicado. La pestaña 2 lo usará para calcular $Q_d$ y la profundidad crítica.")
    if not vig:
        st.caption("Recalcule para poder publicar (las entradas cambiaron).")
    elif not puede:
        st.caption("No se puede publicar: el nivel está fuera del intervalo de los nodos o el caudal no es positivo.")
