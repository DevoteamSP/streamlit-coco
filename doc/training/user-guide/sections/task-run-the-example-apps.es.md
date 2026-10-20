# Quiero ejecutar las apps de ejemplo

**Para** cualquiera que esté evaluando o aprendiendo la librería · **20
min** · **una conexión de Snowflake para las demos respaldadas por CoCo**

Terminas con cada una de las apps de ejemplo del repositorio ejecutándose
localmente, y sabiendo cuál demuestra cada parte de la API.

## Antes de empezar

- `streamlit-coco[sdk]` instalado y `check_environment().ready` es `True`
  (ver [Primeros pasos](getting-started.html)).
- Un checkout del repositorio (los ejemplos se ejecutan desde objetivos
  `make`, no solo desde un `pip install`).
- `headless_pipeline.py` y las pantallas de estate-map/KPI de BI → Semantic
  se ejecutan sin una conexión de Snowflake en vivo; el resto sí la
  necesita.

## Pasos

1. Ejecuta la demo de chat con el patrón preferido:

   ```bash
   make chat
   ```

   Esto es `examples/chat_app.py` — la app funcional más pequeña,
   construida sobre `check_environment` → `render_start_gate` →
   `get_or_create_session` → `panel()` + `chat_input_bar()`. Su barra
   lateral incluye un ejecutor de prompts de prueba respaldado por
   `examples/testdata/prompts.json`.

2. Ejecuta la demo heredada todo-en-uno:

   ```bash
   make approval
   ```

   Esto es `examples/approval_gate.py`, construido sobre el helper
   heredado CCv2 `chat()` en lugar de `panel()`.

3. Ejecuta la demo de salida estructurada:

   ```bash
   make structured
   ```

   Esto es `examples/structured_output.py` — define `output_schema` y
   dirige el JSON del agente hacia un widget vía `on_structured_output`
   en lugar de texto de chat.

4. Ejecuta la demo headless desde una terminal, sin navegador:

   ```bash
   make headless
   ```

   Esto es `examples/headless_pipeline.py` — Python asíncrono puro sin
   import de Streamlit, impulsando `query()` y `CocoSession`
   directamente.

5. Ejecuta la demo de subida de archivos:

   ```bash
   make cwd-upload
   ```

   Esto es `examples/cwd_upload_chat.py` —
   `chat_input_bar(accept_file=...)` y `cwd_uploader()` conectando
   subidas del navegador al `cwd` del agente.

6. Ejecuta las dos demos multipágina en rail lateral derecho:

   ```bash
   make backlog        # Product Backlog Desk — respaldado por archivos/JSON, sin SQL
   make bi-semantic     # BI -> Semantic (alias: make tableau-semantic)
   ```

7. Ejecuta la demo de generación guiada de apps:

   ```bash
   make app-builder
   ```

Cada objetivo `make` y sus variables se listan en
[Referencia de comandos](reference-commands.html); qué demuestra cada
ejemplo y qué necesita está en
[Referencia de apps de ejemplo](reference-examples.html).

## Resultado

Cada objetivo `make` abre (o imprime, en el caso de `make headless`) una
app en ejecución en su propio puerto. Nada fuera de `examples/` se
modifica al ejecutar una demo; los artefactos generados aterrizan bajo el
propio `out/` o `data/` de cada ejemplo — ver [Salidas](outputs.html).

## Variaciones

- `make run` ejecuta `examples/chat_app.py` por defecto; define
  `EXAMPLE=` para apuntarlo a un archivo de ejemplo diferente.
- `make tableau-semantic` es un alias obsoleto de `make bi-semantic` — usa
  este último.

## Si falla

- [La vista previa no arranca](../../technical-guide/help.html#preview-wont-start)
- ["Fix with CoCo" no está conectado para una pantalla](../../technical-guide/help.html#fix-with-coco-not-wired)
- [Fallo de parseo del log de vista previa](../../technical-guide/help.html#preview-log-parse-miss)
