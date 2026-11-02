"""Pruebas del caso integrador: datos, hidráulica, estructura y auditoría de la matriz de Gemini."""
import math

import numpy as np
import pytest

from modulos.caso import datos_rio as dr
from modulos.caso import hidraulica as hy
from modulos.caso import estructura as es
from modulos.newton_sistemas import newton_raphson_sistemas
from modulos.punto_fijo import punto_fijo_sistemas
from modulos.lagrange import lagrange_interpolacion
from modulos.diferencias_divididas import interpolacion_newton
from modulos.spline import spline_cubico_natural


# ------------------------------------------------------------------ datos
def test_conversiones_exactas_y_tabla_gemini():
    assert dr.CFS_A_M3S == pytest.approx(0.3048 ** 3, rel=1e-15)
    h, q = dr.arrays_nodos()
    np.testing.assert_allclose(h, [1.829, 2.134, 2.438, 2.743, 3.048], atol=6e-4)       # redondeo de Gemini
    np.testing.assert_allclose(q, [84.95, 135.92, 218.04, 311.48, 424.75], atol=6e-3)
    assert len(h) == 5 and h == sorted(h)


def test_validacion_separada_de_los_nodos_y_pendiente_excluida():
    h, _ = dr.arrays_nodos()
    v = dr.observacion_validacion()
    p = dr.observacion_pendiente()
    assert v["h_m"] not in h and p["h_m"] not in h          # no contamina la construcción
    assert min(h) < v["h_m"] < max(h)                        # dentro del intervalo (sin extrapolar)
    assert "NO VERIFICADO" in p["estado"]
    assert v["nivel_ft"] == 8.07 and v["caudal_cfs"] == 7870 and v["calificador"] == "Provisional"


def test_tres_metodos_comparten_datos_y_lagrange_igual_newton():
    h, q = dr.arrays_nodos()
    v = dr.observacion_validacion()
    lag = lagrange_interpolacion(h, q, v["h_m"])
    new = interpolacion_newton(h, q, v["h_m"])
    spl = spline_cubico_natural(h, q)
    assert lag["valor_evaluado"] == pytest.approx(new["valor_evaluado"], rel=1e-12)
    # estimación razonable frente a la lectura USGS (diferencia < 2 %) y spline cercano
    assert abs(lag["valor_evaluado"] - v["Q_m3s"]) / v["Q_m3s"] < 0.02
    assert abs(spl["eval_func"](v["h_m"]) - v["Q_m3s"]) / v["Q_m3s"] < 0.02


# ------------------------------------------------------------------ hidráulica
@pytest.mark.parametrize("Q,b", [(33.6, 4.0), (10.0, 2.5), (0.5, 1.0)])
def test_profundidad_critica_sistema_y_escalar_coinciden_con_analitica(Q, b):
    g = 9.81
    y_an = hy.profundidad_critica_analitica(Q, b, g)
    # escalar con el Newton de sistemas (caso 1x1)
    F, J = hy.sistema_escalar(Q, b, g)
    r = newton_raphson_sistemas(F, [y_an * 1.5], J=J, tol_cambio=1e-10, tol_residual=1e-9 * Q * Q, dominio=hy.dominio_positivo)
    assert r["convergio"] and r["x_sol"][0] == pytest.approx(y_an, rel=1e-8)
    # sistema 2x2 (y, V)
    y0 = 1.0
    Fs, Js, Gs = hy.sistema_critico(Q, b, g, y0)
    x0 = hy.aproximacion_inicial(Q, b, y0)
    rn = newton_raphson_sistemas(Fs, x0, J=Js, tol_cambio=1e-10, tol_residual=1e-10, dominio=hy.dominio_positivo)
    assert rn["convergio"] and rn["x_sol"][0] == pytest.approx(y_an, rel=1e-8)
    rp = punto_fijo_sistemas(Gs, x0, tol_cambio=1e-10, tol_residual=1e-10, max_iter=500, F=Fs)
    assert rp["convergio"] and rp["x_sol"][0] == pytest.approx(y_an, rel=1e-7)   # |lambda| = 1/sqrt(2) < 1
    comp = hy.comprobaciones_hidraulicas(rn["x_sol"][0], Q, b, g)
    assert comp["froude"] == pytest.approx(1.0, rel=1e-7)
    assert comp["energia_especifica_m"] == pytest.approx(comp["energia_minima_teorica_m"], rel=1e-7)


def test_hidraulica_validaciones():
    with pytest.raises(ValueError):
        hy.profundidad_critica_analitica(-1, 4)
    with pytest.raises(ValueError):
        hy.profundidad_critica_analitica(10, 0)
    with pytest.raises(ValueError):
        hy.caudal_derivado(100, 1.5)
    with pytest.raises(ValueError):
        hy.caudal_derivado(float("nan"), 0.15)
    assert hy.caudal_derivado(100, 0.15) == pytest.approx(15)


def test_unidades_carga():
    w = hy.peso_agua_por_metro_kNm(1.0, 4.0, 1000.0, 9.81)
    assert w["w_kN_por_m"] == pytest.approx(39.24)               # 1000*9.81*4*1 N/m = 39240 N/m
    assert hy.carga_en_tramo_kN(w["w_kN_por_m"], 5.0) == pytest.approx(196.2)


# ------------------------------------------------------------------ estructura
def test_armadura_warren_vs_analitica_y_equilibrio():
    L, H, W = 5.0, 1.5, 200.0
    sis = es.armadura_warren_canal(L, H, W)
    assert sis["rango"] == 10 and sis["A"].shape == (10, 10)      # determinada y estable
    r = es.resolver_armadura(sis)
    assert r["exito"]
    ref = es.solucion_analitica_warren(L, H, W)
    for k in ("AB", "BC", "DE", "AD", "EC", "DB", "BE"):
        assert r["fuerzas_kN"][k] == pytest.approx(ref[k], abs=1e-9)
    assert r["reacciones_kN"]["Ry_A"] == pytest.approx(W / 2) and r["reacciones_kN"]["Ry_C"] == pytest.approx(W / 2)
    assert abs(r["reacciones_kN"]["Rx_A"]) < 1e-9
    assert r["equilibrio_global"]["cumple"]
    assert r["gauss"]["norma_residuo_inf"] < 1e-9                  # r = A x - b
    assert r["estado_barras"]["AB"] == "tracción" and r["estado_barras"]["DE"] == "compresión"
    assert r["estado_barras"]["DB"] == "fuerza nula"


def test_armadura_inestable_o_indeterminada_se_rechaza():
    with pytest.raises(ValueError):                                 # una barra de más
        es.construir_sistema_armadura({"A": (0, 0), "B": (1, 0), "C": (0.5, 1)},
                                      [("AB", "A", "B"), ("AC", "A", "C"), ("BC", "B", "C"), ("AB2", "A", "B")],
                                      [("A", "x"), ("A", "y"), ("B", "y")], {"C": (0, -1)})
    # mecanismo: 3 barras en línea recta + apoyos -> matriz singular, resolver_armadura debe fallar con mensaje claro
    sis = es.construir_sistema_armadura({"A": (0, 0), "B": (1, 0), "C": (2, 0)},
                                        [("AB", "A", "B"), ("BC", "B", "C")],
                                        [("A", "x"), ("A", "y"), ("C", "y"), ("C", "x")], {"B": (0, -1)})
    r = es.resolver_armadura(sis)
    assert not r["exito"] and "singular" in r["mensaje"].lower()
    with pytest.raises(ValueError):
        es.armadura_warren_canal(-1, 1, 10)


def test_auditoria_matriz_gemini_es_incorrecta():
    a = es.auditar_matriz_gemini(math.radians(30), 100.0)
    assert a["gemini"]["T_AB"] == pytest.approx(0.0)                                  # Gemini: T_AB = 0
    assert a["referencia_analitica"]["AB"] == pytest.approx(100 / (2 * math.tan(math.radians(30))))
    for k in a["referencia_analitica"]:
        assert a["referencia_numerica"][k] == pytest.approx(a["referencia_analitica"][k], rel=1e-10)
    assert a["gemini"]["T_AC"] * a["gemini"]["T_BC"] < 0                                 # signos opuestos: no simétrico
