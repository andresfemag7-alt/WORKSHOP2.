import pandas as pd
import streamlit as st

import ui
from modulos.caso import datos_rio as dr
from modulos.caso import hidraulica as hid
from modulos.caso.estructura import armadura_warren_canal, resolver_armadura
from modulos.newton_sistemas import newton_raphson_sistemas
from modulos.spline import spline_cubico_natural

ui.iniciar("Caso integrador: río → canal → armadura", "caso_integrador", "🌉")
st.caption("Modelo ACADÉMICO CONCEPTUAL. Nodos preliminares; estación USGS 09380000 (Lees Ferry, AZ).")
for aviso in dr.ESTACION["advertencias"]:
    st.warning(aviso)

xs, ys = dr.arrays_nodos()
h_min, h_max = min(xs), max(xs)

st.subheader("1 · Hidrología: nivel → caudal (spline)")
c1, c2 = st.columns(2)
h = c1.slider("Nivel del río h [m]", float(h_min), float(h_max), float(dr.observacion_validacion()["h_m"]), 0.01)
alpha_min, alpha_max = hid.ALPHA_RANGO_ESCENARIO
alpha = c2.slider("Fracción derivada α", alpha_min, alpha_max, 0.15, 0.01)
q_total = float(spline_cubico_natural(xs, ys)["eval_func"](h))
q_d = hid.caudal_derivado(q_total, alpha)
st.write(f"Q total = **{q_total:.2f} m³/s** · Q derivado = **{q_d:.2f} m³/s**")

st.subheader("2 · Hidráulica: tirante crítico (Newton–Raphson)")
c3, c4 = st.columns(2)
b = c3.slider("Ancho del canal b [m]", 1.0, 20.0, 6.0, 0.5)
L = c4.slider("Luz de la armadura L [m]", 4.0, 40.0, 12.0, 0.5)
yc = hid.profundidad_critica_analitica(q_d, b)
F, J, _ = hid.sistema_critico(q_d, b, 9.81, yc)
nw = newton_raphson_sistemas(F, hid.aproximacion_inicial(q_d, b, yc * 1.5), J=J, dominio=hid.dominio_positivo)
if not nw.get("convergio"):
    st.error(nw.get("motivo_parada") or nw.get("mensaje"))
    st.stop()
y_sol, V_sol = nw["x_sol"]
comp = hid.comprobaciones_hidraulicas(y_sol, q_d, b)
st.write(f"y = **{y_sol:.4f} m** (analítico {yc:.4f} m) · V = **{V_sol:.3f} m/s** · Fr = **{comp['froude']:.4f}**")

st.subheader("3 · Estructura: armadura Warren (Gauss)")
w = hid.peso_agua_por_metro_kNm(y_sol, b)["w_kN_por_m"]
W = hid.carga_en_tramo_kN(w, L)
H_arm = st.slider("Altura de la armadura H [m]", 1.0, 8.0, 3.0, 0.5)
sol = resolver_armadura(armadura_warren_canal(L, H_arm, W))
if not sol["exito"]:
    st.error(sol["mensaje"])
    st.stop()
st.write(f"Peso del agua sobre el tramo: **{W:.1f} kN** ({w:.2f} kN/m)")
st.dataframe(pd.DataFrame([{"barra": n, "fuerza [kN]": f, "estado": sol["estado_barras"][n]}
                           for n, f in sol["fuerzas_kN"].items()]), use_container_width=True, hide_index=True)
st.caption("Solo se considera el peso del agua; no incluye peso propio del canal ni de la armadura, ni sobrecargas.")
