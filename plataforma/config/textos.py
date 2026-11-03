"""Títulos, descripciones y mensajes centralizados (editar aquí, no en las pestañas)."""

APP_TITULO = "Métodos numéricos aplicados a una captación y derivación hídrica"
APP_SUBTITULO = (
    "Algoritmos Numéricos · Ingeniería Civil - Aplicación de los métodos a la ingeniería - "
    "Sebastian Molina & Andrés Madroñero. - "
    "Docente: Mg.Mario Hernan Lopez Arbelaez")

ADVERTENCIA_MODELO = (
    "**Modelo académico, no un diseño para construir.** Un proyecto real exigiría topografía, hidrología de diseño, "
    "estudios geotécnicos, cargas completas (peso propio, viento, sismo), normativa y factores de seguridad. "
    "Aquí la armadura soporta solo el peso del agua, y la profundidad crítica es un parámetro del flujo: "
    "no garantiza estabilidad, borde libre ni seguridad del canal.")

CONTEXTO = (
    "**Caso integrador.** Se capta agua del río Colorado (estación USGS 09380000) y se deriva por un canal rectangular "
    "de concreto hacia una planta de tratamiento. En un tramo sobre una depresión, el canal se apoya en una armadura "
    "de acero tipo Warren. Cada pestaña resuelve una etapa con un método numérico, y su resultado alimenta a la siguiente:")

FLUJO_PASOS = [
    ("3·4 Interpolación", r"con el nivel del río $\color{#0B5C8E}{\mathbf{h}}$ se estima el caudal total $\color{#0B5C8E}{\mathbf{Q_{total}}}$ (Lagrange, Newton y spline)"),
    ("2 No lineales", r"se deriva una fracción del caudal, $\color{#0B5C8E}{\mathbf{Q_d = \alpha \cdot Q_{total}}}$, y se calcula la profundidad crítica $\color{#0B5C8E}{\mathbf{y_c}}$ (punto fijo y Newton-Raphson)"),
    ("1 Lineales", r"con $\color{#0B5C8E}{\mathbf{y_c}}$ se obtiene el peso del agua, las cargas en los nudos, las fuerzas en cada barra y las reacciones (eliminación de Gauss)"),
]


TABS = {

    "lineales": {

        "nombre": "1 · Sistemas lineales",

        "titulo": "Equilibrio estático de la armadura de soporte",

        "descripcion": "Eliminación de Gauss con pivoteo parcial aplicada al equilibrio de nudos de una armadura Warren.",

        "problema": "¿Qué fuerza axial soporta cada barra y cuánto valen las reacciones cuando el canal con agua descansa sobre la armadura?",

        "metodo": "Eliminación de Gauss con pivoteo parcial por columnas + sustitución regresiva sobre <span class=\"mat\">A·x = b</span>.",

        "entradas": "Geometría (luz <span class=\"mat\">L</span>, altura <span class=\"mat\">H</span>), peso del agua del tramo (de <span class=\"mat\">y<sub>c</sub></span> o manual).",

        "resultado": "Fuerzas axiales (tracción +, compresión −), reacciones, residual <span class=\"mat\">r = A·x − b</span> y equilibrio global.",

        "limites": "Solo peso del agua; sin peso propio, sobrecargas ni factores de seguridad. Geometría y apoyos son supuestos del escenario.",

    },

    "no_lineales": {

        "nombre": "2 · Sistemas no lineales",

        "titulo": "Profundidad crítica del canal rectangular",

        "descripcion": "Punto fijo simultáneo y Newton-Raphson para sistemas, aplicados a las dos condiciones del flujo crítico.",

        "problema": "¿A qué profundidad <span class=\"mat\">y<sub>c</sub></span> el flujo del caudal derivado <span class=\"mat\">Q<sub>d</sub></span> es crítico (<span class=\"mat\">Fr = 1</span>) en un canal de ancho <span class=\"mat\">b</span>?",

        "metodo": "Sistema 2×2 en <span class=\"mat\">(y, V)</span>: <span class=\"mat\">Fr = 1</span> y continuidad. También se resuelve la ecuación escalar equivalente como caso 1×1 con el mismo Newton.",

        "entradas": "<span class=\"mat\">Q<sub>d</sub> = α·Q<sub>total</sub></span>, ancho <span class=\"mat\">b</span>, gravedad <span class=\"mat\">g</span>, aproximación inicial, tolerancias y máximo de iteraciones.",

        "resultado": "<span class=\"mat\">y<sub>c</sub></span> [m], velocidad crítica, <span class=\"mat\">Fr</span>, historial iterativo (cambio y residual por separado) y motivo de parada.",

        "limites": "<span class=\"mat\">y<sub>c</sub></span> no es el tirante normal ni el de operación; no garantiza borde libre. Ancho <span class=\"mat\">b</span> y fracción <span class=\"mat\">α</span> son supuestos.",

    },

    "lagrange": {

        "nombre": "3 · Interpolación de Lagrange",

        "titulo": "Caudal del río a partir del nivel (curva de descarga)",

        "descripcion": "Polinomio de Lagrange único por los nodos nivel–caudal de la estación USGS 09380000.",

        "problema": "¿Cuánto caudal total <span class=\"mat\">Q</span> lleva el río para un nivel <span class=\"mat\">h</span> medido en la estación de aforo?",

        "metodo": "Interpolación polinomial de Lagrange: <span class=\"mat\">P(h) = Σ Q<sub>i</sub> L<sub>i</sub>(h)</span>.",

        "entradas": "Nodos <span class=\"mat\">(h<sub>i</sub>, Q<sub>i</sub>)</span> en m y m³/s; nivel consultado <span class=\"mat\">h</span> dentro del intervalo.",

        "resultado": "<span class=\"mat\">Q<sub>total</sub></span> estimado [m³/s], bases <span class=\"mat\">L<sub>i</sub></span>, polinomio, reproducción de nodos y contraste con la lectura de validación.",

        "limites": "Nodos preliminares no verificados; el rating cambia con el tiempo; el caudal del tramo está regulado por una presa; no extrapola.",

    },

    "newton": {

        "nombre": "4 · Newton + Spline",

        "titulo": "Newton y spline cúbico sobre los mismos datos",

        "descripcion": "Diferencias divididas de Newton y spline cúbico natural, comparados con Lagrange con idénticos nodos y validación.",

        "problema": "¿Cambia la estimación de <span class=\"mat\">Q</span> según el método de interpolación? ¿Cuál reproduce mejor la lectura de validación?",

        "metodo": "Newton (diferencias divididas, Horner) = mismo polinomio que Lagrange; spline cúbico natural = interpolación por tramos.",

        "entradas": "Los mismos nodos y nivel consultado de la pestaña 3; nodo adicional opcional (didáctico).",

        "resultado": "Tabla de diferencias divididas, coeficientes, comparación de predicciones, MAE/RMSE/error máximo y gráfica conjunta.",

        "limites": "Con una sola observación de validación las métricas globales son poco representativas.",

    },

}

MSG_SIN_FLUJO = "Aún no hay un valor aguas arriba publicado. Calcule y publique el paso anterior, o use el modo manual."
