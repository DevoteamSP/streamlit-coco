# Salidas

Cada archivo o artefacto que produce `streamlit-coco` o sus apps de
ejemplo, qué contiene, y dónde aterriza.

## Archivos subidos

Producido por: `upload_to_cwd()`, `cwd_uploader()`, o
`chat_input_bar(accept_file=...)` — ver
[Quiero añadir subida de archivos](task-add-file-uploads.html).

Aterriza en: `<CocoOptions.cwd>/_uploads/` (el nombre del subdirectorio
es configurable vía `subdir`/`upload_subdir`).

Léelo: es una copia simple del archivo que subió el usuario, bajo su
nombre original (validado); cualquier herramienta del agente que lea
desde `cwd` puede verlo directamente.

## Salida de build de App Builder

Producido por: la acción **Build this app** / **regenerate** de la página
Studio en `examples/app_builder/`.

Aterriza en: `examples/app_builder/out/<slug>/`, conteniendo
`brief.json` (el brief estructurado), `BRIEF.md` (el brief legible por
humanos, editable y recargable en el editor de CoCo), `sketches/`
(cualquier boceto subido), y `streamlit_app.py` (la app generada).

Léelo: `streamlit_app.py` es un script Streamlit ejecutable; `BRIEF.md` es
la fuente de verdad de lo que se pidió, y es lo que **Save & regenerate**
escribe antes de encolar un nuevo turno de CoCo.

## Artefactos intermedios de BI → Semantic

Producido por: las pantallas 2 a 5 de `examples/bi_to_semantic/`.

Aterriza en: `examples/bi_to_semantic/out/`, conteniendo
`estate_map.json` (pantalla 2), `kpi_inventory.json` (pantalla 3),
`access_rules.json` (pantalla 4), y `decisions.json` (registro de
arbitraje de la pantalla 5).

Léelo: cada archivo coincide con su JSON Schema bajo
`examples/bi_to_semantic/contracts/` (`estate_map.schema.json`,
`kpi_inventory.schema.json`, `access_rules.schema.json`);
`decisions.json` registra lo que eligió el revisor en cada punto de
arbitraje de la pantalla 5.

## Salida generada de BI → Semantic

Producido por: la pantalla 6 (Generate) de `examples/bi_to_semantic/`,
tras la aprobación de escritura.

Aterriza en: `examples/bi_to_semantic/out/streamlit_dash/` (el consumidor
determinista) y `examples/bi_to_semantic/out/streamlit_dash_coco/` (el
consumidor escrito por CoCo), junto con la vista semántica SQL/YAML
generada y la política de row access.

Léelo: ambos directorios consumidores son apps Streamlit ejecutables,
previsualizadas vía `app_viewer()` en los puertos 8511 (determinista) y
8512 (escrito por CoCo). Los archivos de vista semántica y política de
row access son el SQL/YAML a revisar antes de aplicarlos a una cuenta de
Snowflake.

## Escrituras del Copilot de Backlog Desk

Producido por: las skills Edit/Write del Copilot de Backlog Desk (Draft
release notes, Propose ticket update), ambas protegidas por aprobación.

Aterriza en: `examples/backlog_desk/data/tickets/` (JSON de tickets
actualizado) y `examples/backlog_desk/data/releases/` (notas de release
en Markdown).

Léelo: el JSON de tickets sigue la misma forma que ya leen las páginas
Board/Epic/Ticket; las notas de release son Markdown plano.

## Archivos del proceso hijo de `app_viewer()`

Producido por: cualquier llamada a `app_viewer(app_dir, ...)`.

Aterriza en: dentro del propio `app_dir` previsualizado — `.preview.log`,
`.preview.pid`, `.preview.port`.

Léelo: `.preview.log` es la salida estándar/error estándar del proceso
hijo de Streamlit, usada por el tail de log del flujo "Fix with CoCo";
`.preview.pid` y `.preview.port` identifican el proceso hijo en
ejecución. Solo hay una vista previa por `app_dir` a la vez — nunca
apuntes `app_dir` a la app que aloja el propio viewer.

## Artefactos de build de release

Producido por: `make build` (orientado a mantenedores, ver
[Referencia de comandos](reference-commands.html)).

Aterriza en: `dist/` — un sdist y un wheel.

Léelo: estos son los archivos que `make publish` sube a PyPI; no se
producen por el uso normal de la librería.
