import numpy as np
import pandas as pd
import streamlit as st

import ui
from modulos.caso import datos_rio as dr
from modulos.diferencias_divididas import interpolacion_newton
from modulos.lagrange import lagrange_interpolacion

ui.iniciar("Interpolación polinomial", "interpolacion", "📈")
st.caption("Lagrange y Newton construyen el mismo polinomio único de grado n−1 por los n nodos.")

xs, ys = dr.arrays_nodos()
st.subheader("Nodos nivel–caudal (preliminares)")
st.dataframe(pd.DataFrame(dr.nodos_construccion())[["id", "nivel_ft", "caudal_cfs", "h_m", "Q_m3s"]],
             use_container_width=True, hide_index=True)

h_min, h_max = min(xs), max(xs)
h = st.slider("Nivel h [m] a evaluar", float(h_min - 0.3), float(h_max + 0.3),
              float(dr.observacion_validacion()["h_m"]), 0.01)

lag = lagrange_interpolacion(xs, ys, h)
new = interpolacion_newton(xs, ys, h)
if not (lag["exito"] and new["exito"]):
    st.error(lag.get("mensaje") or new.get("mensaje"))
    st.stop()

c1, c2 = st.columns(2)
c1.metric("Q Lagrange [m³/s]", f"{lag['valor_evaluado']:.3f}")
c2.metric("Q Newton [m³/s]", f"{new['valor_evaluado']:.3f}")
if lag["extrapolando"]:
    st.warning(lag["advertencia_extrapolacion"])

with st.expander("Polinomio y comparación con SciPy"):
    st.code(lag["expresion_algebraica"])
    st.write(lag["comparacion_libreria"])

fig, ax = ui.figura()
xx = np.linspace(h_min - 0.3, h_max + 0.3, 400)
ax.plot(xx, lag["P_poly"](xx), color=ui.TEAL, lw=2.5, label="P(h)")
ax.scatter(xs, ys, color=ui.AMBAR, zorder=5, label="nodos")
ax.axvline(h, color=ui.CORAL, ls="--", alpha=0.7)
ax.set_xlabel("h [m]")
ax.set_ylabel("Q [m³/s]")
ax.legend(facecolor="none", labelcolor=ui.HIELO)
st.pyplot(fig, transparent=True)
