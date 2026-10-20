# Guía de usuario — streamlit-coco

Esta guía describe streamlit-coco 0.1.9.

Documenta el producto tal como está construido: cómo usarlo, qué hace cada
parte de su API pública, y qué produce cada pantalla o comando. No es un
tutorial — para una primera ejecución guiada, ver Enablement
[`guided-tour.html`](../enablement/guided-tour.html) y
[`hands-on.html`](../enablement/hands-on.html).

## Para quién es

Cualquiera que escriba Python contra `streamlit-coco`: incrustar un panel
o rail de Copilot en una app Streamlit, ejecutar o adaptar uno de los
ejemplos, o llamar a la API headless desde un script. Asume conocimientos
de Python en funcionamiento y nociones básicas de Streamlit; no asume
exposición previa al Cortex Code Agent SDK.

## Rutas de lectura

**Construir una app.** Lee [Conceptos](sections/concepts.html), luego
[Primeros pasos](sections/getting-started.html), luego
[Quiero construir una app CoCo mínima](sections/task-build-a-minimal-app.html).
Mantén abierta la [Referencia de la API](sections/reference-api.html)
mientras programas.

**Evaluar el producto.** Lee [Conceptos](sections/concepts.html), luego
[Quiero ejecutar las apps de ejemplo](sections/task-run-the-example-apps.html)
y [Referencia de apps de ejemplo](sections/reference-examples.html).
Consulta las [Preguntas frecuentes](sections/faq.html) para las preguntas
que más hacen los evaluadores.

**Extender o integrar más a fondo.** Lee la
[Referencia de la API](sections/reference-api.html) y la
[Referencia de comandos](sections/reference-commands.html) de principio a
fin, luego las páginas de tareas para
[aprobaciones de herramientas](sections/task-configure-tool-approvals.html),
[subida de archivos](sections/task-add-file-uploads.html),
[salida estructurada](sections/task-use-structured-output.html) y
[uso headless](sections/task-run-headless.html). La Guía Técnica
`architecture.html` y `extending.html` cubren lo que hay detrás de esta
API.

## Contenidos

### Inicio
- [Conceptos](sections/concepts.html)
- [Primeros pasos](sections/getting-started.html)

### Tareas
- [Quiero construir una app CoCo mínima](sections/task-build-a-minimal-app.html)
- [Quiero ejecutar las apps de ejemplo](sections/task-run-the-example-apps.html)
- [Quiero configurar aprobaciones de herramientas](sections/task-configure-tool-approvals.html)
- [Quiero añadir subida de archivos](sections/task-add-file-uploads.html)
- [Quiero usar salida estructurada](sections/task-use-structured-output.html)
- [Quiero ejecutar CoCo en modo headless](sections/task-run-headless.html)

### Referencia
- [Referencia de la API](sections/reference-api.html)
- [Referencia de comandos](sections/reference-commands.html)
- [Referencia de apps de ejemplo](sections/reference-examples.html)
- [Salidas](sections/outputs.html)

### Respuestas
- [Preguntas frecuentes](sections/faq.html)

## No cubierto

- **Módulo de Skills** — no existe una capa de orquestación
  `.cortex/skills/*/SKILL.md` en la raíz del repositorio. Los propios
  archivos `types/<id>/SKILL.md` del ejemplo App Builder son skills de
  orientación de CoCo internas al ejemplo, documentadas en
  [Referencia de apps de ejemplo](sections/reference-examples.html) →
  App Builder, no como un capítulo reference-skills separado.
- **Objetos de Snowflake** — esta librería no crea ni posee ningún DDL de
  Snowflake. La ejecución SQL solo ocurre a través de la propia herramienta
  SQL del agente, protegida por aprobación, usando lo que el rol conectado
  ya pueda hacer.
- **Native App** — el repositorio no tiene `manifest.yml` ni
  `snowflake.yml`. El empaquetado Native App no está lanzado.
- **Modos de despliegue más allá de local** — solo se lanza hoy un
  objetivo: local (Streamlit, el CLI de CoCo y la configuración de
  Snowflake en la misma máquina). Streamlit in Snowflake y SPCS solo se
  discuten como alcance del modelo de amenazas en la Guía Técnica; no
  están implementados.
- **Catálogo de controles** — no hay una capa de archivos de reglas o
  rúbrica de puntuación en este repositorio.
- **Infraestructura como código** — no hay Terraform en este repositorio.
- **Pantallas de las apps de ejemplo, página por página** — las tres apps
  de ejemplo tienen cada una sus propias pantallas, pero esta guía cubre
  cada app como una única entrada de referencia en
  [Referencia de apps de ejemplo](sections/reference-examples.html) en
  lugar de una entrada por página de Streamlit. Cada ejemplo incluye su
  propio README con un recorrido a nivel de página; duplicarlo aquí se
  desviaría de él.
