"""Notación matemática de la INTERFAZ (capa visual solamente).

Reglas de esta capa:
  * Solo cambia cómo se MUESTRAN las fórmulas en textos, títulos, subtítulos y mensajes. No toca los módulos
    numéricos (``modulos/``) ni los valores calculados.
  * No se aplica a tablas (``st.dataframe``, ``tabla_variables``): allí el contenido se muestra tal cual.
  * Streamlit renderiza ``$...$`` en markdown, caption, encabezados, métricas, etiquetas de campos, radios, botones,
    expanders, pestañas, alertas y tooltips ``help=``. NO lo renderiza en las opciones de un ``selectbox`` ni dentro de
    bloques HTML crudos: ahí no se usan fórmulas.
  * Las constantes son cadenas CRUDAS (r"...") porque LaTeX usa barra invertida: en una cadena normal ``\\a``, ``\\r``,
    ``\\t``, ``\\b`` y ``\\f`` serían caracteres de control.

Convenciones: vectores y matrices en negrita (``\\mathbf``), subíndices de palabra en texto (``Q_\\text{total}``),
número de Froude en romano (``\\mathrm{Fr}``), normas con ``\\lVert \\rVert``.
"""
from __future__ import annotations

import re

# ----------------------------------------------------------------------------- símbolos del caso
QT = r"$Q_\text{total}$"
QD = r"$Q_d$"
YC = r"$y_c$"
VC = r"$V_c$"
HC = r"$h_c$"
H = r"$h$"
Q = r"$Q$"
ALFA = r"$\alpha$"
RHO = r"$\rho$"
THETA = r"$\theta$"
KAPPA_A = r"$\kappa(\mathbf{A})$"
FR = r"$\mathrm{Fr}$"
AXB = r"$\mathbf{A}\mathbf{x}=\mathbf{b}$"
RESIDUAL = r"$\mathbf{r}=\mathbf{A}\mathbf{x}-\mathbf{b}$"
NORMA_DX = r"$\lVert\Delta\mathbf{x}\rVert_\infty$"
NORMA_F = r"$\lVert\mathbf{F}\rVert_\infty$"
JDX = r"$\mathbf{J}\,\Delta\mathbf{x}=-\mathbf{F}$"


def sub(base: str, indice) -> str:
    """Símbolo con subíndice, p. ej. sub('a', 3) -> '$a_{3}$' (con llaves: vale para índices de varios caracteres)."""
    return "$" + base + "_{" + str(indice) + "}$"


def fila(n) -> str:
    """Fila de una matriz: '$F_{2}$'."""
    return sub("F", n)


# ----------------------------------------------------------------------------- mensajes de los módulos
# Se usan FUNCIONES de reemplazo (no cadenas): en re.sub una cadena como r"\lVert" lanzaría «bad escape».
_REEMPLAZOS = [
    (re.compile(r"\|\|dx\|\|_inf"), lambda m: NORMA_DX),
    (re.compile(r"\|\|F\|\|_inf"), lambda m: NORMA_F),
    (re.compile(r"\|x\|"), lambda m: r"$\lVert\mathbf{x}\rVert$"),
    (re.compile(r"kappa\(A\)"), lambda m: KAPPA_A),
    (re.compile(r"\bkappa\b"), lambda m: r"$\kappa$"),
    (re.compile(r"\bcond\s*="), lambda m: r"$\kappa(\mathbf{J})=$"),
    (re.compile(r"<="), lambda m: r"$\le$"),
    (re.compile(r">="), lambda m: r"$\ge$"),
    (re.compile(r"(?<=\s)>(?=\s)"), lambda m: r"$>$"),
    (re.compile(r"(?<=[\s(])<(?=\s)"), lambda m: r"$<$"),
    # intervalo "[a, b]" entre dos números
    (re.compile(r"\[(-?[0-9][0-9.eE+-]*),\s*(-?[0-9][0-9.eE+-]*)\]"),
     lambda m: "$[" + m.group(1) + r",\," + m.group(2) + "]$"),
]


def mensaje(texto, var: str = "x") -> str:
    """Muestra con LaTeX la notación en texto plano de los mensajes que generan los módulos (no los modifica).

    ``var`` es el nombre con que la interfaz llama a la variable independiente: "h" en las pestañas 3 y 4
    (los módulos, que son genéricos, hablan de "x").
    """
    if not isinstance(texto, str):
        return ""
    reglas = _REEMPLAZOS + [(re.compile(r"\bx = ([-+0-9.eE]+) está"),
                             lambda m: "$" + var + " = " + m.group(1) + "$ está")]
    t = texto
    for patron, f in reglas:
        # Solo se reescribe FUERA de los tramos $...$: lo ya convertido no se vuelve a tocar
        # (p. ej. el "kappa" dentro de "\kappa" no debe coincidir otra vez).
        partes = re.split(r"(\$[^$]*\$)", t)
        t = "".join(p if i % 2 else patron.sub(f, p) for i, p in enumerate(partes))
    return t


# ----------------------------------------------------------------------------- polinomios (para st.latex)
def _bloque(izquierda: str, terminos: list, por_linea: int) -> str:
    """``izquierda = t0 ± t1 ± ...`` repartido en líneas de ``por_linea`` términos (un renglón largo se desborda).

    ``terminos`` es una lista de (signo, texto) con signo '', '+' o '-'; el primer término lleva su signo dentro del texto.
    """
    def unir(grupo, primera_linea):
        partes = []
        for i, (sig, t) in enumerate(grupo):
            partes.append(t if (primera_linea and i == 0) or not sig else sig + " " + t)
        return " ".join(partes)

    grupos = [terminos[i:i + por_linea] for i in range(0, len(terminos), por_linea)]
    if len(grupos) == 1:
        return izquierda + "=" + unir(grupos[0], True)
    lineas = []
    for k, g in enumerate(grupos):
        lineas.append(izquierda + " &= " + unir(g, True) if k == 0 else r"&\quad " + unir(g, False))
    return r"\begin{aligned}" + r" \\ ".join(lineas) + r"\end{aligned}"


def poli_latex(texto: str, var_origen: str = "x", var: str = "h", nombre: str = "P", por_linea: int = 4) -> str:
    """'5.3 x^2 - 19.3 x + 16.0' (salida de ``texto_polinomio``) -> LaTeX con la variable ``var`` y líneas cortas."""
    t = re.sub(r"\b" + re.escape(var_origen) + r"\b", var, texto.strip())
    partes = re.split(r"\s([+-])\s", t)
    terminos = [("", partes[0])]
    for i in range(1, len(partes), 2):
        terminos.append((partes[i], partes[i + 1]))
    limpios = []
    for sig, term in terminos:
        term = re.sub(r"\^(\d+)", lambda m: "^{" + m.group(1) + "}", term)
        term = re.sub(r"(\d) (" + re.escape(var) + r")", lambda m: m.group(1) + r"\," + m.group(2), term)
        limpios.append((sig, term))
    return _bloque(nombre + "(" + var + ")", limpios, por_linea)


def _factor(var: str, x: float) -> str:
    return "(" + var + "-" + format(x, "g") + ")" if x >= 0 else "(" + var + "+" + format(-x, "g") + ")"


def newton_latex(coef, nodos, var: str = "h", nombre: str = "P", por_linea: int = 2) -> str:
    """Forma de Newton  a0 + a1(h-h0) + a2(h-h0)(h-h1) + ...  con coeficientes numéricos, en varias líneas."""
    terminos = []
    for k, a in enumerate(coef):
        cuerpo = format(abs(float(a)), ".6f") + "".join(_factor(var, nodos[j]) for j in range(k))
        if k == 0:
            terminos.append(("", ("-" if a < 0 else "") + cuerpo))
        else:
            terminos.append(("-" if a < 0 else "+", cuerpo))
    return _bloque(nombre + "(" + var + ")", terminos, por_linea)
