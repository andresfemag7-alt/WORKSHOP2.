"""Conjunto de datos nivel–caudal compartido por las pestañas 3 y 4 (mismos nodos, mismo ajuste, misma validación)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from modulos.caso import datos_rio as dr
from . import componentes as ui

MODO_CASO = "Caso integrador (USGS 09380000 · nodos preliminares)"
MODO_PROPIO = "Mis propios nodos"


def _df_caso() -> pd.DataFrame:
    return pd.DataFrame({"h (m)": [r["h_m"] for r in dr.nodos_construccion()], "Q (m³/s)": [r["Q_m3s"] for r in dr.nodos_construccion()]})


def selector_datos() -> dict:
    """Se dibuja SOLO en la pestaña 3. Guarda el resultado en session_state['datos_activos'] para la pestaña 4."""
    modo = st.radio("Origen de los nodos", [MODO_CASO, MODO_PROPIO], key="modo_datos", horizontal=True)
    out = {"ok": False, "modo": modo, "mensajes": []}
    if modo == MODO_CASO:
        nodos = dr.nodos_construccion()
        ui.tabla_html([{"Nodo": r["id"], "Nivel (ft)": f"{r['nivel_ft']:g}", "Caudal (cfs)": f"{r['caudal_cfs']:g}",
                        "<i>h</i> (m)": f"{r['h_m']:.5f}", "<i>Q</i> (m³/s)": f"{r['Q_m3s']:.4f}"} for r in nodos], izquierda=True)
        st.caption("Conversión con factores exactos: $h = \\mathrm{ft}\\times 0.3048$; $Q = \\mathrm{cfs}\\times 0.028316846592$. Se conserva la precisión completa "
                   "(la propuesta original redondeaba a 3 y 2 decimales: 1.829 m, 84.95 m³/s…).")
        out.update(ok=True, h=[r["h_m"] for r in nodos], Q=[r["Q_m3s"] for r in nodos],
                   validacion=[dr.observacion_validacion()], pendiente=dr.observacion_pendiente(), procedencia="preliminar")
    else:
        if "df_propios" not in st.session_state:
            st.session_state["df_propios"] = _df_caso()
        st.caption("Edite, agregue o elimine filas. Unidades: h en m, Q en m³/s. Se rechazan nodos repetidos o no numéricos.")
        ed = st.data_editor(st.session_state["df_propios"], num_rows="dynamic", key="ed_nodos", width="stretch", hide_index=True)
        df = ed.apply(pd.to_numeric, errors="coerce")
        if df.isna().any(axis=None):
            out["mensajes"].append("Hay celdas vacías o no numéricas: complete o elimine esas filas.")
        else:
            h, Q = df["h (m)"].tolist(), df["Q (m³/s)"].tolist()
            if len(h) < 2:
                out["mensajes"].append("Se necesitan al menos 2 nodos.")
            elif len(set(np.round(h, 12))) < len(h):
                out["mensajes"].append("Hay nodos con el mismo nivel h repetido.")
            elif any(v <= 0 for v in h) or any(v <= 0 for v in Q):
                out["mensajes"].append("Nivel y caudal deben ser positivos.")
            else:
                out.update(ok=True, h=h, Q=Q, validacion=[], pendiente=None, procedencia="editado")
        with st.expander("Observaciones de validación propias (opcional, no se usan en la construcción)"):
            if "df_val_propios" not in st.session_state:
                st.session_state["df_val_propios"] = pd.DataFrame({"h (m)": pd.Series(dtype=float), "Q (m³/s)": pd.Series(dtype=float)})
            ev = st.data_editor(st.session_state["df_val_propios"], num_rows="dynamic", key="ed_val", width="stretch", hide_index=True)
            ev = ev.apply(pd.to_numeric, errors="coerce").dropna()
            if out["ok"]:
                out["validacion"] = [{"id": f"V{i + 1}", "h_m": float(r["h (m)"]), "Q_m3s": float(r["Q (m³/s)"]), "nivel_ft": None, "caudal_cfs": None}
                                     for i, r in ev.reset_index(drop=True).iterrows()]
    for m in out["mensajes"]:
        st.error(m)
    st.session_state["datos_activos"] = out
    return out


def datos_activos() -> dict:
    return st.session_state.get("datos_activos", {"ok": False, "mensajes": ["Los datos se configuran en la pestaña 3."]})
