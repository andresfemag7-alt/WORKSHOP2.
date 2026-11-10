Workshop 2 | Métodos Numéricos Aplicados a la Ingeniería Civil

Laboratorio N.º 2 — Algoritmos Numéricos

Estudiantes: Sebastian Molina Giraldo y Andrés Felipe Madroñero
Docente: Mg. Mario Hernán López Arbelaez
Programa: Ingeniería Civil

Aplicación web

El proyecto cuenta con una aplicación interactiva desarrollada en Python mediante Streamlit, que permite ejecutar métodos numéricos, visualizar sus procedimientos y analizar los resultados dentro de un mismo contexto de ingeniería civil.

Acceder a la aplicación web

Descripción del proyecto

Este repositorio corresponde al desarrollo del Laboratorio N.º 2 de Algoritmos Numéricos, cuyo propósito es aplicar cuatro temas estudiados en la asignatura a un problema integrador de ingeniería civil.

El proyecto plantea un sistema conceptual de captación y derivación hídrica, en el que el agua de un río es conducida mediante un canal rectangular de concreto. En uno de sus tramos, el canal debe atravesar una depresión del terreno, por lo que se considera una estructura metálica tipo Warren para proporcionar soporte.

A partir de este escenario, se relacionan diferentes procedimientos matemáticos para estimar el caudal del río, analizar las condiciones hidráulicas del canal y determinar las fuerzas internas de la estructura de apoyo.

Objetivo

Desarrollar una plataforma interactiva que permita implementar, analizar y comparar métodos numéricos mediante su aplicación a un modelo conceptual de ingeniería civil, integrando cálculos hidráulicos y estructurales.

Contexto de ingeniería civil

El modelo utiliza como referencia el río Colorado, específicamente la estación hidrométrica USGS 09380000, ubicada en Lees Ferry, Estados Unidos.

Se plantea una captación que deriva una fracción del caudal hacia un canal de concreto. Posteriormente, se analiza la profundidad crítica del flujo y se utiliza como referencia para estimar la carga de agua transmitida a una armadura metálica de soporte.

De esta manera, los cuatro temas numéricos se relacionan mediante variables compartidas y una secuencia de cálculo.

Métodos numéricos implementados

1. Sistemas de ecuaciones lineales

Aplicación: análisis del equilibrio estático de una armadura metálica tipo Warren.

Se implementa la eliminación de Gauss con pivoteo parcial para resolver el sistema de ecuaciones generado a partir del equilibrio de fuerzas en los nudos.

El procedimiento permite determinar:

Fuerzas axiales en los elementos de la armadura.

Elementos sometidos a tracción o compresión.

Reacciones en los apoyos.

Verificación del equilibrio mediante residuos numéricos.

2. Sistemas de ecuaciones no lineales

Aplicación: cálculo de la profundidad crítica en un canal rectangular.

Se emplean los métodos de punto fijo y Newton-Raphson para resolver las ecuaciones que relacionan el caudal, la velocidad y la profundidad del agua.

La aplicación permite analizar el comportamiento iterativo, las condiciones de convergencia y los resultados obtenidos con cada procedimiento.

3. Interpolación de Lagrange

Aplicación: estimación del caudal del río a partir de datos de nivel y caudal.

Se construye un polinomio de interpolación mediante Lagrange, utilizando pares de datos correspondientes a la relación nivel–caudal.

El objetivo es estimar el caudal para un nivel determinado dentro del intervalo de datos disponible y evaluar la aproximación obtenida.

4. Interpolación de Newton y comparación con splines

Aplicación: análisis comparativo de la interpolación de datos hidrométricos.

Se utiliza el método de Newton mediante diferencias divididas y se compara con la interpolación de Lagrange y el spline cúbico natural.

El módulo permite estudiar las diferencias entre las aproximaciones, visualizar las curvas y evaluar los errores respecto a los datos de validación.

Integración de los métodos

Aunque la plataforma organiza los métodos en cuatro pestañas, su secuencia de aplicación dentro del modelo es:

Interpolación de Lagrange → Newton y spline → Sistemas no lineales → Sistemas lineales

Se estima el caudal del río a partir del nivel mediante interpolación.

Se comparan los procedimientos de interpolación sobre los mismos datos.

Se determina el caudal derivado y se calcula la profundidad crítica del canal.

Se estima el peso del agua y se determinan las fuerzas y reacciones de la armadura de soporte.

La plataforma también permite utilizar los módulos de manera independiente e incorpora mecanismos para compartir resultados y advertir cuando existen cálculos desactualizados.

Tecnologías utilizadas

Tecnología

Aplicación

Python

Desarrollo de algoritmos y cálculos matemáticos

Streamlit

Interfaz web interactiva

NumPy

Operaciones matriciales y numéricas

SciPy

Herramientas de cálculo científico

Pandas

Organización y presentación de datos

Plotly

Visualización gráfica interactiva

Pytest

Pruebas automatizadas

Estructura del repositorio

WORKSHOP2.
├── .devcontainer/       # Entorno de desarrollo
├── .streamlit/          # Configuración de Streamlit
├── assets/              # Recursos gráficos
├── modulos/             # Implementaciones numéricas
├── plataforma/          # Interfaz y lógica de la aplicación
├── tests/               # Pruebas del proyecto
├── app.py               # Archivo principal
├── requirements.txt     # Dependencias
├── pytest.ini           # Configuración de pruebas
└── README.md            # Documentación

Ejecución local

Para ejecutar la aplicación en un entorno local:

1. Clonar el repositorio

git clone https://github.com/andresfemag7-alt/WORKSHOP2..git
cd WORKSHOP2.

2. Instalar las dependencias

pip install -r requirements.txt

3. Ejecutar la aplicación

streamlit run app.py

La terminal indicará la dirección local desde la cual se puede acceder a la interfaz.

Alcance y limitaciones

Este proyecto tiene una finalidad académica y utiliza un modelo conceptual simplificado para demostrar la aplicación de métodos numéricos en ingeniería civil.

Los datos hidrométricos incluidos en la aplicación se consideran preliminares mientras no se complete su verificación con las fuentes originales.

Asimismo, el análisis estructural contempla simplificaciones relacionadas con las cargas, la geometría y las condiciones de apoyo.

Por lo tanto, los resultados tienen un propósito didáctico y no constituyen un diseño hidráulico o estructural apto para construcción.

Autores

Sebastian Molina Giraldo
Andrés Felipe Madroñero

Proyecto académico desarrollado para la asignatura de Algoritmos Numéricos, aplicado a problemas de Ingeniería Civil.

Repositorio: GitHub — WORKSHOP2
Aplicación: Workshop 2 — Streamlit
