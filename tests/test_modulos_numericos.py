"""Pruebas de los módulos numéricos contra los valores del manuscrito (notebooks) y contra SciPy."""
import numpy as np
import pytest

from modulos.diferencias_divididas import agregar_nodo_newton, interpolacion_newton
from modulos.lagrange import lagrange_interpolacion
from modulos.newton_sistemas import comparar_con_libreria_no_lineal, newton_raphson_sistemas
from modulos.punto_fijo import punto_fijo_sistemas
from modulos.sistemas_lineales import comparar_con_libreria_lineal, gauss_pivoteo_parcial
from modulos.spline import spline_cubico_natural, verificar_monotonia
from modulos.metricas import metricas_error


# ------------------------------------------------------------------ sistemas lineales
def test_lineal_caso1_pivote_nulo_manuscrito():
    r = gauss_pivoteo_parcial([[0, 2, 3], [4, 6, 7], [2, 1, 6]], [8, -3, 5])
    assert r["exito"]
    np.testing.assert_allclose(r["x"], [-239 / 44, 1 / 22, 29 / 11], rtol=1e-12)
    p1 = r["historial_pasos"][0]
    assert p1["hubo_intercambio"] and p1["filas_intercambiadas"] == (1, 2) and p1["valor_pivote"] == 4
    # F3 <- F3 - (1/2) F1 (manuscrito)
    m31 = [m for m in p1["multiplicadores"] if m["fila_afectada"] == 3][0]["factor_m"]
    assert m31 == pytest.approx(0.5)
    # matriz triangular del manuscrito: diag [4, 2, 11/2], c = [-3, 8, 29/2]
    U = r["matriz_triangular"]
    np.testing.assert_allclose(np.diag(U[:, :3]), [4, 2, 5.5])
    np.testing.assert_allclose(U[:, 3], [-3, 8, 14.5])
    assert r["norma_residuo_inf"] < 1e-14


def test_lineal_caso2_y_caso3():
    r2 = gauss_pivoteo_parcial([[3, -2], [-1, 4]], [5, 15])
    np.testing.assert_allclose(r2["x"], [5, 5])
    r3 = gauss_pivoteo_parcial([[1, 1, 0, 0], [-1, 2, 1, 0], [0, -1, 2, 1], [0, 0, -1, 2]], [3, 6, 8, 5])
    np.testing.assert_allclose(r3["x"], [1, 2, 3, 4], atol=1e-12)
    for r in (r2, r3):
        assert 1 < r["condicion_A"] < 10  # "kappa entre 2 y 9" (notebook)
        comp = comparar_con_libreria_lineal([[3, -2], [-1, 4]], [5, 15], r2["x"])
        assert comp["max_diferencia_absoluta"] < 1e-12


def test_lineal_entradas_invalidas_y_singular():
    assert not gauss_pivoteo_parcial([[1, 2, 3], [4, 5, 6]], [1, 2])["exito"]            # no cuadrada
    assert not gauss_pivoteo_parcial([[1, 2], [3, 4]], [1, 2, 3])["exito"]               # dimensión b
    assert not gauss_pivoteo_parcial([[1, np.nan], [3, 4]], [1, 2])["exito"]             # NaN
    r = gauss_pivoteo_parcial([[1, 2], [2, 4]], [1, 2])                                   # singular
    assert not r["exito"] and "singular" in r["mensaje"].lower()


# ------------------------------------------------------------------ no lineales
F1 = lambda x, y: np.array([x**2 + x * y - 10.0, y + 3.0 * x * y**2 - 57.0])
J1 = lambda x, y: np.array([[2 * x + y, x], [3 * y**2, 1 + 6 * x * y]])


def G1(x, y):
    """G1 EXACTA del notebook 2 (incluye su parche 1e-12 para x = 0)."""
    rad_x = max(10.0 - x * y, 0.0)
    den_y = 3.0 * x if abs(x) > 1e-12 else 1e-12
    rad_y = max((57.0 - y) / den_y, 0.0)
    return np.array([np.sqrt(rad_x), np.sqrt(rad_y)])

F2 = lambda x, y: np.array([(x - 4) ** 2 + (y - 4) ** 2 - 5, x**2 + y**2 - 16])
J2 = lambda x, y: np.array([[2 * (x - 4), 2 * (y - 4)], [2 * x, 2 * y]])


def test_punto_fijo_simultaneo_manuscrito():
    r = punto_fijo_sistemas(G1, [1.5, 3.5], max_iter=100, F=F1)
    h = r["historial"]
    np.testing.assert_allclose(h[0]["x_nuevo"], [2.179449, 3.448027], atol=1e-6)
    np.testing.assert_allclose(h[1]["x_nuevo"], [1.576452, 2.861895], atol=1e-6)
    np.testing.assert_allclose(h[2]["x_nuevo"], [2.342725, 3.383378], atol=1e-6)
    # HALLAZGO DE AUDITORÍA: G1 no es contractiva. Tras las 3 primeras iteraciones (que coinciden con el
    # manuscrito) la iteración oscila, en la iteración 8 llega a x = 0 y el parche 1e-12 dispara y ~ 7e6.
    assert not r["convergio"] and "máximo de iteraciones" in r["motivo_parada"]
    assert h[7]["x_nuevo"][0] == 0.0 and h[8]["x_nuevo"][1] > 1e6


def test_punto_fijo_usa_vector_anterior():
    # G(x, y) = (y, x): con actualización simultánea el vector (1,2) pasa a (2,1) y vuelve a (1,2).
    r = punto_fijo_sistemas(lambda x, y: np.array([y, x]), [1.0, 2.0], max_iter=2)
    assert r["historial"][0]["x_nuevo"] == [2.0, 1.0]
    assert r["historial"][1]["x_nuevo"] == [1.0, 2.0]


def test_newton_problema5_manuscrito():
    r = newton_raphson_sistemas(F1, [1.5, 3.5], J=J1)
    h = r["historial"]
    np.testing.assert_allclose(h[0]["delta_x"], [0.536029, -0.656125], atol=1e-6)
    np.testing.assert_allclose(h[0]["x_nuevo"], [2.036029, 2.843875], atol=1e-6)
    np.testing.assert_allclose(h[1]["delta_x"], [-0.037328, 0.158413], atol=1e-6)
    np.testing.assert_allclose(h[2]["delta_x"], [0.001299, -0.002289], atol=1e-6)
    assert r["convergio"]
    np.testing.assert_allclose(r["x_sol"], [2.0, 3.0], atol=1e-4)
    comp = comparar_con_libreria_no_lineal(F1, [1.5, 3.5], r["x_sol"])
    assert comp["max_diferencia_absoluta"] < 1e-3


def test_newton_problema6_circunferencias_manuscrito():
    r1 = newton_raphson_sistemas(F2, [2.0, 3.5], J=J2)
    np.testing.assert_allclose(r1["historial"][0]["delta_x"], [-0.208333, 0.083333], atol=1e-6)
    np.testing.assert_allclose(r1["historial"][2]["x_nuevo"], [1.805829, 3.569171], atol=2e-6)
    r2 = newton_raphson_sistemas(F2, [3.5, 2.0], J=J2)
    np.testing.assert_allclose(r2["historial"][2]["x_nuevo"], [3.569171, 1.805829], atol=2e-6)


def test_newton_jacobiano_singular_y_dominio():
    r = newton_raphson_sistemas(lambda x, y: np.array([x * y, x * y]), [1.0, 1.0])
    assert r["exito"] and not r["convergio"] and "singular" in r["motivo_parada"].lower()
    r = newton_raphson_sistemas(lambda x: np.array([x**2 - 4]), [1.0], dominio=lambda v: v[0] > 0)
    assert r["convergio"]
    assert not newton_raphson_sistemas(F1, ["a", 1])["exito"]


# ------------------------------------------------------------------ interpolación
def test_lagrange_manuscrito():
    r7 = lagrange_interpolacion([0, 20], [3.85, 0.8], 15)
    assert r7["valor_evaluado"] == pytest.approx(1.5625)
    r8 = lagrange_interpolacion([1, 3, 4], [2, 6, 24], 2)
    assert r8["valor_evaluado"] == pytest.approx(-4 / 3)
    np.testing.assert_allclose(r8["P_expandido"].coeffs, [16 / 3, -58 / 3, 16], rtol=1e-12)
    r9 = lagrange_interpolacion([1, 4, 5, 6], [0, 1.386294, 1.609438, 1.791759], 2)
    assert r9["valor_evaluado"] == pytest.approx(0.6287674, abs=1e-6)
    for r in (r7, r8, r9):
        assert r["reproduccion_nodos"]["reproduce"] and r["comparacion_libreria"]["coincidencia"]


def test_nodos_repetidos_y_extrapolacion():
    assert not lagrange_interpolacion([1, 1, 2], [1, 2, 3])["exito"]
    assert not interpolacion_newton([1, 2, 2], [1, 2, 3])["exito"]
    assert not spline_cubico_natural([1, 2, 2], [1, 2, 3])["exito"]
    r = lagrange_interpolacion([1, 2, 3], [1, 4, 9], 10)
    assert r["extrapolando"] and r["advertencia_extrapolacion"]


def test_newton_manuscrito_y_equivalencia_con_lagrange():
    r10 = interpolacion_newton([1, 2, 3], [1, 4, 9])
    np.testing.assert_allclose(r10["coeficientes_newton"], [1, 3, 1])
    np.testing.assert_allclose(r10["P_expandido"].coeffs, [1, 0, 0], atol=1e-12)
    xs = [1.0, 1.3, 1.6, 1.9]
    ys = [0.7651977, 0.6200860, 0.4554022, 0.2818186]
    r11 = interpolacion_newton(xs, ys, 1.5)
    np.testing.assert_allclose(r11["coeficientes_newton"], [0.7651977, -0.4837057, -0.1087339, 0.0658784], atol=1e-7)
    assert r11["valor_evaluado"] == pytest.approx(0.5118127, abs=1e-7)
    # mismo polinomio que Lagrange con los mismos nodos
    lag = lagrange_interpolacion(xs, ys, 1.5)
    assert r11["valor_evaluado"] == pytest.approx(lag["valor_evaluado"], abs=1e-12)
    # propiedad acumulativa (ejercicio 12)
    ext = agregar_nodo_newton(xs, ys, 2.2, 0.1103623, 1.5)
    assert ext["coeficientes_previos_conservados"]
    assert ext["coeficiente_nuevo"] == pytest.approx(0.0018251, abs=1e-7)
    assert ext["correccion_en_x_eval"] == pytest.approx(7.3004e-6, abs=1e-9)
    assert ext["despues"]["valor_evaluado"] == pytest.approx(0.5118200, abs=1e-7)


def test_spline_natural_vs_scipy_y_nodos():
    xs = [1.0, 1.3, 1.6, 1.9, 2.2]
    ys = [0.7651977, 0.6200860, 0.4554022, 0.2818186, 0.1103623]
    s = spline_cubico_natural(xs, ys)
    assert s["comparacion_libreria"]["max_diferencia_absoluta"] < 1e-10
    np.testing.assert_allclose(s["eval_func"](np.array(xs)), ys, atol=1e-12)
    assert s["segundas_derivadas"][0] == 0 and s["segundas_derivadas"][-1] == 0
    assert verificar_monotonia(s["eval_func"], 1.0, 2.2)["creciente"] is False  # datos decrecientes


def test_metricas_error_y_nota_con_un_punto():
    m = metricas_error([10.0], [11.0])
    assert m["MAE"] == m["RMSE"] == m["error_max"] == 1.0 and m["nota"]
    m = metricas_error([1, 2, 3], [1, 2, 5])
    assert m["MAE"] == pytest.approx(2 / 3) and m["error_max"] == 2 and m["nota"] is None
