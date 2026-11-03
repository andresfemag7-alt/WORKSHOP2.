"""Página de inicio. Ejecutar con:  streamlit run app.py"""
import streamlit as st

import ui

ui.iniciar("Workshop 2 · Algoritmos numéricos para ingeniería civil", "inicio")

st.markdown(
    """
Plataforma que integra métodos numéricos en un caso de ingeniería civil:
**hidrología → hidráulica → estructura**.

Usa el menú lateral para recorrer las páginas:

1. **Interpolación** – polinomios de Lagrange y Newton sobre la curva nivel–caudal.
2. **Spline cúbico** – interpolación por tramos de la misma curva.
3. **Sistemas lineales** – eliminación de Gauss con pivoteo aplicada a una armadura.
4. **Sistemas no lineales** – punto fijo y Newton–Raphson para el tirante crítico.
5. **Caso integrador** – de la lectura del río al esfuerzo en las barras.
"""
)
st.info(
    "Modelo académico conceptual. Los nodos nivel–caudal son preliminares y no están verificados "
    "contra la curva de descarga oficial de USGS (estación 09380000)."
)
