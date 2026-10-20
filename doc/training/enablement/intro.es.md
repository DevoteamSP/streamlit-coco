# Introducción

## Qué es streamlit-coco

`streamlit-coco` es una librería Python/Streamlit que incrusta el Cortex
Code Agent SDK de Snowflake ("CoCo") en una app Streamlit: un Copilot en
rail lateral o en panel completo, puertas de aprobación human-in-the-loop
para herramientas destructivas, una vista previa en vivo de una app que
CoCo acaba de escribir, salida estructurada hacia tus propios widgets, y
una API headless `query()` / `CocoSession` para scripts y CI.

Paquete PyPI: `streamlit-coco`. Versión actual: **0.1.9** (alpha — la API
todavía puede cambiar). Python 3.10+, Streamlit 1.55+. Licencia: Apache-2.0.

## El problema que resuelve

Conectar el SDK de CoCo a una app Streamlit a mano implica construir, desde
cero: estado de sesión que sobreviva a los reruns de Streamlit, renderizado
en streaming de la transcripción del agente, tarjetas de herramienta
legibles en lugar de volcados JSON en bruto, y un flujo de aprobación para
todo lo que el agente pueda escribir, editar o ejecutar. `streamlit-coco`
ofrece esa plomería como un conjunto de funciones componibles (`panel()`,
`chat_input_bar()`, `copilot_rail()`, `render_approvals()`, …) para que
quien escribe la app se ocupe de la página y las opciones, no del puente de
sesión.

## Para quién es

Consultores e ingenieros que necesitan añadir un Copilot basado en CoCo a
una app Streamlit sobre una cuenta de Snowflake con acceso a Cortex Code.
Asume conocimientos básicos de Python y suficiente familiaridad con
Streamlit como para leer código con `st.container` / `st.session_state` —
la librería oculta la mayor parte de la plomería de gestión de sesión, así
que no se requiere experiencia profunda en Streamlit.

## Objetivos de aprendizaje

Al terminar esta ruta serás capaz de:

1. Explicar qué hace `streamlit-coco`, y cuándo aplica frente a usar el CLI
   de CoCo o el SDK directamente (ver la sección "When not to use" del
   README).
2. Instalar la librería, conectarla a una cuenta de Snowflake y ejecutar
   cada app de ejemplo incluida (`make chat`, `make backlog`, `make
   bi-semantic`, `make headless`, …).
3. Construir una app Streamlit usando el patrón preferido — `panel()` +
   `chat_input_bar()` — con `require_approval_for` configurado para que las
   herramientas destructivas se pausen a la espera de una decisión humana.
4. Configurar `CocoOptions` para un flujo de trabajo real e incrustar
   `copilot_rail()` en una app multipágina existente.
5. Diagnosticar una sesión que no logra conectar o una herramienta que no
   se ejecuta, usando `check_environment()`, `STREAMLIT_COCO_DEBUG` y la
   [referencia de ayuda](../technical-guide/help.html) de la Guía Técnica.

## Estimación de tiempo

| Módulo | Tiempo |
| --- | --- |
| `intro.md` (esta página) | 10 min |
| [`setup.md`](setup.html) | 20–30 min |
| [`guided-tour.md`](guided-tour.html) | 20–30 min |
| [`hands-on.md`](hands-on.html) — 6 ejercicios | 120–150 min |
| [`demo-guide.md`](demo-guide.html) — lectura + un ensayo | 30–40 min |
| **Total de Enablement** | **~3.5–4.5 horas** |

Los casos de entrenamiento ([`01-simple`](../training/01-simple.html),
[`02-intermediate`](../training/02-intermediate.html),
[`03-advanced`](../training/03-advanced.html)) son una ruta separada,
presupuestada en 20–30, 45–60 y 30–45 minutos respectivamente.

## Prerrequisitos

- Python 3.10+ y `uv` instalados localmente.
- Una cuenta de Snowflake con **acceso a Cortex Code**, y un
  `~/.snowflake/connections.toml` funcional (el `config.toml` heredado
  también funciona) — o la conexión por defecto del Snowflake CLI.
- El **CLI de CoCo** (`cortex`) instalado y accesible en `PATH` (verificar
  con `cortex --version`), o una ruta que puedas fijar mediante
  `CORTEX_CODE_CLI_PATH`.
- Acceso Git al repositorio de desarrollo
  (`github.com/DevoteamSP/streamlit-coco-dev`) si piensas ejecutar los
  ejemplos incluidos, o simplemente `pip install "streamlit-coco[sdk]"` si
  solo necesitas el paquete publicado.
- Nada más: no se requiere un warehouse de Snowflake dedicado para seguir
  esta ruta — los ejemplos usan por defecto datos de muestra de solo
  lectura o fixtures desconectados.
