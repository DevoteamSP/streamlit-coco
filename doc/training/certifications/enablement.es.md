# streamlit-coco — Certificación Enablement

**Umbral de aprobación: 8/10.** Prerrequisito: ruta de Enablement.

### Q1. ¿Qué problema resuelve `streamlit-coco` para quien escribe una app Streamlit?

a) Reemplaza por completo el CLI de CoCo, así que nunca es necesario instalar ningún CLI
b) Proporciona plomería lista para usar de sesión, renderizado en streaming, tarjetas de herramienta y flujo de aprobación, para que quien escribe la app no la construya a mano
c) Genera automáticamente definiciones de roles y grants de Snowflake
d) Aprovisiona y gestiona el warehouse de Snowflake contra el que se ejecuta una sesión de CoCo

### Q2. ¿Qué afirmación describe mejor `panel()`?

a) Un Copilot en rail lateral compuesto para apps multipágina
b) Un primitivo nativo de transcripción/campo/aprobaciones/Stop que devuelve un `CocoChatResult`
c) Un widget de chat todo-en-uno heredado de Custom Component v2
d) Una columna de vista previa que incrusta una app Streamlit hija en un iframe

### Q3. ¿Qué añade `copilot_rail()` sobre `panel()`?

a) Un Copilot en rail lateral derecho con un selector de conexión, trabajos encolados y preguntas de ejemplo
b) Una API headless puramente asíncrona sin import de Streamlit
c) Un enrutador de salida estructurada basado en JSON Schema
d) Una protección contra path-traversal en los nombres de archivo subidos

### Q4. ¿Qué hace `app_viewer()`?

a) Ejecuta la herramienta SQL del agente contra el rol de Snowflake conectado
b) Lanza un proceso hijo `streamlit run` para una app generada, lo incrusta en un iframe y ofrece una acción Fix
c) Transmite los eventos NDJSON en bruto del agente a la terminal
d) Sube archivos del navegador al directorio de trabajo del agente

### Q5. ¿Qué comando lanza la implementación de referencia de primera parte del patrón preferido (`panel()` + `chat_input_bar()`)?

a) `make demo`
b) `make chat`
c) `make run-app`
d) `make copilot`

### Q6. ¿Qué conjunto de prerrequisitos es correcto para empezar la ruta de Enablement?

a) Python 3.10+, una cuenta de Snowflake con acceso a Cortex Code, el CLI de CoCo (`cortex`) accesible en `PATH` o mediante `CORTEX_CODE_CLI_PATH`, y una configuración de conexión de Snowflake funcional
b) Node.js 18+, un warehouse de Snowflake dedicado y una licencia GHAS de pago
c) Python 3.8+, Docker, y un manifiesto de Native App
d) Una cuenta de Streamlit Community Cloud y un archivo `snowflake.yml`

### Q7. ¿Cuáles de estos forman parte del pipeline del patrón preferido demostrado en `examples/chat_app.py`? (Opción múltiple — selecciona todas las que apliquen)

a) `check_environment()`
b) `render_start_gate()`
c) `get_or_create_session()`
d) `panel()`
e) `chat_input_bar()`
f) `chat()` (componente CCv2 heredado)

### Q8. ¿Qué comando instala `streamlit-coco` para alguien que solo necesita el paquete publicado, sin un checkout del repositorio de desarrollo?

a) `pip install "streamlit-coco[sdk]"`
b) `npm install streamlit-coco`
c) `make install` (funciona solo dentro del checkout del repo de desarrollo)
d) `uv build`

### Q9. ¿Bajo qué licencia se publica `streamlit-coco`?

a) MIT
b) Apache-2.0
c) GPL-3.0
d) BSD-3-Clause

### Q10. ¿Cuál es la versión actual del paquete y el estado de lanzamiento que describe este pack de entrenamiento?

a) `0.1.6`, una versión estable
b) `0.1.9`, alpha — la API todavía puede cambiar
c) `1.0.0`, disponibilidad general
d) `0.2.0`, beta

## Answer Key

| P | Respuesta | Explicación |
|---|--------|-------------|
| 1 | **b** | La librería proporciona estado de sesión, streaming de transcripción, tarjetas de herramienta y plomería de aprobación como funciones componibles, para que quien escribe la app se ocupe de la página y las opciones, no del puente de sesión. |
| 2 | **b** | `panel(session, **kwargs) -> CocoChatResult` es el primitivo nativo de salida de transcripción/campo con aprobaciones y un control Stop. |
| 3 | **a** | `copilot_rail()` compone `panel()` en un Copilot en rail lateral derecho con un selector de conexión, trabajos encolados, configuración de visualización de la transcripción y preguntas de ejemplo. |
| 4 | **b** | `app_viewer(app_dir, ...)` lanza un proceso hijo `streamlit run`, lo incrusta en un iframe y ofrece Fix with CoCo raspando el log de la vista previa. |
| 5 | **b** | El Makefile mapea `chat` a `Run examples/chat_app.py`; `demo`, `run-app` y `copilot` no son objetivos del Makefile. |
| 6 | **a** | Los prerrequisitos son Python 3.10+, una cuenta de Snowflake habilitada para Cortex Code, el CLI `cortex` en PATH (o `CORTEX_CODE_CLI_PATH`), y un `connections.toml`/`config.toml` funcional — no se requiere warehouse dedicado, Docker ni manifiesto de Native App. |
| 7 | **A, B, C, D, E** | `chat_app.py` encadena `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`; `chat()` es el componente CCv2 heredado usado en `examples/approval_gate.py`, no en este ejemplo. |
| 8 | **a** | La ruta que solo requiere el paquete publicado es `pip install "streamlit-coco[sdk]"`; `make install` apunta a un checkout del repositorio, y los otros dos comandos no instalan este paquete. |
| 9 | **b** | `streamlit-coco` se publica bajo Apache-2.0. |
| 10 | **b** | El pack describe la versión `0.1.9`, indicada como alpha — la API todavía puede cambiar. |
