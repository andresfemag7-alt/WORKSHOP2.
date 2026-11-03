import pandas as pd
import streamlit as st

import ui
from modulos.caso.estructura import armadura_warren_canal, resolver_armadura, solucion_analitica_warren
from modulos.metricas import evaluar_condicionamiento

ui.iniciar("Sistemas lineales: armadura Warren", "sistemas_lineales", "🏗️")
st.caption("Equilibrio de nudos A·x = b resuelto con eliminación de Gauss con pivoteo parcial.")

c1, c2, c3 = st.columns(3)
L = c1.slider("Luz L [m]", 4.0, 40.0, 20.0, 0.5)
H = c2.slider("Altura H [m]", 1.0, 10.0, 4.0, 0.5)
W = c3.slider("Peso total del agua W [kN]", 0.0, 500.0, 100.0, 5.0)

sis = armadura_warren_canal(L, H, W)
sol = resolver_armadura(sis)
if not sol["exito"]:
    st.error(sol["mensaje"])
    st.stop()

ana = solucion_analitica_warren(L, H, W)
filas = [{"barra": n, "fuerza [kN]": f, "estado": sol["estado_barras"][n], "analítica [kN]": ana[n],
          "diferencia": abs(f - ana[n])} for n, f in sol["fuerzas_kN"].items()]
st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
st.write("Reacciones [kN]:", sol["reacciones_kN"])

cond = evaluar_condicionamiento(sis["A"])
st.info(f"κ(A) = {cond['kappa']:.3g} · {cond['estado']}. {cond['advertencia']}")
(st.success if sol["equilibrio_global"]["cumple"] else st.error)(
    "Equilibrio global (ΣFx, ΣFy, ΣM) verificado." if sol["equilibrio_global"]["cumple"]
    else "El equilibrio global no se cumple.")

fig, ax = ui.figura(8, 3.2)
P = sis["nodos"]
for nombre, a, b in sis["barras"]:
    f = sol["fuerzas_kN"][nombre]
    col = ui.AMBAR if f > 1e-9 else ui.CORAL if f < -1e-9 else ui.HIELO
    (x1, y1), (x2, y2) = P[a], P[b]
    ax.plot([x1, x2], [y1, y2], color=col, lw=3)
for n, (x, y) in P.items():
    ax.scatter(x, y, color=ui.HIELO, zorder=5)
    ax.annotate(n, (x, y), textcoords="offset points", xytext=(6, 6), color=ui.HIELO)
ax.set_aspect("equal")
ax.set_xlabel("x [m]")
ax.set_ylabel("y [m]")
st.pyplot(fig, transparent=True)
st.caption("Ámbar = tracción · Coral = compresión · Gris = fuerza nula.")
