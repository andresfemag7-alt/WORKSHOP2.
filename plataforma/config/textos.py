"""Títulos, descripciones y mensajes centralizados (editar aquí, no en las pestañas)."""

APP_TITULO = "Métodos numéricos aplicados a una captación y derivación hídrica"
APP_SUBTITULO = "Algoritmos Numéricos · Ingeniería Civil - Aplicación de los métodos a la ingeniería - Estudiantes: Sebastian Molina & Andrés Madroñero - Docente: Mg.Mario Hernan Lopez Arbelaez"

ADVERTENCIA_MODELO = (
    "**Modelo académico conceptual — no es un diseño listo para construir.** Un proyecto real de captación requeriría "
    "topografía, hidrología de diseño y análisis de crecientes, estudios geotécnicos, materiales, cargas completas "
    "(peso propio, sobrecargas, viento, sismo), normativa aplicable, análisis estructural detallado, factores de "
    "seguridad y revisión por profesionales competentes. La profundidad crítica es un parámetro del régimen de flujo: "
    "no garantiza estabilidad, borde libre ni seguridad del canal.")

CONTEXTO = (
    "**Caso integrador.** Se capta agua del río Colorado y se deriva por un canal rectangular de concreto hacia una "
    "planta de tratamiento; en un tramo sobre una depresión, el canal se apoya en una armadura de acero. "
    "Cada pestaña resuelve UNA etapa con UN método:")

FLUJO_PASOS = [
    ("3·4 Interpolación", "nivel h → caudal total Q_total (curva de descarga)"),
    ("2 No lineales", "Q_d = α·Q_total → profundidad crítica y_c"),
    ("1 Lineales", "y_c → peso del agua → cargas nodales → fuerzas internas y reacciones"),
]

TABS = {
    "lineales": {
        "nombre": "1 · Sistemas lineales",
        "titulo": "Equilibrio estático de la armadura de soporte",
        "descripcion": "Eliminación de Gauss con pivoteo parcial aplicada al equilibrio de nudos de una armadura Warren.",
        "problema": "¿Qué fuerza axial soporta cada barra y cuánto valen las reacciones cuando el canal con agua descansa sobre la armadura?",
        "metodo": "Eliminación de Gauss con pivoteo parcial por columnas + sustitución regresiva sobre $A \\cdot x = b$.",
        "entradas": "Geometría (luz $L$, altura $H$), peso del agua del tramo (de $y_c$ o manual).",
        "resultado": "Fuerzas axiales (tracción +, compresión −), reacciones, residual $r = A \\cdot x - b$ y equilibrio global.",
        "limites": "Solo peso del agua; sin peso propio, sobrecargas ni factores de seguridad. Geometría y apoyos son supuestos del escenario.",
    },
    "no_lineales": {
        "nombre": "2 · Sistemas no lineales",
        "titulo": "Profundidad crítica del canal rectangular",
        "descripcion": "Punto fijo simultáneo y Newton-Raphson para sistemas, aplicados a las dos condiciones del flujo crítico.",
        "problema": "¿A qué profundidad $y_c$ el flujo del caudal derivado $Q_d$ es crítico ($Fr = 1$) en un canal de ancho $b$?",
        "metodo": "Sistema $2 \\times 2$ en $(y, V)$: $Fr = 1$ y continuidad. También se resuelve la ecuación escalar equivalente como caso $1 \\times 1$ con el mismo Newton.",
        "entradas": "$Q_d = \\alpha \\cdot Q_{total}$, ancho $b$, gravedad $g$, aproximación inicial, tolerancias y máximo de iteraciones.",
        "resultado": "$y_c$ [m], velocidad crítica, $Fr$, historial iterativo (cambio y residual por separado) y motivo de parada.",
        "limites": "$y_c$ no es el tirante normal ni el de operación; no garantiza borde libre. Ancho $b$ y fracción $\\alpha$ son supuestos.",
    },
    "lagrange": {
        "nombre": "3 · Interpolación de Lagrange",
        "titulo": "Caudal del río a partir del nivel (curva de descarga)",
        "descripcion": "Polinomio de Lagrange único por los nodos nivel–caudal de la estación USGS 09380000.",
        "problema": "¿Cuánto caudal total $Q$ lleva el río para un nivel $h$ medido en la estación de aforo?",
        "metodo": "Interpolación polinomial de Lagrange: $$P(h) = \\sum Q_i L_i(h)$$.",
        "entradas": "Nodos $(h_i, Q_i)$ en m y $m^3/s$; nivel consultado $h$ dentro del intervalo.",
        "resultado": "$Q_{total}$ estimado [$m^3/s$], bases $L_i$, polinomio, reproducción de nodos y contraste con la lectura de validación.",
        "limites": "Nodos preliminares no verificados; el rating cambia con el tiempo; el caudal del tramo está regulado por una presa; no extrapola.",
    },
    "newton": {
        "nombre": "4 · Newton + Spline",
        "titulo": "Newton y spline cúbico sobre los mismos datos",
        "descripcion": "Diferencias divididas de Newton y spline cúbico natural, comparados con Lagrange con idénticos nodos y validación.",
        "problema": "¿Cambia la estimación de $Q$ según el método de interpolación? ¿Cuál reproduce mejor la lectura de validación?",
        "metodo": "Newton (diferencias divididas, Horner) = mismo polinomio que Lagrange; spline cúbico natural = interpolación por tramos.",
        "entradas": "Los mismos nodos y nivel consultado de la pestaña 3; nodo adicional opcional (didáctico).",
        "resultado": "Tabla de diferencias divididas, coeficientes, comparación de predicciones, MAE/RMSE/error máximo y gráfica conjunta.",
        "limites": "Con una sola observación de validación las métricas globales son poco representativas.",
    },
}

MSG_SIN_FLUJO = "Aún no hay un valor aguas arriba publicado. Calcule y publique el paso anterior, o use el modo manual."
