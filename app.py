"""Plataforma web · Workshop 2 · Métodos numéricos aplicados a una captación y derivación hídrica.

Ejecución local:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from plataforma import componentes as ui
from plataforma import estado
from plataforma.config import tema, textos
from plataforma.tabs import lagrange, lineales, newton, no_lineales

st.set_page_config(page_title="Workshop 2 · Métodos numéricos", layout="wide")
tema.aplicar_tema()

st.markdown(f'<p class="app-titulo">{textos.APP_TITULO}</p><p class="app-sub">{textos.APP_SUBTITULO}</p>', unsafe_allow_html=True)
with st.expander(" Alcance del modelo (léalo antes de interpretar resultados)", expanded=False):
    st.markdown(textos.ADVERTENCIA_MODELO)
    st.markdown(textos.CONTEXTO)
    st.markdown(textos.CADENA)
    for m in textos.GUIA_METODOS:
        with st.container(border=True):
            st.markdown("**" + m["pestana"] + "**")
            st.markdown("**Pregunta.** " + m["pregunta"])
            st.markdown("**Cómo funciona.** " + m["metodo"])
            st.markdown("**Cómo se usa en la app.** " + m["uso"])
            st.markdown("**Entrega a la cadena:** " + m["entrega"])

panel = st.container()  # se rellena al final para reflejar los valores publicados en esta misma ejecución

orden = ["lineales", "no_lineales", "lagrange", "newton"]
tabs = dict(zip(orden, st.tabs([f"{tema.ICONOS[k]} {textos.TABS[k]['nombre']}" for k in orden])))

# Orden de EJECUCIÓN = orden del flujo de datos (3 → 4 → 2 → 1); el orden VISUAL de las pestañas no cambia.
with tabs["lagrange"]:
    lagrange.render()
with tabs["newton"]:
    newton.render()
with tabs["no_lineales"]:
    no_lineales.render()
with tabs["lineales"]:
    lineales.render()

with panel:
    with st.expander(" Flujo de datos entre pestañas (qué valor viene de dónde)", expanded=False):
        q = estado.obtener("q_total")
        filas = []
        SIM = {"q_total": "<i>Q</i><sub>total</sub>", "q_d": "<i>Q</i><sub>d</sub>", "y_c": "<i>y</i><sub>c</sub>"}
        for clave in ("q_total", "q_d", "y_c"):
            simbolo = f"<b>{SIM[clave]}</b>"
            it = estado.obtener(clave)
            if not it:
                filas.append({"Símbolo": simbolo, "Valor": "—", "Unidad": "—", "Calculado por": "sin publicar", "Hora": "—", "Estado": "pendiente"})
                continue
            viejo = clave != "q_total" and q is not None and not estado.iguales({"Q": it["entradas"].get("Q_total", -1.0)}, {"Q": q["valor"]})
            filas.append({"Símbolo": simbolo, "Valor": ui.fmt(it["valor"], 4), "Unidad": it["unidad"], "Calculado por": it["modulo"],
                          "Hora": it["hora"],
                          "Estado": f"⚠️ desactualizado (<i>Q</i><sub>total</sub> cambió)" if viejo else "✅ vigente"})
        ui.tabla_html(filas)
        st.caption("Cada pestaña funciona también de forma independiente. Un valor solo se publica si el cálculo convergió y no es una extrapolación; "
                   "si cambia un valor aguas arriba, los de abajo se marcan como desactualizados hasta recalcularlos.")
        if st.button("Restablecer valores publicados", key="reset_flujo"):
            estado.restablecer_todo()
            st.rerun()
