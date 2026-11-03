"""Datos hidrológicos del caso: estación USGS 09380000 (Colorado River at Lees Ferry, AZ).

ESTADO DE VERIFICACIÓN (ver docs/auditoria_datos_y_modelos.md):
  * La estación y su nombre FUERON verificados en el sitio oficial de USGS (2026-11-01).
  * La lectura 8.07 ft / 7870 cfs (2026-11-01 17:00 MST, PROVISIONAL) SÍ fue leída en la página oficial
    y se usa como observación de validación.
  * La observación 7.11 ft / 5030 cfs atribuida por Gemini al 2026-11-01 NO pudo comprobarse: queda
    PENDIENTE y se excluye de la construcción y de las métricas.
"""
from __future__ import annotations

FT_A_M = 0.3048                  # exacto por definición
CFS_A_M3S = 0.028316846592       # = 0.3048**3, exacto

ESTACION = {
    "id": "USGS 09380000",
    "nombre": "Colorado River at Lees Ferry, AZ",
    "entidad": "United States Geological Survey (USGS) - USGS Water Data for the Nation",
    "url": "https://waterdata.usgs.gov/usa/nwis/uv?site_no=09380000",
    "url_hoja_tecnica": "https://pubs.usgs.gov/publication/fs20263002/full",
    "fecha_consulta": "2026-11-01",
    "advertencias": [
        "El caudal en este punto está REGULADO por la presa de Glen Canyon (menos de 16 millas aguas arriba): "
        "no representa un régimen natural.",
        "El caudal se calcula a partir del nivel con una curva de descarga (rating) que USGS actualiza con "
        "mediciones de campo; puede cambiar por sedimentación, erosión y vegetación.",
        "Los datos recientes son PROVISIONALES y están sujetos a revisión.",
    ],
}


def ft_a_m(ft: float) -> float:
    return ft * FT_A_M


def cfs_a_m3s(cfs: float) -> float:
    return cfs * CFS_A_M3S


# Nodos preliminares (propuesta de Gemini). rol: "nodo" se usa para construir; el resto, no.
_REGISTROS = [
    {"id": "N0", "nivel_ft": 6.00, "caudal_cfs": 3000, "rol": "nodo"},
    {"id": "N1", "nivel_ft": 7.00, "caudal_cfs": 4800, "rol": "nodo"},
    {"id": "N2", "nivel_ft": 8.00, "caudal_cfs": 7700, "rol": "nodo"},
    {"id": "N3", "nivel_ft": 9.00, "caudal_cfs": 11000, "rol": "nodo"},
    {"id": "N4", "nivel_ft": 10.00, "caudal_cfs": 15000, "rol": "nodo"},
]
PROCEDENCIA_NODOS = ""

OBS_VALIDACION_VERIFICADA = {
    "id": "V1", "nivel_ft": 8.07, "caudal_cfs": 7870, "rol": "validacion",
    "fecha": "2026-11-01 17:00 MST", "calificador": "Provisional",
    "tipo": "Lectura instantánea; el caudal es calculado por USGS desde el nivel con su rating vigente "
            "(no es una medición independiente de caudal).",
    "fuente": ESTACION["url"], "fecha_consulta": "2026-11-01",
}

OBS_PENDIENTE = {
    "id": "V0", "nivel_ft": 7.11, "caudal_cfs": 5030, "rol": "pendiente",
    "fecha": "1 nov 2026 (según Gemini; sin hora)",
    "estado": "NO VERIFICADO: no se pudo comprobar en USGS que exista; la lectura más reciente verificada "
              "el 2026-11-01 17:00 MST fue 8.07 ft / 7870 cfs. Se excluye de construcción y de métricas.",
}


def _con_si(r: dict) -> dict:
    out = dict(r)
    out["h_m"] = ft_a_m(r["nivel_ft"])
    out["Q_m3s"] = cfs_a_m3s(r["caudal_cfs"])
    return out


def nodos_construccion() -> list[dict]:
    return [_con_si(r) for r in _REGISTROS if r["rol"] == "nodo"]


def observacion_validacion() -> dict:
    return _con_si(OBS_VALIDACION_VERIFICADA)


def observacion_pendiente() -> dict:
    return _con_si(OBS_PENDIENTE)


def arrays_nodos() -> tuple[list[float], list[float]]:
    n = nodos_construccion()
    return [r["h_m"] for r in n], [r["Q_m3s"] for r in n]


def rango_nodos() -> tuple[float, float]:
    h, _ = arrays_nodos()
    return min(h), max(h)
