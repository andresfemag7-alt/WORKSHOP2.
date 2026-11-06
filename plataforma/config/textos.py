"""Títulos, descripciones y mensajes centralizados (editar aquí, no en las pestañas)."""

APP_TITULO = "Métodos numéricos aplicados a una captación y derivación hídrica"
APP_SUBTITULO = "Algoritmos Numéricos · Ingeniería Civil - Aplicación de los métodos a la ingeniería"

ADVERTENCIA_MODELO = (
    "**Modelo académico conceptual — no es un diseño listo para construir.** Un proyecto real de captación requeriría "
    "topografía, hidrología de diseño y análisis de crecientes, estudios geotécnicos, materiales, cargas completas "
    "(peso propio, sobrecargas, viento, sismo), normativa aplicable, análisis estructural detallado, factores de "
    "seguridad y revisión por profesionales competentes. La profundidad crítica es un parámetro del régimen de flujo: "
    "no garantiza estabilidad, borde libre ni seguridad del canal.")

CONTEXTO = (
    "**Caso integrador.** Una captación toma agua del río Colorado (estación USGS 09380000, Lees Ferry) y la deriva por un "
    "canal rectangular de concreto hacia una planta de tratamiento. En un tramo el terreno se hunde y el canal pasa por "
    "encima, apoyado en una armadura de acero tipo Warren. Para dimensionar ese tramo hay que responder tres preguntas "
    "encadenadas. Ninguna tiene una fórmula directa que lo resuelva todo, por eso cada una se resuelve con un método "
    "numérico distinto: se aproxima la respuesta con cálculos repetidos y se controla el error en cada paso.")

CADENA = (
    r"**Cómo se encadenan.** Solo viajan tres valores entre pestañas: $Q_\text{total}$ (caudal del río), "
    r"$Q_d=\alpha\,Q_\text{total}$ (caudal derivado al canal) y $y_c$ (profundidad crítica). El resultado de una "
    "pestaña es la entrada de la siguiente; se calcula en el orden 3 → 4 → 2 → 1, aunque las pestañas se muestren "
    "numeradas 1 a 4. Un valor solo se publica si el cálculo convergió y no es una extrapolación.")

# Una entrada por método, en el orden del flujo de datos. Claves: pestana, pregunta, metodo, uso, entrega.
GUIA_METODOS = [
    {
        "pestana": "Pestaña 3 · Interpolación de Lagrange",
        "pregunta": r"¿Cuánto caudal lleva el río? La estación mide el nivel $h$, no el caudal $Q$; solo se conocen "
                    r"unos pocos pares $(h_i,\,Q_i)$ de la curva de descarga.",
        "metodo": r"Se construye UN polinomio $P(h)=\sum_{i=0}^{n} Q_i\,L_i(h)$ que pasa exactamente por todos los nodos. "
                  r"Cada base $L_i(h)$ vale 1 en su propio nodo $h_i$ y 0 en los demás, así que cerca de cada dato "
                  r"solo pesa su pieza. Con 5 nodos el polinomio es de grado 4.",
        "uso": r"Se introduce el nivel medido $h$ y se obtiene $Q_\text{total}$. La app comprueba que el polinomio "
               r"devuelve los nodos originales y lo contrasta con una lectura real de validación. Solo es válido "
               r"entre el menor y el mayor nivel de los nodos: fuera de ese rango sería extrapolar y no se publica.",
        "entrega": r"$Q_\text{total}$",
    },
    {
        "pestana": "Pestaña 4 · Newton y spline cúbico",
        "pregunta": "¿Cambia la estimación según cómo se interpole? ¿Cuál se acerca más a la lectura real?",
        "metodo": r"**Newton (diferencias divididas):** es el MISMO polinomio de Lagrange escrito de otra forma, "
                  r"$P(h)=a_0+a_1(h-h_0)+a_2(h-h_0)(h-h_1)+\cdots$; al agregar un nodo solo aparece un coeficiente "
                  r"nuevo y los anteriores no cambian. **Spline cúbico natural:** en vez de una sola curva usa un "
                  r"cúbico por cada intervalo, empalmados con suavidad y con curvatura nula en los extremos; evita "
                  r"las oscilaciones de un polinomio de grado alto.",
        "uso": "Se usan los mismos nodos y el mismo nivel de la pestaña 3. La app compara los tres métodos contra la "
               "observación de validación (error medio, cuadrático y máximo) y verifica que el spline sea monótono, "
               "porque un caudal no puede bajar cuando el nivel sube.",
        "entrega": "Contraste de los tres métodos; confirma el valor de $Q_\\text{total}$ que se publica.",
    },
    {
        "pestana": "Pestaña 2 · Sistemas no lineales",
        "pregunta": r"¿A qué profundidad $y_c$ es crítico el flujo del caudal derivado $Q_d$ en un canal de ancho $b$? "
                    r"Flujo crítico significa $\mathrm{Fr}=V/\sqrt{g\,y}=1$.",
        "metodo": r"Dos condiciones con dos incógnitas $(y,\,V)$: $V^2=g\,y$ y la continuidad $b\,y\,V=Q_d$. Como "
                  r"aparecen $V^2$ y el producto $y\,V$, el sistema es no lineal y se resuelve por aproximaciones "
                  r"sucesivas. **Punto fijo:** despeja $y=Q_d/(b\,V)$ y $V=\sqrt{g\,y}$ y repite hasta que ya no "
                  r"cambien; es simple pero lento. **Newton-Raphson:** en cada paso linealiza con el jacobiano y "
                  r"resuelve $\mathbf{J}\,\Delta\mathbf{x}=-\mathbf{F}$; converge en muchas menos iteraciones.",
        "uso": r"Se fijan $\alpha$, $b$, $g$ y una aproximación inicial. El cálculo para cuando el cambio entre "
               r"iteraciones y el residual son pequeños a la vez. La app lo verifica contra la fórmula exacta "
               r"$y_c=\sqrt[3]{Q_d^2/(g\,b^2)}$. Ojo: $y_c$ es una profundidad de referencia del régimen de flujo, "
               r"no la profundidad de operación del canal.",
        "entrega": r"$y_c$",
    },
    {
        "pestana": "Pestaña 1 · Sistemas lineales",
        "pregunta": "¿Qué fuerza soporta cada barra de la armadura y cuánto valen las reacciones en los apoyos "
                    "cuando el canal lleno descansa sobre ella?",
        "metodo": r"Con $y_c$ se calcula el peso del agua del tramo, $W=\rho\,g\,b\,y_c\,L$, y se reparte en los "
                  r"nudos. El método de los nudos exige equilibrio en $x$ y en $y$ en cada nudo: 5 nudos dan 10 "
                  r"ecuaciones para 10 incógnitas (7 barras y 3 reacciones), es decir "
                  r"$\mathbf{A}\mathbf{x}=\mathbf{b}$. Se resuelve por **eliminación de Gauss con pivoteo parcial** "
                  r"(se triangulariza la matriz eligiendo el pivote mayor de cada columna) y sustitución regresiva.",
        "uso": r"Se fijan la luz $L$ y la altura $H$ de la armadura. Positivo es tracción y negativo compresión. La app "
               r"verifica el resultado con el residual $\mathbf{r}=\mathbf{A}\mathbf{x}-\mathbf{b}$, el número de "
               r"condición $\kappa(\mathbf{A})$ y el equilibrio global: la suma de las reacciones debe igualar $W$.",
        "entrega": "Fuerzas axiales en las 7 barras y las 3 reacciones.",
    },
]

# Se conserva por compatibilidad; el cuadro de alcance ahora usa GUIA_METODOS.
FLUJO_PASOS = [
    ("3·4 Interpolación", r"nivel $h$ → caudal total $Q_\text{total}$ (curva de descarga)"),
    ("2 No lineales", r"$Q_d=\alpha\,Q_\text{total}$ → profundidad crítica $y_c$"),
    ("1 Lineales", r"$y_c$ → peso del agua → cargas nodales → fuerzas internas y reacciones"),
]

TABS = {
    "lineales": {
        "nombre": "1 · Sistemas lineales",
        "titulo": "Equilibrio estático de la armadura de soporte",
        "descripcion": "Eliminación de Gauss con pivoteo parcial aplicada al equilibrio de nudos de una armadura Warren.",
        "problema": "¿Qué fuerza axial soporta cada barra y cuánto valen las reacciones cuando el canal con agua descansa sobre la armadura?",
        "metodo": r"Eliminación de Gauss con pivoteo parcial por columnas + sustitución regresiva sobre $\mathbf{A}\mathbf{x}=\mathbf{b}$.",
        "entradas": r"Geometría (luz $L$, altura $H$), peso del agua del tramo (de $y_c$ o manual).",
        "resultado": r"Fuerzas axiales (tracción +, compresión −), reacciones, residual $\mathbf{r}=\mathbf{A}\mathbf{x}-\mathbf{b}$ y equilibrio global.",
        "limites": "Solo peso del agua; sin peso propio, sobrecargas ni factores de seguridad. Geometría y apoyos son supuestos del escenario.",
    },
    "no_lineales": {
        "nombre": "2 · Sistemas no lineales",
        "titulo": "Profundidad crítica del canal rectangular",
        "descripcion": "Punto fijo simultáneo y Newton-Raphson para sistemas, aplicados a las dos condiciones del flujo crítico.",
        "problema": r"¿A qué profundidad $y_c$ el flujo del caudal derivado $Q_d$ es crítico ($\mathrm{Fr}=1$) en un canal de ancho $b$?",
        "metodo": r"Sistema 2×2 en $(y,\,V)$: $\mathrm{Fr}=1$ y continuidad. También se resuelve la ecuación escalar equivalente como caso 1×1 con el mismo Newton.",
        "entradas": r"$Q_d=\alpha\,Q_\text{total}$, ancho $b$, gravedad $g$, aproximación inicial, tolerancias y máximo de iteraciones.",
        "resultado": r"$y_c$ [m], velocidad crítica, $\mathrm{Fr}$, historial iterativo (cambio y residual por separado) y motivo de parada.",
        "limites": r"$y_c$ no es el tirante normal ni el de operación; no garantiza borde libre. Ancho $b$ y fracción $\alpha$ son supuestos.",
    },
    "lagrange": {
        "nombre": "3 · Interpolación de Lagrange",
        "titulo": "Caudal del río a partir del nivel (curva de descarga)",
        "descripcion": "Polinomio de Lagrange único por los nodos nivel–caudal de la estación USGS 09380000.",
        "problema": r"¿Cuánto caudal total $Q$ lleva el río para un nivel $h$ medido en la estación de aforo?",
        "metodo": r"Interpolación polinomial de Lagrange: $P(h)=\sum_{i=0}^{n} Q_i\,L_i(h)$.",
        "entradas": r"Nodos $(h_i,\,Q_i)$ en m y m³/s; nivel consultado $h$ dentro del intervalo.",
        "resultado": r"$Q_\text{total}$ estimado [m³/s], bases $L_i$, polinomio, reproducción de nodos y contraste con la lectura de validación.",
        "limites": "Nodos preliminares no verificados; el rating cambia con el tiempo; el caudal del tramo está regulado por una presa; no extrapola.",
    },
    "newton": {
        "nombre": "4 · Newton + Spline",
        "titulo": "Newton y spline cúbico sobre los mismos datos",
        "descripcion": "Diferencias divididas de Newton y spline cúbico natural, comparados con Lagrange con idénticos nodos y validación.",
        "problema": r"¿Cambia la estimación de $Q$ según el método de interpolación? ¿Cuál reproduce mejor la lectura de validación?",
        "metodo": "Newton (diferencias divididas, Horner) = mismo polinomio que Lagrange; spline cúbico natural = interpolación por tramos.",
        "entradas": "Los mismos nodos y nivel consultado de la pestaña 3; nodo adicional opcional (didáctico).",
        "resultado": "Tabla de diferencias divididas, coeficientes, comparación de predicciones, MAE/RMSE/error máximo y gráfica conjunta.",
        "limites": "Con una sola observación de validación las métricas globales son poco representativas.",
    },
}

MSG_SIN_FLUJO = "Aún no hay un valor aguas arriba publicado. Calcule y publique el paso anterior, o use el modo manual."
