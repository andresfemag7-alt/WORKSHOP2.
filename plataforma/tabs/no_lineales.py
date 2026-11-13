"""Pestaña 2 · Sistemas no lineales: profundidad crítica del canal rectangular."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from modulos.caso import hidraulica as hy
from modulos.newton_sistemas import comparar_con_libreria_no_lineal, newton_raphson_sistemas
from modulos.punto_fijo import punto_fijo_sistemas

from .. import componentes as ui
from .. import estado, graficas, simbolos
from ..config import textos

MODO_FLUJO = "Usar $Q_{total}$ publicado (pestaña 3 o 4)"
MODO_MANUAL = "Ingresar $Q_{total}$ manualmente"


def render() -> None:
    ui.cabecera_tab("no_lineales")
    with st.expander("Ecuación física, derivación y formulación como sistema", expanded=False):
        st.markdown(
            "Para una sección **rectangular** de ancho *b* con caudal *Q*, el flujo es crítico cuando el número de Froude vale 1:")
        st.latex(r"Fr=\frac{V}{\sqrt{g\,y}}=1,\qquad Q=b\,y\,V")
        st.markdown("Eliminando *V* se obtiene la ecuación escalar de la propuesta original, que se verificó dimensionalmente "
                    "([m⁶/s²] en ambos términos):")
        st.latex(r"f(y_c)=Q_d^{2}-g\,b^{2}\,y_c^{3}=0,\qquad f'(y_c)=-3\,g\,b^{2}\,y_c^{2},\qquad y_c=\left(\frac{Q_d^{2}}{g\,b^{2}}\right)^{1/3}")
        st.markdown(
            "**Cómo encaja con «sistemas» de ecuaciones.** Las dos condiciones físicas independientes forman un sistema 2×2 en las "
            "incógnitas reales *(y, V)* — no se fabrican incógnitas:")
        st.latex(r"f_1=V^{2}-g\,y=0\ (Fr=1),\qquad f_2=b\,y\,V-Q_d=0\ (\text{continuidad})")
        st.markdown(
            "Se escalan (F₁/(g·y_ref), F₂/$Q_d$) para que las tolerancias sean **adimensionales**. *Punto fijo simultáneo:* "
            "y⁽ᵏ⁺¹⁾ = $Q_d$/(b·V⁽ᵏ⁾), V⁽ᵏ⁺¹⁾ = √(g·y⁽ᵏ⁾), ambos con el vector anterior; el radio espectral de la iteración en la raíz es 1/√2 ≈ 0.71 < 1, "
            "así que converge (linealmente). *Newton:* J·Δx = −F sin invertir J. El caso escalar se resuelve con el mismo Newton (n = 1).")
        st.markdown("**Advertencia:** $y_c$ es solo el tirante del régimen crítico. No es el tirante normal ni el de operación y **no garantiza** "
                    "borde libre, estabilidad ni seguridad del canal.")

    st.markdown("#### Entradas")
    q_item = estado.obtener("q_total")
    if q_item is not None:
        modo = st.radio("Origen del caudal total", [MODO_FLUJO, MODO_MANUAL], horizontal=True, key="nl_modo")
    else:
        st.info(textos.MSG_SIN_FLUJO + " Puede trabajar de forma independiente con $Q_{total}$ manual.")
        modo = MODO_MANUAL
    if modo == MODO_FLUJO:
        Qt = q_item["valor"]
        st.markdown(f"$Q_{{total}}$ = **{Qt:.4f} m³/s** · calculado por *{q_item['modulo']}* a las {q_item['hora']} ({q_item['detalle']}).")
        proc_q = "calculado"
    else:
        Qt = st.number_input("Q_total (m³/s)", 0.001, 1e5, 222.85, 1.0, key="nl_Qt_manual", format="%.4f",
                             help="Valor manual de ejemplo (≈ lectura USGS del 2026-11-01).")
        proc_q = "editado"

    c1, c2, c3 = st.columns(3)
    alpha = c1.number_input("Fracción derivada α", 0.01, 1.0, 0.15, 0.01, key="nl_alpha",
                            help="Supuesto del ejercicio (15 %). No es una regla universal ni una autorización de captación.")
    b = c2.number_input("Ancho del canal b (m)", 0.2, 100.0, 4.0, 0.1, key="nl_b", help="Supuesto del escenario.")
    g = c3.number_input("Gravedad g (m/s²)", 9.0, 10.0, 9.81, 0.01, key="nl_g")
    if not (hy.ALPHA_RANGO_ESCENARIO[0] <= alpha <= hy.ALPHA_RANGO_ESCENARIO[1]):
        st.warning(f"α = {alpha:.2f} está fuera del rango de trabajo del escenario ({hy.ALPHA_RANGO_ESCENARIO[0]:.2f}–"
                   f"{hy.ALPHA_RANGO_ESCENARIO[1]:.2f}); el cálculo es válido, pero revise que tenga sentido.")
    Qd = Qt * alpha

    st.markdown("**Parámetros del método iterativo**")
    st.caption("En las tolerancias use el **punto (.)** como separador decimal. El mismo valor se puede escribir de tres formas: "
               "decimal `0.0001`; científica `1e-4` (la «e» significa «por 10 elevado a»); o potencia de diez `1x10^-4`.")
    d1, d2, d3, d4 = st.columns(4)
    y0 = d1.number_input("Profundidad inicial y₀ (m)", 0.01, 100.0, 1.0, 0.1, key="nl_y0",
                         help="Debe ser positiva. V₀ se obtiene de la continuidad: V₀ = Q_d/(b·y₀).")
    tol_c = ui.tolerancia(d2, "Tolerancia del cambio", 1e-8, "nl_tolc_txt",
                          "‖Δx‖∞ en (m, m/s). Con y ~ 1 m, 1e-8 m es mucho menor que cualquier precisión de campo. "
                          "Escriba por ejemplo 6x10^-8 o 6e-8.")
    tol_r = ui.tolerancia(d3, "Tolerancia del residual", 1e-10, "nl_tolr_txt",
                          "‖F‖∞ del sistema ESCALADO (adimensional, error relativo de Fr² y de Q). Escriba por ejemplo 6x10^-8 o 6e-8.")
    max_it = int(d4.number_input("Máx. iteraciones", 1, 2000, 200, 10, key="nl_maxit"))

    ui.tabla_variables([
        {"simbolo": "Q_total", "descripcion": "Caudal total del río", "valor": ui.fmt(Qt, 4), "unidad": "m³/s", "proc": proc_q},
        {"simbolo": "α", "descripcion": "Fracción derivada", "valor": f"{alpha:.2f}", "unidad": "—", "proc": "editado" if alpha != 0.15 else "supuesto"},
        {"simbolo": "Q_d", "descripcion": "Caudal derivado Q_d = α·Q_total", "valor": ui.fmt(Qd, 4), "unidad": "m³/s", "proc": "calculado"},
        {"simbolo": "b", "descripcion": "Ancho del canal rectangular", "valor": f"{b:g}", "unidad": "m", "proc": "editado" if b != 4.0 else "supuesto"},
        {"simbolo": "g", "descripcion": "Aceleración de la gravedad", "valor": f"{g:g}", "unidad": "m/s²", "proc": "constante"},
        {"simbolo": "y, V", "descripcion": "Incógnitas: profundidad y velocidad (dominio: y > 0, V > 0)", "valor": "—", "unidad": "m, m/s", "proc": "calculado"},
    ])

    entradas = {"Q_total": Qt, "alpha": alpha, "b": b, "g": g, "y0": y0, "tol_c": tol_c, "tol_r": tol_r, "max_it": max_it}

    def calcular():
        try:
            hy.validar_parametros(Qd, b, g)
            x0 = hy.aproximacion_inicial(Qd, b, y0)
        except ValueError as exc:
            return {"error": str(exc)}
        Fs, Js, Gs = hy.sistema_critico(Qd, b, g, y0)
        newton = newton_raphson_sistemas(Fs, x0, J=Js, tol_cambio=tol_c, tol_residual=tol_r, max_iter=max_it, dominio=hy.dominio_positivo)
        pf = punto_fijo_sistemas(Gs, x0, tol_cambio=tol_c, tol_residual=tol_r, max_iter=max_it, F=Fs)
        F1, J1 = hy.sistema_escalar(Qd, b, g)
        esc = newton_raphson_sistemas(F1, [y0], J=J1, tol_cambio=tol_c, tol_residual=tol_r * Qd ** 2, max_iter=max_it, dominio=hy.dominio_positivo)
        out = {"newton": newton, "pf": pf, "esc": esc, "x0": x0, "Qd": Qd, "y_an": hy.profundidad_critica_analitica(Qd, b, g)}
        if newton["exito"] and newton["x_sol"]:
            out["lib"] = comparar_con_libreria_no_lineal(Fs, x0, newton["x_sol"])
        return out

    res = ui.ejecutar("nl", entradas, calcular, "Calcular profundidad crítica")
    if not res:
        return
    d = res["datos"]
    if "error" in d:
        st.error(d["error"])
        return
    vig = ui.vigente(res, entradas)
    nw, pf, esc = d["newton"], d["pf"], d["esc"]

    st.markdown("#### Resultados")
    if not nw["exito"] or not nw["convergio"]:
        st.markdown(f'<div class="caja-error"><b>Newton no convergió.</b> {simbolos.bonito(nw["motivo_parada"])}<br>'
                    "No se publica y_c al flujo integrado. Pruebe otra aproximación inicial o aumente el máximo de iteraciones.</div>", unsafe_allow_html=True)
        estado.invalidar("y_c")
        _tablas_historial(nw, pf, esc)
        return
    y_c, V_c = nw["x_sol"]
    comp = hy.comprobaciones_hidraulicas(y_c, d["Qd"], b, g)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Profundidad crítica $y_c$", f"{y_c:.5f} m")
    m2.metric("Velocidad crítica $V_c$", f"{V_c:.4f} m/s")
    m3.metric("Froude (comprobación)", f"{comp['froude']:.6f}")
    m4.metric("Área mojada $b \\cdot y_c$", f"{comp['area_mojada_m2']:.4f} m²")
    st.markdown(f'<div class="caja-res">Newton (sistema 2×2): {simbolos.bonito(nw["motivo_parada"])}</div>', unsafe_allow_html=True)

    I = lambda x: f"<i>{x}</i>"
    yc = I("y") + "<sub>c</sub>"
    Qd = I("Q") + "<sub>d</sub>"

    def fila_metodo(nombre, r):
        return {"Método": nombre, "Convergió": "sí" if r["convergio"] else "no", "Iteraciones": str(r["iteraciones"]),
                f"{yc} (m)": f"{r['x_sol'][0]:.4f}" if r.get("x_sol") else "—",
                "Motivo de parada": simbolos.bonito_html(r["motivo_parada"])}

    ui.tabla_html([
        fila_metodo(f"Newton-Raphson, sistema 2×2 ({I('y')}, {I('V')})", nw),
        fila_metodo("Punto fijo simultáneo, sistema 2×2", pf),
        fila_metodo(f"Newton escalar 1×1 sobre {I('f')}({I('y')}) = {Qd}² − {I('g')}·{I('b')}²·{I('y')}³", esc),
    ], izquierda=True)

    st.markdown("**Comprobaciones hidráulicas**")
    lib = d.get("lib", {})
    L = ui.cient_latex
    dif_e = comp["energia_especifica_m"] - comp["energia_minima_teorica_m"]
    ui.tabla_latex(
        ["Comprobación", "Fórmula", "Valor", "Diferencia"],
        [
            ["Profundidad crítica analítica",
             r"$y_c=\left(\dfrac{Q_d^{2}}{g\,b^{2}}\right)^{1/3}$",
             f"${comp['y_analitica_m']:.8f}\\ \\mathrm{{m}}$",
             f"con Newton: ${L(comp['diferencia_con_analitica_m'])}\\ \\mathrm{{m}}$"],
            ["Energía específica",
             r"$E=y+\dfrac{V^{2}}{2g}$",
             f"${comp['energia_especifica_m']:.6f}\\ \\mathrm{{m}}$",
             f"con $1.5\\,y_c$: ${L(dif_e)}\\ \\mathrm{{m}}$"],
            ["Residual de continuidad",
             r"$b\,y\,V-Q_d$",
             f"${L(comp['residual_Q_m3s'])}\\ \\mathrm{{m^{{3}}/s}}$",
             "—"],
            [f"`{lib.get('libreria_usada', 'scipy.optimize.root')}`",
             r"$\mathbf{F}(y,V)=\mathbf{0}$",
             f"$y={lib['x_libreria'][0]:.8f}\\ \\mathrm{{m}}$" if lib else "—",
             f"con Newton: ${L(lib['max_diferencia_absoluta'])}$" if lib else "—"],
        ],
        clave="tabla_comprobaciones")

    # Gráficas en ancho completo y una debajo de otra: en media columna los títulos de las subgráficas se pisaban.
    st.markdown("#### Gráficas")
    ui.grafica(graficas.fig_funcion_critica(d["Qd"], b, g, y_c, [h["x_k"][0] for h in esc["historial"]] + esc["x_sol"][:1]), "fig_fcrit")
    series = {"Newton 2×2": {"cambio": [h["norma_cambio"] for h in nw["historial"]], "residual": [h["norma_residual_nuevo"] for h in nw["historial"]]},
              "Punto fijo 2×2": {"cambio": [h["norma_cambio"] for h in pf["historial"]], "residual": [h["norma_residual"] for h in pf["historial"]]}}
    ui.grafica(graficas.fig_convergencia(series), "fig_conv")
    st.caption("El cambio entre iteraciones ‖Δx‖ y el residual ‖F‖ se evalúan por separado; **ninguno es el error verdadero** de $y_c$.")
    _tablas_historial(nw, pf, esc)

    st.markdown("#### Interpretación")
    st.markdown(
        f"- Para $Q_d$ = {d['Qd']:.2f} m³/s en un canal de b = {b:g} m, el flujo es crítico a $y_c$ = **{y_c:.3f} m** con $V_c$ = {V_c:.2f} m/s. "
        f"El caudal unitario es q = {comp['caudal_unitario_m2s']:.2f} m²/s.\n"
        "- Si el canal opera con tirantes **mayores** que $y_c$, el flujo es subcrítico (Fr < 1); con tirantes menores, supercrítico. "
        "Qué régimen ocurra depende de la pendiente y rugosidad (tirante normal), que **este modelo no calcula**.\n"
        "- $y_c$ no garantiza borde libre, estabilidad ni seguridad del canal.")

    st.markdown("#### Publicar al flujo integrado")
    puede = vig and abs(comp["diferencia_con_analitica_m"]) < 1e-4
    if st.button("Publicar $y_c$ (y $Q_d$) para la pestaña 1", key="pub_yc", disabled=not puede, type="primary"):
        estado.publicar("q_d", d["Qd"], "m³/s", "Pestaña 2 · No lineales", {"Q_total": Qt, "alpha": alpha}, "Q_d = α·Q_total")
        estado.publicar("y_c", y_c, "m", "Pestaña 2 · No lineales", {"Q_total": Qt, "alpha": alpha, "b": b, "g": g},
                        f"Newton 2×2, {nw['iteraciones']} iteraciones")
        st.success("y_c publicado. La pestaña 1 puede usarlo para calcular el peso del agua.")
    if not vig:
        st.caption("Recalcule para poder publicar (las entradas cambiaron).")
    elif not puede:
        st.caption("No se publica: $y_c$ no coincide con la solución analítica.")


def _tablas_historial(nw: dict, pf: dict, esc: dict) -> None:
    with st.expander("Historial iterativo (cambio y residual por separado)"):
        met = st.radio("Método", ["Newton 2×2", "Punto fijo simultáneo 2×2", "Newton escalar 1×1"], horizontal=True, key="nl_hist")
        if met == "Newton 2×2" and nw.get("historial"):
            ui.tabla(pd.DataFrame([{"k": h["iteracion"], "y_k (m)": h["x_k"][0], "V_k (m/s)": h["x_k"][1], "Δy (m)": h["delta_x"][0], "ΔV (m/s)": h["delta_x"][1],
                                    "‖Δx‖∞ (cambio)": h["norma_cambio"], "y_(k+1)": h["x_nuevo"][0], "V_(k+1)": h["x_nuevo"][1],
                                    "‖F(x_(k+1))‖∞ (residual)": h["norma_residual_nuevo"], "cond(J)": h["cond_J"]} for h in nw["historial"]]))
            st.caption("Δx es la **corrección** (solución de J·Δx = −F); x_(k+1) = x_k + Δx es la **nueva aproximación**.")
        elif met == "Punto fijo simultáneo 2×2" and pf.get("historial"):
            ui.tabla(pd.DataFrame([{"k": h["iteracion"], "y_k (m)": h["x_k"][0], "V_k (m/s)": h["x_k"][1], "y_(k+1)": h["x_nuevo"][0], "V_(k+1)": h["x_nuevo"][1],
                                    "‖Δx‖∞ (cambio)": h["norma_cambio"], "‖F(x_(k+1))‖∞ (residual)": h["norma_residual"]} for h in pf["historial"]]))
            st.caption("Actualización simultánea: y_(k+1) y V_(k+1) se calculan solo con (y_k, V_k).")
        elif met == "Newton escalar 1×1" and esc.get("historial"):
            ui.tabla(pd.DataFrame([{"k": h["iteracion"], "y_k (m)": h["x_k"][0], "f(y_k) (m⁶/s²)": h["F_k"][0], "f'(y_k)": h["jacobiano"][0][0],
                                    "Δy (m)": h["delta_x"][0], "y_(k+1)": h["x_nuevo"][0], "|f(y_(k+1))|": h["norma_residual_nuevo"]} for h in esc["historial"]]))
        else:
            st.info("Este método no produjo iteraciones.")
