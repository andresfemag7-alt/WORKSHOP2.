import numpy as np
import pandas as pd
import streamlit as st

import ui
from modulos.caso import hidraulica as hid
from modulos.newton_sistemas import newton_raphson_sistemas
from modulos.punto_fijo import punto_fijo_sistemas

ui.iniciar("Sistemas no lineales: tirante crítico", "no_lineales", "🌀")
st.caption("Se resuelve (y, V) con Fr = 1 y continuidad Q = b·y·V mediante Newton–Raphson y punto fijo.")

c1, c2, c3 = st.columns(3)
Q = c1.slider("Caudal Q [m³/s]", 1.0, 100.0, 20.0, 0.5)
b = c2.slider("Ancho b [m]", 1.0, 30.0, 10.0, 0.5)
factor = c3.slider("y₀ = factor × y crítico", 0.5, 3.0, 1.5, 0.1)

g = 9.81
yc = hid.profundidad_critica_analitica(Q, b, g)
F, J, G = hid.sistema_critico(Q, b, g, yc)
x0 = hid.aproximacion_inicial(Q, b, yc * factor)

nw = newton_raphson_sistemas(F, x0, J=J, dominio=hid.dominio_positivo)
pf = punto_fijo_sistemas(G, x0, F=F, max_iter=100)

m1, m2, m3 = st.columns(3)
m1.metric("y crítico analítico [m]", f"{yc:.5f}")
m2.metric("Newton: iteraciones", nw.get("iteraciones", "—"))
m3.metric("Punto fijo: iteraciones", pf.get("iteraciones", "—"))

for nombre, r in (("Newton–Raphson", nw), ("Punto fijo", pf)):
    if r.get("convergio"):
        st.success(f"{nombre}: {r['motivo_parada']}")
    else:
        st.warning(f"{nombre}: {r.get('motivo_parada') or r.get('mensaje')}")

fig, ax = ui.figura()
ys = np.linspace(max(0.05, yc * 0.4), yc * 2.2, 300)
ax.plot(ys, np.sqrt(g * ys), color=ui.TEAL, lw=2.5, label="V = √(g·y)  (Fr = 1)")
ax.plot(ys, Q / (b * ys), color=ui.CORAL, lw=2.5, label="V = Q/(b·y)  (continuidad)")
for r, col, et in ((nw, ui.AMBAR, "Newton"), (pf, ui.HIELO, "Punto fijo")):
    if r.get("historial"):
        pts = np.array([h["x_k"] for h in r["historial"]] + [r["x_sol"]])
        ax.plot(pts[:, 0], pts[:, 1], "-o", color=col, alpha=0.8, label=et)
ax.set_xlabel("y [m]")
ax.set_ylabel("V [m/s]")
ax.legend(facecolor="none", labelcolor=ui.HIELO)
st.pyplot(fig, transparent=True)

with st.expander("Historial de Newton–Raphson"):
    if nw.get("historial"):
        st.dataframe(pd.DataFrame([{"k": h["iteracion"], "y": h["x_k"][0], "V": h["x_k"][1],
                                    "‖F‖∞": h["norma_residual_k"], "cond(J)": h["cond_J"]}
                                   for h in nw["historial"]]), use_container_width=True, hide_index=True)
