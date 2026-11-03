# Workshop 2 - Algoritmos Numericos (Ingenieria Civil)

Plataforma web (Streamlit) que integra metodos numericos en un caso de ingenieria civil:
hidrologia -> hidraulica -> estructura. Modelo academico conceptual.

## Paginas

| Pagina | Contenido | Imagen de fondo |
|---|---|---|
| Inicio (`app.py`) | Presentacion del caso | `docs/img/fondo_inicio.png` |
| 1 Interpolacion | Lagrange y Newton | `docs/img/fondo_interpolacion.png` |
| 2 Spline | Spline cubico natural | `docs/img/fondo_spline.png` |
| 3 Sistemas lineales | Gauss con pivoteo, armadura Warren | `docs/img/fondo_sistemas_lineales.png` |
| 4 Sistemas no lineales | Punto fijo y Newton-Raphson | `docs/img/fondo_no_lineales.png` |
| 5 Caso integrador | Rio -> canal -> armadura | `docs/img/fondo_caso_integrador.png` |

Cada pagina llama a `ui.iniciar(titulo, fondo)`, que aplica su imagen como fondo.
Las imagenes se generan con los modulos reales del repositorio:

```bash
python tools/generar_fondos.py
```

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
pytest
```

## Estructura

- `modulos/`: metodos numericos y caso integrador (`modulos/caso/`).
- `pages/`: paginas de Streamlit.
- `ui.py`: configuracion de pagina, fondo y estilo de figuras.
- `tools/generar_fondos.py`: generador de las imagenes de fondo.
- `tests/`: pruebas con pytest.

## Advertencia sobre los datos

Los nodos nivel-caudal (estacion USGS 09380000, Lees Ferry, AZ) son preliminares y no estan
verificados contra la curva de descarga oficial.
