"""Pestaña 1 · Sistemas lineales: equilibrio estático de la armadura que soporta el canal."""
from __future__ import annotations

import html
import math
import re

import numpy as np
import pandas as pd
import streamlit as st

from modulos.caso import estructura as es
from modulos.caso import hidraulica as hy
from modulos.sistemas_lineales import comparar_con_libreria_lineal, gauss_pivoteo_parcial

from .. import componentes as ui
from .. import estado, graficas
from .. import notacion as nt
from ..config import textos

DESCRIPCION_ECUACION = {"Fx": "Σ Fx = 0", "Fy": "Σ Fy = 0"}
EJEMPLOS = {
    "Caso 1 · 3×3 con pivote nulo (Clase 07)": ([[0, 2, 3], [4, 6, 7], [2, 1, 6]], [8, -3, 5]),
    "Caso 2 · 2×2 bien condicionado": ([[3, -2], [-1, 4]], [5, 15]),
    "Caso 3 · 4×4 tridiagonal": ([[1, 1, 0, 0], [-1, 2, 1, 0], [0, -1, 2, 1], [0, 0, -1, 2]], [3, 6, 8, 5]),
}
PERSONALIZADO = "Personalizado n×n"

# ----------------------------------------------------------------------------- formato de tablas (estilo tabla_html, a la izquierda)
_SUP_MENOS = "−"


def _I(x: str) -> str:
    return f"<i>{x}</i>"


def _etq(nombre: str) -> str:
    """Etiqueta de incógnita/variable en HTML: Rx_A → R<sub>x,A</sub> cursiva, x1 → x<sub>1</sub>, AB → AB."""
    m = re.fullmatch(r"R([xy])_(\w+)", nombre)
    if m:
        return f"{_I('R')}<sub>{_I(m.group(1))}, {m.group(2)}</sub>"
    m = re.fullmatch(r"([A-Za-z])(\d+)", nombre)
    if m:
        return f"{_I(m.group(1))}<sub>{m.group(2)}</sub>"
    return nombre


def _ecuacion(codigo: str) -> str:
    """'A:Fx' → 'Nudo A: ΣF<sub>x</sub> = 0'."""
    nudo, eje = codigo.split(":")
    return f"Nudo {nudo}: Σ{_I('F')}<sub>{_I(eje[1])}</sub> = 0"


def _cient_html(x: float, n: int = 2) -> str:
    """1.42e-14 → 1.42×10 con exponente −14 en superíndice (el cero se muestra como 0)."""
    x = float(x)
    if x == 0:
        return "0"
    mant, exp = f"{x:.{n}e}".split("e")
    return f"{mant.replace('-', _SUP_MENOS)}×10<sup>{int(exp)}</sup>".replace("<sup>-", f"<sup>{_SUP_MENOS}")


def _num(x, d: int = 4) -> str:
    """Número con hasta ``d`` decimales (sin ceros sobrantes) y signo menos tipográfico."""
    x = float(x)
    t = f"{round(x, d) + 0.0:.{d}f}".rstrip("0").rstrip(".")
    return (t or "0").replace("-", _SUP_MENOS)


def _texto(t: str) -> str:
    """Texto de los módulos con notación: kappa(A) → κ(A), «en x» → «en x» en negrita, <= → ≤."""
    t = html.escape(str(t), quote=False).replace("<=", "≤").replace(">=", "≥")
    t = t.replace("kappa(A)", f"{_I('κ')}(<b>A</b>)").replace("kappa", _I("κ"))
    return re.sub(r"\ben x\b", "en <b>x</b>", t)


def _matriz(M, etiquetas: list[str]) -> None:
    """Matriz (aumentada o no) con encabezados en cursiva con subíndice y entradas justificadas a la izquierda."""
    cols = [_etq(e) if e != "b" else "<b>b</b>" for e in etiquetas]
    ui.tabla_html([{c: _num(v) for c, v in zip(cols, fila)} for fila in np.asarray(M, dtype=float)], izquierda=True)


def render() -> None:
    ui.cabecera_tab("lineales")
    modo = st.radio("Modo de trabajo", ["Armadura del caso integrador", r"Sistema lineal propio ($\mathbf{A}\mathbf{x}=\mathbf{b}$)"],
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
    L = c1.number_input(r"Luz del tramo $L$ (m)", 0.5, 100.0, 5.0, 0.5, key="lin_L",
                        help="Longitud de canal soportada por la armadura = luz entre apoyos A y C. Supuesto del escenario (propuesta original: 5 m).")
    H = c2.number_input(r"Altura de la armadura $H$ (m)", 0.2, 50.0, 1.5, 0.1, key="lin_H", help="Supuesto del escenario.")
    rho = c3.number_input(r"Densidad del agua $\rho$ (kg/m³)", 900.0, 1100.0, 1000.0, 10.0, key="lin_rho",
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
            st.warning(r"⚠️ El caudal total publicado cambió después de calcular $y_c$, que por tanto **está desactualizado**. "
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
        W = st.number_input(r"Peso total del agua sobre el tramo $W$ (kN)", 0.0, 1e6, 200.0, 10.0, key="lin_W",
                            help=r"Modo manual e independiente de las otras pestañas. $W=w\,L$, con $w=\rho\,g\,b\,y$.")
        filas.append({"simbolo": "W", "descripcion": "Peso del agua en el tramo (manual)", "valor": ui.fmt(W, 3), "unidad": "kN", "proc": "editado"})
    ui.tabla_variables(filas)
    if usar_flujo:
        st.caption(r"Cadena de transferencia: $w=\rho\,g\,b\,y_c$ [N/m → kN/m]; $W=w\,L$ [kN] (carga **tributaria** del tramo, no carga de diseño); "
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
        st.info(r"Con $W=0$ todas las fuerzas son nulas: es el resultado correcto del modelo.")

    st.markdown(r"#### Sistema de equilibrio $\mathbf{A}\mathbf{x}=\mathbf{b}$")
    cA, cB = st.columns([3, 2])
    with cA:
        etq = sis["incognitas"]
        ecs = [_ecuacion(e) for e in sis["ecuaciones"]]
        ui.tabla_html([{"Ecuación": ec, **{_etq(n): _num(v) for n, v in zip(etq, fila)}}
                       for ec, fila in zip(ecs, np.asarray(sis["A"], dtype=float))], izquierda=True)
    with cB:
        ui.tabla_html([{"Ecuación": ec, f"<b>b</b> = −{_I('P')}<sub>ext</sub> (kN)": _num(v)}
                       for ec, v in zip(ecs, sis["b"])], izquierda=True)
        st.caption(r"Incógnitas $\mathbf{x}$: fuerzas axiales de las 7 barras (kN; **+ tracción, − compresión**) y 3 reacciones (kN). "
                   f"10 ecuaciones, 10 incógnitas, rango = {sis['rango']} → armadura **estáticamente determinada y estable**.")

    mostrar_gauss(r["gauss"], sis["incognitas"], "arm")

    st.markdown("#### Resultados")
    c1, c2 = st.columns([3, 2])
    with c1:
        ui.tabla_html([{"Barra": n, "Nudos": f"{a}–{b_}", "Longitud (m)": _num(sis["longitudes"][n]),
                        f"Fuerza axial {_I('N')} (kN)": _num(r["fuerzas_kN"][n]), "Estado": r["estado_barras"][n]}
                       for n, a, b_ in sis["barras"]], izquierda=True)
    with c2:
        ui.tabla_html([{"Reacción": _etq(k), "Valor (kN)": _num(v)} for k, v in r["reacciones_kN"].items()], izquierda=True)
    ui.grafica(graficas.fig_armadura(sis, r), "fig_armadura")

    g = r["gauss"]
    eq = r["equilibrio_global"]
    st.markdown("#### Comprobaciones")
    ref = es.solucion_analitica_warren(L, H, W)
    dif = max(abs(r["fuerzas_kN"][k] - ref[k]) for k in r["fuerzas_kN"])
    comp = comparar_con_libreria_lineal(sis["A"], sis["b"], g["x"])
    C = _cient_html
    ui.tabla_html([
        {"Comprobación": f"Residual ‖<b>A</b>·<b>x</b> − <b>b</b>‖<sub>∞</sub> (kN)", "Valor": C(g["norma_residuo_inf"], 2),
         "Lectura": "≈ 0: se satisface cada ecuación de equilibrio"},
        {"Comprobación": f"Σ{_I('F')}<sub>{_I('x')}</sub>, Σ{_I('F')}<sub>{_I('y')}</sub> global (kN)",
         "Valor": f"{C(eq['suma_Fx_kN'], 1)}, {C(eq['suma_Fy_kN'], 1)}", "Lectura": "Cargas + reacciones en equilibrio"},
        {"Comprobación": f"Σ{_I('M')} respecto al origen (kN·m)", "Valor": C(eq["suma_M_kNm"], 1), "Lectura": "Equilibrio de momentos"},
        {"Comprobación": f"Máx |<b>x</b> − solución analítica| (kN)", "Valor": C(dif, 1), "Lectura": "Método de los nudos a mano (simetría)"},
        {"Comprobación": f"Máx |<b>x</b> − <code>{comp['libreria_usada']}</code>|", "Valor": C(comp["max_diferencia_absoluta"], 1),
         "Lectura": _texto(comp["interpretacion"])},
        {"Comprobación": f"{_I('κ')}<sub>2</sub>(<b>A</b>)", "Valor": C(g["condicion_A"], 2),
         "Lectura": f"{_texto(g['estado_condicion'])}. {_texto(g['advertencia_condicion'])}"},
    ], izquierda=True)
    st.markdown("#### Interpretación")
    ab, bc = r["fuerzas_kN"]["AB"], r["fuerzas_kN"]["DE"]
    st.markdown(
        f"- Las barras **inferiores (AB, BC)** trabajan en **tracción** (~{ab:.1f} kN) y la **cuerda superior DE** en **compresión** "
        f"(~{abs(bc):.1f} kN), como en una viga biapoyada; las diagonales AD y EC están en compresión y las barras DB y BE resultan de fuerza nula para esta carga simétrica.\n"
        f"- Cada apoyo vertical toma $W/2$ = {W / 2:.1f} kN y la reacción horizontal es nula (sin cargas horizontales).\n"
        "- **Límites:** es solo el peso del agua. No incluye peso propio del canal y de la armadura, sobrecargas, viento, sismo, pandeo de barras en compresión, "
        "ni factores de seguridad: **no es una verificación estructural**.")

    with st.expander("Auditoría: por qué no se usó la matriz 3×3 de la propuesta inicial"):
        theta = st.slider(r"Ángulo $\theta$ del triángulo de referencia (°)", 15, 75, 30, key="aud_theta")
        a = es.auditar_matriz_gemini(math.radians(theta), 100.0)
        ui.tabla_html([
            {"Barra": n, f"Propuesta ({_I('T')}) (kN)": _num(a["gemini"][f"T_{n}"]),
             "Triángulo bien planteado (numérico) (kN)": _num(a["referencia_numerica"][n]),
             "Analítica (kN)": _num(a["referencia_analitica"][n])} for n in ("AB", "AC", "BC")], izquierda=True)
        st.markdown(r"La matriz propuesta no es una armadura determinada: su 3.ª fila ($T_{AB}=0$) no corresponde a ningún equilibrio de nudo, "
                    r"omite las reacciones y obliga a $T_{AB}=0$, lo que viola el equilibrio horizontal en A. Resultados con $P=100$ kN.")


# ----------------------------------------------------------------------------- sistema propio
def _propio() -> None:
    st.markdown(r"Resuelva **cualquier** sistema $\mathbf{A}\mathbf{x}=\mathbf{b}$ de forma independiente (no depende de las otras pestañas).")
    preset = st.selectbox("Sistema", list(EJEMPLOS) + [PERSONALIZADO], key="lin_preset")
    if preset == PERSONALIZADO:
        n = int(st.number_input(r"Orden $n$", 2, 8, 3, 1, key="lin_n"))
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
    ui.tabla_html([{"Variable": _etq(c), "Valor": _num(v, 10),
                    f"Residual {_I('r')}<sub>{_I('i')}</sub> = (<b>A</b>·<b>x</b> − <b>b</b>)<sub>{_I('i')}</sub>": _cient_html(rr, 2)}
                   for c, v, rr in zip(cols, g["x"], g["residuo"])], izquierda=True)
    comp = comparar_con_libreria_lineal(A_np, b_np, g["x"])
    ui.tabla_html([
        {"Diagnóstico": "‖<b>r</b>‖<sub>∞</sub> / ‖<b>b</b>‖<sub>∞</sub>", "Valor": _cient_html(g["residuo_relativo"], 2)},
        {"Diagnóstico": f"{_I('κ')}<sub>2</sub>(<b>A</b>)", "Valor": f"{_cient_html(g['condicion_A'], 3)} — {_texto(g['estado_condicion'])}"},
        {"Diagnóstico": f"Máx |<b>x</b> − <code>{comp['libreria_usada']}</code>|", "Valor": _cient_html(comp["max_diferencia_absoluta"], 2)},
    ], izquierda=True)
    st.caption(nt.mensaje(g["advertencia_condicion"]) + r" Un residual pequeño NO garantiza un error pequeño en $\mathbf{x}$ si $\kappa(\mathbf{A})$ es grande.")


# ----------------------------------------------------------------------------- procedimiento
def mostrar_gauss(g: dict, etiquetas: list[str], clave: str) -> None:
    if not g["exito"]:
        st.error(g["mensaje"])
        return
    with st.expander("Procedimiento: pivoteo parcial, multiplicadores y matriz tras cada etapa", expanded=False):
        encab = list(etiquetas) + ["b"]
        st.markdown(r"Matriz aumentada inicial $[\mathbf{A}\mid\mathbf{b}]$:")
        _matriz(g["matrices_etapas"][0], encab)
        for paso, M in zip(g["historial_pasos"], g["matrices_etapas"][1:]):
            sw = (f"intercambio {nt.fila(paso['filas_intercambiadas'][0])} ↔ {nt.fila(paso['filas_intercambiadas'][1])}"
                  if paso["hubo_intercambio"] else "sin intercambio de filas")
            st.markdown(f"**Etapa $k={paso['paso_k']}$** — columna {paso['columna']}, pivote $p={paso['valor_pivote']:+.4f}$, {sw}.")
            if paso["multiplicadores"]:
                ui.tabla_html([{"Operación": (f"{_I('F')}<sub>{m['fila_afectada']}</sub> ← {_I('F')}<sub>{m['fila_afectada']}</sub> "
                                              f"− ({_num(m['factor_m'], 4)})·{_I('F')}<sub>{m['fila_pivote']}</sub>"),
                                f"{_I('m')}<sub>{_I('ik')}</sub>": _num(m["factor_m"], 6)} for m in paso["multiplicadores"]], izquierda=True)
            _matriz(M, encab)
        st.markdown(r"**Sustitución regresiva** sobre la matriz triangular $[\mathbf{U}\mid\mathbf{c}]$ de la última etapa:")
        st.latex(r"x_n=\frac{c_n}{u_{nn}},\qquad x_i=\frac{c_i-\sum_{j=i+1}^{n}u_{ij}\,x_j}{u_{ii}},\quad i=n-1,\dots,1")

