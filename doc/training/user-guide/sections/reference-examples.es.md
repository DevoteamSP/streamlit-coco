# Referencia de apps de ejemplo

Cada app de ejemplo de primera parte bajo `examples/`, qué demuestra,
cómo ejecutarla y qué necesita. Ver [Referencia de comandos](reference-commands.html)
para los objetivos `make` subyacentes y [Salidas](outputs.html) para los
archivos que produce cada una.

## `chat_app.py`

Se ejecuta con `make chat`. Demuestra el patrón de integración preferido:
`check_environment()` → `render_start_gate()` → `get_or_create_session()`
→ `panel()` + `chat_input_bar()`. Su barra lateral incluye un ejecutor de
prompts de prueba respaldado por `examples/testdata/prompts.json`.
Necesita una conexión de Snowflake con acceso a Cortex Code.

## `approval_gate.py`

Se ejecuta con `make approval`. Demuestra el widget heredado CCv2 `chat()`
todo-en-uno en lugar de `panel()` — útil como referencia para apps que
siguen en la API más antigua. Necesita una conexión de Snowflake.

## `structured_output.py`

Se ejecuta con `make structured`. Demuestra `output_schema` junto con
`on_structured_output`, dirigiendo el JSON del agente hacia un widget en
lugar de texto de chat. Necesita una conexión de Snowflake.

## `headless_pipeline.py`

Se ejecuta con `make headless`. Python asíncrono puro sin import de
Streamlit; impulsa `query()` y `CocoSession` desde una terminal, cada uno
en su propio bucle de eventos. Necesita una conexión de Snowflake; no
produce ninguna interfaz en el navegador.

## `cwd_upload_chat.py`

Se ejecuta con `make cwd-upload`. Demuestra
`chat_input_bar(accept_file=...)` y `cwd_uploader()` — subidas del
navegador escritas en el `cwd` del agente. Necesita una conexión de
Snowflake para los turnos del agente; la mecánica de subida en sí no la
necesita.

## `backlog_desk/`

Se ejecuta con `make backlog`. Un Product Backlog Desk multipágina:
respaldado por archivos/JSON (sin SQL), con páginas Board / Epic / Ticket
/ Release y un Copilot en rail lateral derecho que se abre desde un botón
**Copilot** de la cabecera o un enlace de acción (se cierra con
**Close** — no es una página de navegación). Su Copilot incluye cuatro
skills basadas en prompts (no skills de orquestación `.cortex/skills/`):
Summarize sprint, Draft release notes (protegida por aprobación), Propose
ticket update (protegida por aprobación), Check definition of done. Los
datos viven bajo `data/{epics,tickets,releases,policies}`. Este es el
ejemplo de primera parte de un rail incrustado en un producto sin SQL y
sin chat. Necesita una conexión de Snowflake para el Copilot; las páginas
Board/Epic/Ticket/Release en sí solo leen JSON local.

## `bi_to_semantic/`

Se ejecuta con `make bi-semantic` (alias: `make tableau-semantic`,
obsoleto). Lee workbooks de Tableau (`.twb`/`.twbx`) y/o Power BI
(`.pbix`/`.pbit`), muestra desviaciones de KPI y de reglas de acceso,
arbitra desacuerdos mediante `request_input(schema=...)`, y escribe una
vista semántica, una política de row access, y una app consumidora
Streamlit generada (desconectada por defecto, sin necesidad de warehouse
para verla). Seis pantallas: Welcome, 1 Load, 2 Estate map (parseo
determinista), 3 KPI inventory (determinista), 4 Access-rule comparator
(Power BI parseado localmente; Tableau vía CoCo), 5 Arbitration
(`request_input`), 6 Generate (aprobación de escritura + vista previa).
Las pantallas 2 y 3 no necesitan ningún agente CoCo ni warehouse; la ruta
Tableau de la pantalla 4 y la pantalla 6 sí. Los fixtures de muestra
(paquete MIT Tableau Server y paquete Power BI Obvience) viven bajo
`examples/bi_samples/`. El `cwd` del agente para este ejemplo es
`examples/workspaces/bi_to_semantic/` (excluido de git). Vista previa: un
consumidor Python (determinista) en `127.0.0.1:8511` y un consumidor
escrito por CoCo en `:8512`, ambos vía `app_viewer()`. Los JSON Schemas de
los artefactos intermedios viven bajo
`examples/bi_to_semantic/contracts/`. Ver [Salidas](outputs.html) para
los nombres exactos de archivo.

## `app_builder/`

Se ejecuta con `make app-builder`. Generación guiada de apps Streamlit
para usuarios de negocio. Páginas: Welcome, Library (tarjetas Resume y
Create-a-new-project, con un filtro de píldoras por tema), Brief (un
brief en texto libre y bocetos, o preguntas tipadas), Studio (Build this
app / regenerate; Open Copilot; Open Preview; un expander App brief con
Save / Save & regenerate), Admin (CRUD de types y editores de guideline
skills). Cada type de app es `types/<id>/type.json` (su tarjeta de
catálogo) más un `types/<id>/SKILL.md` opcional (con `reference/` y
`CHECKLIST.md`) que CoCo lee vía `add_dirs`; `types/shared/SKILL.md`
contiene las reglas de generación comunes a cada type y no es en sí misma
una tarjeta de catálogo. El conjunto de types en vivo bloqueado es: KPI
presentation, Data quality, Call transcription, Meeting recap, Prompt
library, CSV explorer — cada uno declara un `grounding_kind` (`tabular` /
`semantic_view` / `documents` / `urls`) que decide si su paso de
perfilado es un parser pandas determinista (`engine/profile.py`) o un
trabajo de CoCo. Los documentos y URLs los obtiene la aplicación
anfitriona, nunca la propia sesión de CoCo — no se le concede ninguna
herramienta de red. La salida generada aterriza bajo
`examples/app_builder/out/<slug>/` (`brief.json`, `BRIEF.md`,
`sketches/`, `streamlit_app.py`); la vista previa se ejecuta en el puerto
8513. Necesita una conexión de Snowflake para cualquier type que use un
paso de perfilado impulsado por CoCo o para el paso Build/regenerate de
Studio.
