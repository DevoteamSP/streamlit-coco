# Extensión

Una sección por cada punto de extensión que el repositorio realmente
expone.

## Renderizador de texto conectable (`text_renderer=`)

`panel()`, `render_transcript()`, y `render_output_field()`
(`streamlit_coco/ui.py`, `streamlit_coco/display.py`) aceptan
`text_renderer=` para que una app pueda renderizar texto de
asistente/usuario con cualquier API de texto de Streamlit, o un callable
personalizado, en lugar del `st.markdown` fijo por defecto.

**Valores nombrados:** `"markdown"` (por defecto), `"write"`, `"text"`,
`"caption"`, `"code"` (también acepta nombres con prefijo `st.*`). Pasar
un nombre desconocido lanza un `ValueError` listando los nombres
conocidos.

**Forma callable:** pasa cualquier función con forma
`Callable[[str], None]` — se invoca con el texto del mensaje.

**Archivos a tocar:**
- `streamlit_coco/text_renderer.py` — la tabla de resolución nombre →
  callable. Añade aquí un nuevo valor nombrado si extiendes el conjunto
  incluido.
- Los puntos de llamada en `streamlit_coco/ui.py` (`panel`) y
  `streamlit_coco/display.py` (`render_transcript`,
  `render_output_field`) ya propagan `text_renderer`; un renderizador
  nuevo solo necesita registrarse una vez.

**Paso de regeneración/verificación:** ejecuta `examples/chat_app.py`
(`make chat`) con el nuevo renderizador pasado explícitamente y confirma
que el texto de asistente/usuario se renderiza como se espera; no se
necesita ningún paso de build ya que esto es Python puro.

**Tests a añadir:** extiende
`doc/features/text-renderer/test-checklist.md` con el nuevo valor
nombrado, y añade un caso al archivo de test unitario relevante que
cubra la resolución del renderizador (no hay un `test_text_renderer.py`
dedicado en el árbol actual — revisa `tests/` para la cobertura
existente más cercana antes de añadir un archivo nuevo).

## Despacho de familia/nombre de herramienta

`streamlit_coco/tool_names.py` mapea un nombre de herramienta en bruto a
una enumeración `ToolFamily` (`ASK_USER`, `SQL`, `READ`, `WRITE`,
`EDIT`, `BASH`, `GLOB`, `GREP`, `EXIT_PLAN`, `GENERIC`) vía
`tool_family(name)`, usando una tabla de búsqueda normalizada
(minúsculas, sin separadores). Cualquier nombre de herramienta que no
coincida con una familia conocida — incluidas las herramientas MCP —
recae en `GENERIC` y obtiene una tarjeta de herramienta genérica en
lugar de una específica de familia.

**Archivos a tocar:**
- `streamlit_coco/tool_names.py` — añade el/los nombre(s) normalizado(s)
  de la herramienta a `_FAMILY_BY_NORMALIZED`, y añade un caso a
  `family_label()` si necesita una etiqueta de cabecera dedicada en
  lugar del nombre de herramienta en bruto.
- `streamlit_coco/tool_cards.py` / `streamlit_coco/tool_extract.py` —
  añade el renderizado de tarjeta específico de familia y cualquier
  extracción de entrada/diff/SQL que necesite la nueva familia. Una
  familia dejada sin registrar aquí todavía se renderiza (vía el
  fallback `GENERIC`); registrarla solo cambia cómo se muestra.

**Paso de regeneración/verificación:** ejecuta una demo de chat (`make
chat`) con un prompt que ejercite la nueva herramienta y confirma que la
tarjeta de herramienta se renderiza con la etiqueta de familia esperada
y la vista previa en lugar del fallback genérico.

**Tests a añadir:** un caso en los tests unitarios que cubra
`tool_family()` / `family_label()` para el nuevo nombre de herramienta
(ver el patrón de cobertura de familia de herramienta existente en
`tests/`), y un fixture NDJSON bajo `tests/fixtures/ndjson/` si la nueva
familia necesita cobertura de normalización de eventos en
`test_ndjson_fixtures.py`.

## Catálogo `types/<id>/` de App Builder y paquetes de skill

Cada type de app de App Builder es una carpeta bajo
`examples/app_builder/types/`:

```text
types/<id>/
  type.json          tarjeta de catálogo: id, name, icon, users, needs,
                      needs_snowflake, topics, grounding_kind, brief
                      (context, enables, does_not, questions)
  SKILL.md            opcional — reglas de layout y datos específicas
                      del type, leídas por CoCo vía add_dirs al generar la app
  reference/           opcional — material de referencia de apoyo para SKILL.md
  CHECKLIST.md          opcional — lista de autocomprobación que el prompt
                      de generación ejecuta contra sí una vez tras un Write, antes de detenerse
types/shared/SKILL.md   reglas de generación para todo type (sin type.json —
                      no es una tarjeta de catálogo); cada prompt Build/regenerate
                      le dice a CoCo que lea este archivo más el SKILL.md propio
                      del type (ambos montados vía add_dirs)
```

Este es un punto de extensión a nivel de contenido: añadir un type no
requiere ningún cambio de código Python, solo una nueva carpeta
`types/<id>/` (o usar el editor de types de la pantalla Admin, que
escribe los mismos archivos).

**Archivos a tocar:**
- `examples/app_builder/types/<id>/type.json` — obligatorio; sigue la
  forma de un type existente (por ejemplo
  `types/call-transcription/type.json`) para la estructura de
  `brief.questions` y los valores de `grounding_kind` (`tabular` /
  `semantic_view` / `documents` / `urls`) que deciden si el paso de
  perfilado es un parser pandas determinista
  (`examples/app_builder/engine/profile.py`) o un trabajo de CoCo.
- `examples/app_builder/types/<id>/SKILL.md` — opcional pero esperado
  para un type real; sin él, CoCo genera solo contra las reglas
  compartidas.
- `examples/app_builder/engine/paths.py` — no se necesita ningún cambio;
  `TYPES_DIR` ya apunta a `types/`, así que una carpeta nueva se recoge
  automáticamente.

**Paso de regeneración/verificación:** `make app-builder`, abre Library,
confirma que la nueva tarjeta de type aparece (filtrada correctamente
por sus `topics`), rellena un brief, y Build — confirma que el
`streamlit_app.py` generado sigue las reglas del nuevo `SKILL.md` y (si
hay un `CHECKLIST.md`) que el prompt de generación se autocomprueba
contra él una vez.

**Tests a añadir:** un caso en `test_app_builder_catalog.py` que cubra
que el nuevo `type.json` se parsea y valida contra los campos de tarjeta
de catálogo que leen las páginas Library/Brief/Admin; un caso en
`test_app_builder_profile.py` si `grounding_kind` dispara una nueva ruta
de perfilado determinista.

## Añadir una nueva app de ejemplo

El patrón establecido para un ejemplo basado en rail (como en
`examples/bi_to_semantic/` y `examples/app_builder/`) compone
`copilot_rail()` para el Copilot y `app_viewer()` para una vista previa
en vivo de lo que sea que escriba CoCo, conectados a través de `on_fix` /
encolado de trabajos — ver
[architecture](architecture.html#example-app-orchestration).

**Archivos a tocar:**
- `examples/<name>/` — carpeta nueva con su propio `app.py` (o
  `app_pages/` multipágina), siguiendo el patrón de composición del
  ejemplo existente más cercano en forma al nuevo (`backlog_desk/` para
  un ejemplo de rail sin SQL; `bi_to_semantic/` o `app_builder/` para un
  ejemplo de rail + vista previa).
- `Makefile` — añade un objetivo `<name>:` que ejecute el nuevo ejemplo
  (reflejando un objetivo existente, por ejemplo `bi-semantic:`), añádelo
  a `.PHONY`, y añade una línea a `help`.
- `doc/deployment/local.md` §5 y `doc/testing.md` — añade el nuevo
  objetivo `make` a la tabla de ejemplos para que se descubra desde la
  documentación que ya los lista.

**Paso de regeneración/verificación:** `make <name>` se ejecuta y
alcanza una pantalla usable; si el ejemplo usa `app_viewer()`, confirma
que el puerto de vista previa no colisiona con el puerto fijo de un
ejemplo existente (los ejemplos chat/backlog no usan `app_viewer`;
`bi_to_semantic` usa `:8511`/`:8512`; `app_builder` usa `:8513`).

**Tests a añadir:** como mínimo un test de smoke paralelo a la cobertura
de `test_smoke.py` de los ejemplos existentes, y una entrada de checklist
de funcionalidad bajo `doc/features/<feature>/test-checklist.md` si el
ejemplo ejercita comportamiento de interfaz nuevo en lugar de solo
recomponer primitivos existentes.
