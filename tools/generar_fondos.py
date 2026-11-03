"""Genera una imagen de fondo por página de la app, usando los módulos reales del repositorio.

Uso (desde la raíz del repo):  python tools/generar_fondos.py
Salida: docs/img/fondo_<pagina>.png  (1920x1080, sin texto, pensadas para ir detrás del contenido).
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from modulos.caso import hidraulica as hid  # noqa: E402
from modulos.caso.datos_rio import arrays_nodos  # noqa: E402
from modulos.caso.estructura import armadura_warren_canal, resolver_armadura  # noqa: E402
from modulos.lagrange import bases_lagrange, lagrange_evaluar_directo  # noqa: E402
from modulos.newton_sistemas import newton_raphson_sistemas  # noqa: E402
from modulos.punto_fijo import punto_fijo_sistemas  # noqa: E402
from modulos.spline import spline_cubico_natural  # noqa: E402

SALIDA = RAIZ / "docs" / "img"
W, H = 19.2, 10.8   # pulgadas a 100 dpi -> 1920x1080

# Paleta común: azul petróleo profundo + turquesa + ámbar
BG_TOP, BG_BOT = "#071a26", "#0f3347"
TEAL, AMBAR, HIELO, CORAL = "#2dd4bf", "#f5b942", "#cfe8f1", "#ff7a6b"


def lienzo():
    """Figura de página completa con degradado vertical y un único eje transparente para dibujar."""
    fig = plt.figure(figsize=(W, H), dpi=100)
    fondo = fig.add_axes([0, 0, 1, 1])
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("bg", [BG_TOP, BG_BOT])
    fondo.imshow(grad, aspect="auto", cmap=cmap, extent=[0, 1, 0, 1])
    fondo.axis("off")
    ax = fig.add_axes([0.04, 0.06, 0.92, 0.88])
    ax.set_facecolor("none")
    ax.axis("off")
    return fig, ax


def rejilla(ax, xlim, ylim, n=14):
    for x in np.linspace(*xlim, n):
        ax.plot([x, x], ylim, color=HIELO, lw=0.6, alpha=0.06)
    for y in np.linspace(*ylim, int(n * 0.6)):
        ax.plot(xlim, [y, y], color=HIELO, lw=0.6, alpha=0.06)


def guardar(fig, nombre):
    SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = SALIDA / f"fondo_{nombre}.png"
    fig.savefig(ruta, dpi=100)
    plt.close(fig)
    print("OK", ruta.relative_to(RAIZ))


# ---------------------------------------------------------------- inicio
def fondo_inicio():
    """Collage: curva de descarga del río + armadura Warren + trayectoria de Newton, en capas."""
    fig, ax = lienzo()
    xs, ys = arrays_nodos()
    xx = np.linspace(min(xs), max(xs), 400)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    rejilla(ax, (0, 10), (0, 6))
    # curva nivel-caudal reescalada (el río), de izquierda a derecha, en la franja inferior
    s = spline_cubico_natural(xs, ys)["eval_func"]
    u = (xx - xx.min()) / (xx.max() - xx.min())
    v = s(xx)
    v = (v - v.min()) / (v.max() - v.min())
    for k, a in enumerate(np.linspace(0.05, 0.28, 7)):
        ax.fill_between(u * 10, 0, 0.6 + 1.6 * v * (0.55 + 0.07 * k), color=TEAL, alpha=a * 0.25, lw=0)
    ax.plot(u * 10, 0.6 + 1.6 * v, color=TEAL, lw=3, alpha=0.7)
    # armadura Warren en el centro-derecha
    sis = armadura_warren_canal(8.0, 1.6, 100.0)
    sol = resolver_armadura(sis)
    P = sis["nodos"]
    mx = max(abs(f) for f in sol["fuerzas_kN"].values())
    for nombre, a, b in sis["barras"]:
        f = sol["fuerzas_kN"][nombre]
        col = AMBAR if f > 1e-9 else CORAL if f < -1e-9 else HIELO
        (x1, y1), (x2, y2) = P[a], P[b]
        ax.plot([0.9 + x1 * 0.62, 0.9 + x2 * 0.62], [3.5 + y1 * 0.9, 3.5 + y2 * 0.9],
                color=col, lw=2 + 5 * abs(f) / mx, alpha=0.55, solid_capstyle="round")
    for (x, y) in P.values():
        ax.scatter(0.9 + x * 0.62, 3.5 + y * 0.9, s=160, color=HIELO, alpha=0.8, zorder=5)
    # trayectoria de Newton en el plano (y, V)
    Q, b, g = 20.0, 10.0, 9.81
    yc = hid.profundidad_critica_analitica(Q, b)
    F, J, _ = hid.sistema_critico(Q, b, g, yc)
    r = newton_raphson_sistemas(F, hid.aproximacion_inicial(Q, b, yc * 1.8), J=J)
    pts = np.array([h["x_k"] for h in r["historial"]] + [r["x_sol"]])
    px = 6.8 + (pts[:, 0] - pts[:, 0].min()) / (np.ptp(pts[:, 0]) + 1e-9) * 2.6
    py = 3.0 + (pts[:, 1] - pts[:, 1].min()) / (np.ptp(pts[:, 1]) + 1e-9) * 2.2
    ax.plot(px, py, "-o", color=AMBAR, lw=2.5, ms=14, alpha=0.6)
    ax.scatter(px[-1], py[-1], s=420, facecolors="none", edgecolors=TEAL, lw=3, alpha=0.9)
    guardar(fig, "inicio")


# ---------------------------------------------------------------- interpolación
def fondo_interpolacion():
    """Polinomio de grado 4 (Lagrange = Newton) con sus bases L_i y los nodos nivel-caudal."""
    fig, ax = lienzo()
    xs, ys = arrays_nodos()
    xs, ys = np.array(xs), np.array(ys)
    xx = np.linspace(xs.min(), xs.max(), 500)
    ymax = ys.max() * 1.12
    ax.set_xlim(xs.min() - 0.1, xs.max() + 0.1)
    ax.set_ylim(-ymax * 0.35, ymax)
    rejilla(ax, ax.get_xlim(), ax.get_ylim())
    for Li, yi in zip(bases_lagrange(xs), ys):
        ax.plot(xx, yi * Li(xx) * 0.55, lw=1.8, alpha=0.30, color=HIELO)
    ax.fill_between(xx, 0, lagrange_evaluar_directo(xs, ys, xx), color=TEAL, alpha=0.10)
    ax.plot(xx, lagrange_evaluar_directo(xs, ys, xx), color=TEAL, lw=4, alpha=0.85)
    for x, y in zip(xs, ys):
        ax.plot([x, x], [0, y], color=AMBAR, lw=1.2, alpha=0.4, ls="--")
        ax.scatter(x, y, s=300, color=AMBAR, edgecolors=BG_TOP, lw=3, zorder=5)
    guardar(fig, "interpolacion")


# ---------------------------------------------------------------- spline
def fondo_spline():
    """Spline cúbico natural: tramos coloreados alternados, nodos y derivada en segundo plano."""
    fig, ax = lienzo()
    xs, ys = arrays_nodos()
    xs, ys = np.array(xs), np.array(ys)
    res = spline_cubico_natural(xs, ys)
    f, df = res["eval_func"], res["deriv_func"]
    ax.set_xlim(xs.min() - 0.08, xs.max() + 0.08)
    ax.set_ylim(-ys.max() * 0.2, ys.max() * 1.12)
    rejilla(ax, ax.get_xlim(), ax.get_ylim())
    xx = np.linspace(xs.min(), xs.max(), 600)
    d = df(xx)
    ax.plot(xx, d / d.max() * ys.max() * 0.45, color=CORAL, lw=2, alpha=0.30)
    for i in range(len(xs) - 1):
        t = np.linspace(xs[i], xs[i + 1], 150)
        ax.axvspan(xs[i], xs[i + 1], color=TEAL if i % 2 == 0 else AMBAR, alpha=0.05)
        ax.plot(t, f(t), color=TEAL if i % 2 == 0 else AMBAR, lw=5, alpha=0.85, solid_capstyle="round")
    ax.scatter(xs, ys, s=320, color=HIELO, edgecolors=BG_TOP, lw=3, zorder=5)
    guardar(fig, "spline")


# ---------------------------------------------------------------- sistemas lineales
def fondo_sistemas_lineales():
    """Matriz A de equilibrio de la armadura (mapa de calor) con la armadura dibujada encima."""
    fig, ax = lienzo()
    sis = armadura_warren_canal(20.0, 4.0, 100.0)
    A = np.array(sis["A"], dtype=float)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.75)
    S = np.ma.masked_where(A == 0, np.sign(A))
    ax.imshow(S, cmap="coolwarm", vmin=-1.6, vmax=1.6, alpha=0.40, extent=[5.2, 11.4, 0.4, 6.2],
              aspect="auto", interpolation="nearest")
    for i in range(A.shape[0] + 1):
        y = 0.4 + i * 5.8 / A.shape[0]
        ax.plot([5.2, 11.4], [y, y], color=HIELO, lw=0.8, alpha=0.10)
    for j in range(A.shape[1] + 1):
        x = 5.2 + j * 6.2 / A.shape[1]
        ax.plot([x, x], [0.4, 6.2], color=HIELO, lw=0.8, alpha=0.10)
    sol = resolver_armadura(sis)
    P = sis["nodos"]
    mx = max(abs(f) for f in sol["fuerzas_kN"].values())
    k, ox, oy = 0.22, 0.6, 1.6
    for nombre, a, b in sis["barras"]:
        f = sol["fuerzas_kN"][nombre]
        col = AMBAR if f > 1e-9 else CORAL if f < -1e-9 else HIELO
        (x1, y1), (x2, y2) = P[a], P[b]
        ax.plot([ox + x1 * k, ox + x2 * k], [oy + y1 * k * 1.9, oy + y2 * k * 1.9],
                color=col, lw=2 + 7 * abs(f) / mx, alpha=0.7, solid_capstyle="round")
    for (x, y) in P.values():
        ax.scatter(ox + x * k, oy + y * k * 1.9, s=200, color=HIELO, zorder=5)
    guardar(fig, "sistemas_lineales")


# ---------------------------------------------------------------- no lineales
def fondo_no_lineales():
    """Plano (y, V): curvas F1=0 (Fr=1) y F2=0 (continuidad) y trayectorias de Newton vs punto fijo."""
    fig, ax = lienzo()
    Q, b, g = 20.0, 10.0, 9.81
    yc = hid.profundidad_critica_analitica(Q, b)
    F, J, G = hid.sistema_critico(Q, b, g, yc)
    x0 = hid.aproximacion_inicial(Q, b, yc * 1.5)
    ys_ = np.linspace(0.3, 1.5, 400)
    ax.set_xlim(0.3, 1.5)
    ax.set_ylim(1.0, 5.2)
    rejilla(ax, ax.get_xlim(), ax.get_ylim())
    ax.plot(ys_, np.sqrt(g * ys_), color=TEAL, lw=3.5, alpha=0.8)   # V = sqrt(g y)
    ax.plot(ys_, Q / (b * ys_), color=CORAL, lw=3.5, alpha=0.8)     # V = Q/(b y)
    # campo de |F| como niebla de contornos
    Y, V = np.meshgrid(np.linspace(0.3, 1.5, 200), np.linspace(1.0, 5.2, 200))
    R = np.hypot((V ** 2 - g * Y) / (g * yc), (b * Y * V - Q) / Q)
    ax.contourf(Y, V, np.log10(R + 1e-6), levels=14, cmap="Blues_r", alpha=0.07)
    nw = newton_raphson_sistemas(F, x0, J=J)
    pf = punto_fijo_sistemas(G, x0, F=F, max_iter=60)
    tn = np.array([h["x_k"] for h in nw["historial"]] + [nw["x_sol"]])
    tp = np.array([h["x_k"] for h in pf["historial"]] + [pf["x_sol"]])
    segs = np.stack([tp[:-1], tp[1:]], axis=1)
    ax.add_collection(LineCollection(segs, colors=HIELO, linewidths=2, alpha=0.5))
    ax.scatter(tp[:, 0], tp[:, 1], s=60, color=HIELO, alpha=0.6)
    ax.plot(tn[:, 0], tn[:, 1], "-o", color=AMBAR, lw=3.5, ms=14, alpha=0.9)
    ax.scatter(*nw["x_sol"], s=700, facecolors="none", edgecolors=AMBAR, lw=3)
    guardar(fig, "no_lineales")


# ---------------------------------------------------------------- caso integrador
def fondo_caso_integrador():
    """Cadena del caso: curva de descarga -> canal con tirante crítico -> armadura Warren, en tres bandas."""
    fig, ax = lienzo()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.75)
    rejilla(ax, (0, 12), (0, 6.75))
    # 1) curva de descarga (spline) - banda izquierda
    xs, ys = arrays_nodos()
    s = spline_cubico_natural(xs, ys)["eval_func"]
    xx = np.linspace(min(xs), max(xs), 300)
    yy = s(xx)
    u = 0.5 + (xx - xx.min()) / np.ptp(xx) * 3.2
    v = 1.4 + (yy - yy.min()) / np.ptp(yy) * 4.0
    ax.fill_between(u, 1.4, v, color=TEAL, alpha=0.14)
    ax.plot(u, v, color=TEAL, lw=4, alpha=0.85)
    ax.scatter(0.5 + (np.array(xs) - min(xs)) / np.ptp(xs) * 3.2,
               1.4 + (np.array(arrays_nodos()[1]) - yy.min()) / np.ptp(yy) * 4.0, s=200, color=AMBAR, zorder=5)
    # 2) canal rectangular con tirante - banda central
    ax.plot([4.9, 4.9, 7.1, 7.1], [4.9, 1.6, 1.6, 4.9], color=HIELO, lw=5, alpha=0.6, solid_joinstyle="round")
    yc = 1.7
    ax.fill_between([4.9, 7.1], 1.6, 1.6 + yc, color=TEAL, alpha=0.30)
    ax.plot([4.9, 7.1], [1.6 + yc] * 2, color=TEAL, lw=3, alpha=0.9)
    for k in range(3):
        ax.annotate("", xy=(6.6, 2.0 + k * 0.45), xytext=(5.4, 2.0 + k * 0.45),
                    arrowprops=dict(arrowstyle="-|>", color=HIELO, lw=2, alpha=0.5))
    # 3) armadura Warren - banda derecha
    sis = armadura_warren_canal(8.0, 1.6, 100.0)
    sol = resolver_armadura(sis)
    P = sis["nodos"]
    mx = max(abs(f) for f in sol["fuerzas_kN"].values())
    k, ox, oy = 0.36, 8.2, 3.2
    for nombre, a, b in sis["barras"]:
        f = sol["fuerzas_kN"][nombre]
        col = AMBAR if f > 1e-9 else CORAL if f < -1e-9 else HIELO
        (x1, y1), (x2, y2) = P[a], P[b]
        ax.plot([ox + x1 * k, ox + x2 * k], [oy + y1 * k * 1.4, oy + y2 * k * 1.4],
                color=col, lw=2 + 6 * abs(f) / mx, alpha=0.75, solid_capstyle="round")
    for (x, y) in P.values():
        ax.scatter(ox + x * k, oy + y * k * 1.4, s=170, color=HIELO, zorder=5)
    # flechas de la cadena
    for x0, x1 in [(3.9, 4.7), (7.3, 8.0)]:
        ax.annotate("", xy=(x1, 2.9), xytext=(x0, 2.9),
                    arrowprops=dict(arrowstyle="-|>", color=AMBAR, lw=4, alpha=0.8, mutation_scale=30))
    guardar(fig, "caso_integrador")


if __name__ == "__main__":
    for f in (fondo_inicio, fondo_interpolacion, fondo_spline,
              fondo_sistemas_lineales, fondo_no_lineales, fondo_caso_integrador):
        f()
