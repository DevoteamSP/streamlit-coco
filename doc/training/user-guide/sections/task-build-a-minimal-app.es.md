# Quiero construir una app CoCo mínima

**Para** un desarrollador Python que construye una app Streamlit · **10
min** · **un entorno Python funcional**

Terminas con una app Streamlit de una sola página que incrusta un panel de
CoCo y una barra de entrada, usando el patrón de integración preferido.

## Antes de empezar

- `streamlit-coco[sdk]` instalado (ver Enablement
  [`setup.html`](../../enablement/setup.html)).
- Una conexión de Snowflake configurada y accesible —
  `check_environment().ready` ya debería ser `True`; ver
  [Primeros pasos](getting-started.html).
- No se requiere ninguna app CoCo previa; este es el punto de partida para
  el resto de páginas de tareas de esta guía.

## Pasos

1. Crea `streamlit_app.py` y construye un `CocoOptions` con al menos un
   nombre de conexión:

   ```python
   import streamlit as st
   import streamlit_coco as st_coco

   st.set_page_config(page_title="Minimal CoCo app")

   options = st_coco.CocoOptions(
       connection="my_connection",
       cwd=".",
   )
   ```

2. Llama a `check_environment()` a través de la puerta de aterrizaje, y
   detén el script si no está listo:

   ```python
   if not st_coco.render_start_gate(options):
       st.stop()
   ```

   `render_start_gate()` renderiza la propia pantalla de aterrizaje
   (estado SDK/CLI/Snowflake, una acción **Start**) y devuelve `False`
   mientras el entorno o el usuario no lo hayan confirmado — tu app debe
   llamar a `st.stop()` en ese caso, `render_start_gate()` no detiene el
   script por ti.

3. Obtén o crea la sesión para esta página, y monta el panel y su barra
   de entrada:

   ```python
   session = st_coco.get_or_create_session(options)
   st_coco.panel(session)
   st_coco.chat_input_bar(session)
   ```

   `get_or_create_session()` almacena la sesión en
   `st.session_state["coco"]` por defecto (sobrescribible con `key=`) y la
   reutiliza a través de los reruns.

4. Ejecuta la app:

   ```bash
   streamlit run streamlit_app.py
   ```

5. Escribe un prompt en la barra de entrada al pie de la página y confirma
   que la transcripción transmite una respuesta encima de ella.

## Resultado

Una pestaña del navegador mostrando el panel de CoCo: una cabecera de
estado, una transcripción vacía, y la barra de entrada del chat. Tras un
prompt, la transcripción se llena con la respuesta en streaming del agente
y cualquier tarjeta de herramienta que haya usado. Esta app mínima no
escribe ningún archivo por sí sola — la salida de archivos empieza cuando
añades subidas ([Quiero añadir subida de archivos](task-add-file-uploads.html))
o el agente escribe en `cwd`.

## Variaciones

- Usa `copilot_rail()` en lugar de `panel()` + `chat_input_bar()` para
  incrustar CoCo como un rail lateral derecho dentro de una app más
  grande y multipágina en lugar de un chat de una sola página — ver los
  ejemplos Backlog Desk y BI → Semantic en
  [Referencia de apps de ejemplo](reference-examples.html).
- Define `panel(session, output_mode="field")` para renderizar solo la
  última salida del asistente en lugar de la transcripción completa.
- Define `warm_up=True` en `render_start_gate()` (el valor por defecto)
  para iniciar la sesión en cuanto la puerta se supera, en lugar de
  esperar al primer prompt.

## Si falla

- [`SDKNotInstalledError`](../../technical-guide/help.html#sdk-not-installed)
- [`CLINotFoundError`](../../technical-guide/help.html#cli-not-found)
- [Sesión atascada en "Starting CoCo…"](../../technical-guide/help.html#session-stuck-connecting)
- [Campo de entrada deshabilitado tras el arranque](../../technical-guide/help.html#input-disabled-after-boot)
