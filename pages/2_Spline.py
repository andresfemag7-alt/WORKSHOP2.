import numpy as np
import pandas as pd
import streamlit as st

import ui
from modulos.caso import datos_rio as dr
from modulos.spline import spline_cubico_natural, verificar_monotonia

ui.iniciar("Spline cúbico natural", "spline", "〰️")
st.caption("Interpolación por tramos (clase C²) con S'' = 0 en los extremos.")

xs, ys = dr.arrays_nodos()
res = spline_cubico_natural(xs, ys)
if not res["exito"]:
    st.error(res["mensaje"])
    st.stop()

h_min, h_max = min(xs), max(xs)
h = st.slider("Nivel h [m] a evaluar", float(h_min), float(h_max), float(dr.observacion_validacion()["h_m"]), 0.01)
f, df = res["eval_func"], res["deriv_func"]

c1, c2 = st.columns(2)
c1.metric("Q spline [m³/s]", f"{float(f(h)):.3f}")
c2.metric("dQ/dh [m²/s]", f"{float(df(h)):.3f}")

mono = verificar_monotonia(f, h_min, h_max)
(st.success if mono["creciente"] else st.warning)(
    "La curva es monótona creciente en el intervalo." if mono["creciente"]
    else f"La curva decrece en {mono['n_tramos_decrecientes']} tramos de la malla.")

st.dataframe(pd.DataFrame({k: res[k] for k in ("coef_a", "coef_b", "coef_c", "coef_d")}),
             use_container_width=True)

fig, ax = ui.figura()
xx = np.linspace(h_min, h_max, 400)
ax.plot(xx, f(xx), color=ui.TEAL, lw=2.5, label="spline")
ax.scatter(xs, ys, color=ui.AMBAR, zorder=5, label="nodos")
ax.axvline(h, color=ui.CORAL, ls="--", alpha=0.7)
ax.set_xlabel("h [m]")
ax.set_ylabel("Q [m³/s]")
ax.legend(facecolor="none", labelcolor=ui.HIELO)
st.pyplot(fig, transparent=True)
st.caption(f"Contraste con SciPy: {res['comparacion_libreria']}")
