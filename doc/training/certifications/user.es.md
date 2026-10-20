# streamlit-coco — Certificación User

**Umbral de aprobación: 24/30.** Prerrequisito: Training completado.

### Q1. ¿Cuál es el orden recomendado de los tres casos de Training?

a) `03-advanced` → `02-intermediate` → `01-simple`
b) `01-simple` → `02-intermediate` → `03-advanced`
c) `02-intermediate` → `01-simple` → `03-advanced`
d) Cualquier orden — no hay una secuencia recomendada

### Q2. ¿Qué distingue a `01-simple` de `02-intermediate`?

a) `01-simple` usa datos de muestra y es totalmente guiado; `02-intermediate` trabaja sobre los propios datos del alumno con puntos de control en lugar de pasos clic a clic
b) `01-simple` es el único caso que usa datos reales de Snowflake
c) `02-intermediate` elimina todos los datos y toda la guía
d) Los dos casos son idénticos excepto por su presupuesto de tiempo

### Q3. ¿Cuál es el rasgo definitorio de `03-advanced`?

a) Repite `01-simple` con un conjunto de datos de muestra más grande
b) Algo se rompe — extraído de un incidente real o de una entrada "Fixed" del CHANGELOG — y el alumno lo diagnostica solo
c) Es enteramente de opción múltiple, sin componente práctico
d) Solo cubre la API headless `query()`

### Q4. ¿Qué secuencia de llamadas usa `examples/chat_app.py` para implementar el patrón preferido?

a) `chat()` → `render_approvals()` → `send_prompt()`
b) `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`
c) `require_environment()` → `copilot_rail()` → `app_viewer()`
d) `CocoSession()` → `query()` → `events_to_dataframe()`

### Q5. ¿Qué devuelve `panel()`?

a) `None`
b) Un `CocoChatResult`
c) Un `CocoEnvironment`
d) Un `CocoSession`

### Q6. En `panel()`, ¿qué hace definir `output_label=None`?

a) Renderiza la salida con la etiqueta por defecto "CoCo output"
b) Oculta el contenedor de salida con borde
c) Cambia el modo de salida de `"transcript"` a `"field"`
d) Deshabilita el botón Stop

### Q7. ¿Qué parámetro de `panel()` alterna entre mostrar la transcripción en curso y mostrar solo la última salida en estilo campo?

a) `output_mode` (`"transcript"` o `"field"`)
b) `show_status`
c) `status_expanded`
d) `text_renderer`

### Q8. ¿Qué habilita `chat_input_bar(session, accept_file=True)`?

a) Renderizado de salida JSON estructurada
b) Adjuntar archivos, guardados en el directorio de trabajo de la sesión mediante los helpers de subida
c) Un selector de preguntas de ejemplo en rail lateral derecho
d) Un banner de modo plan con un botón Execute plan

### Q9. ¿Cuál de estos es un parámetro real de `copilot_rail()`?

a) `example_questions`
b) `demo_mode`
c) `sidebar_width`
d) `rail_theme`

### Q10. ¿Para qué se usa `job=` en `copilot_rail()`?

a) Programa una tarea en segundo plano basada en cron
b) Pasa un diccionario como `{prompt, label, status, expect_structured}` para encolar un trabajo que el rail debe enviar
c) Define el warehouse de Snowflake para la sesión
d) Configura el trabajo de CI que construye el rail

### Q11. ¿Qué añade `transcript_display_config()` a una interfaz basada en rail?

a) Un popover con píldoras/sliders "Last messages" y "First n characters" para controlar la visualización de la transcripción
b) Un botón que exporta la transcripción a CSV
c) Un interruptor de modo oscuro
d) Un control para cambiar la interfaz entre etiquetas en inglés y francés

### Q12. ¿A qué debe apuntar `app_dir` para que `app_viewer()` funcione correctamente?

a) Al mismo directorio que la app anfitriona que llama a `app_viewer()`
b) A una carpeta que contenga un `streamlit_app.py` (o el script nombrado vía `script_name`)
c) A cualquier directorio que contenga un `Makefile`
d) A la carpeta `dist/` producida por `make build`

### Q13. ¿Qué hace por defecto el botón "Fix with CoCo" en `app_viewer()`?

a) Reescribe automáticamente la app generada sin ningún paso de aprobación
b) Llama a `on_fix` con un prompt construido a partir de `default_fix_prompt(traceback, app_dir)`, normalmente encolando un trabajo para CoCo
c) Reinicia el proceso hijo `streamlit run` con la configuración por defecto
d) Elimina el log de vista previa anterior

### Q14. ¿Cuántas vistas previas de `app_viewer()` pueden apuntar al mismo `app_dir` a la vez?

a) Ilimitadas, siempre que los puertos difieran
b) Una
c) Dos — una para la app determinista y una para la app escrita por CoCo
d) Tantas como quepan en el rango de puertos 8511–8520

### Q15. ¿Qué campo de `CocoOptions` controla cuánto tiempo espera la app una decisión humana sobre una aprobación pendiente antes de lanzar un error?

a) `max_turns`
b) `approval_timeout_seconds` (por defecto `600.0`)
c) `permission_mode`
d) `require_approval_for`

### Q16. ¿Cuál es el valor por defecto de `CocoOptions.permission_mode`?

a) `"plan"`
b) `"auto"`
c) `"default"`
d) `"approve_all"`

### Q17. ¿Qué función sondea el entorno (instalación del SDK, accesibilidad del CLI, configuración de Snowflake) sin iniciar un agente, y nunca lanza una excepción?

a) `require_environment()`
b) `check_environment()`
c) `CocoSession.ensure_ready()`
d) `resolve_snowflake_config_path()`

### Q18. Si no se pasa `toml_file` y existe exactamente un `*.toml` bajo `~/.snowflake/`, ¿qué ocurre?

a) La librería se niega a arrancar y lanza `SnowflakeConfigNotFoundError`
b) Se usa ese único archivo, sin importar su nombre
c) La librería solo busca un archivo literalmente llamado `connections.toml`
d) Se pide al usuario interactivamente que elija un archivo

### Q19. Con varios archivos `*.toml` bajo `~/.snowflake/` y sin `toml_file` dado, ¿cuál es el orden de selección?

a) Solo alfabético
b) `connections.toml` primero, luego `config.toml`, luego alfabético
c) El archivo modificado más recientemente primero
d) `config.toml` primero, luego `connections.toml`, luego alfabético

### Q20. ¿Qué demuestra `examples/structured_output.py`?

a) `output_schema` junto con `on_structured_output`, dirigiendo el JSON del agente hacia un widget de la app en lugar de texto de chat
b) Un pipeline puramente asíncrono sin import de Streamlit
c) Subida de archivos al directorio de trabajo del agente
d) Un Copilot en rail lateral derecho sin herramienta SQL

### Q21. ¿Qué demuestra `examples/headless_pipeline.py`?

a) `panel()` incrustado en una app multipágina
b) Python asíncrono puro usando `query()` / `CocoSession`, sin import de Streamlit, ejecutado desde una terminal
c) `copilot_rail()` combinado con `app_viewer()`
d) El componente CCv2 heredado `chat()`

### Q22. ¿Qué tipo de demo es `examples/approval_gate.py`?

a) El patrón preferido (`panel()` + `chat_input_bar()`)
b) Un script headless
c) El componente CCv2 heredado `chat()` todo-en-uno
d) Un ejemplo basado en rail sin herramienta SQL

### Q23. ¿Qué distingue a `examples/backlog_desk/` frente a los demás ejemplos de app?

a) Es el primer ejemplo basado en rail que no usa herramienta SQL en absoluto — sus datos están respaldados por archivos/JSON
b) Es el único ejemplo que requiere un warehouse de Snowflake dedicado
c) Es el único ejemplo que usa el componente CCv2 heredado
d) Es el único ejemplo sin ningún Copilot

### Q24. En `examples/backlog_desk/`, ¿cómo se abre su Copilot?

a) Es una página de navegación dedicada en la barra lateral
b) Se abre automáticamente en cada carga de página
c) Desde un botón "Copilot" de la cabecera o un enlace de acción, y se cierra con "Close" — no es una página de navegación
d) Solo mediante el objetivo `make headless`

### Q25. ¿Qué tipos de archivos fuente lee `examples/bi_to_semantic/` como entrada?

a) Solo archivos de stage de Snowflake
b) Workbooks Tableau `.twb`/`.twbx` y/o Power BI `.pbix`/`.pbit`
c) Solo exportaciones CSV de un data warehouse
d) Archivos `.cortex/skills/*/SKILL.md`

### Q26. ¿Dónde aterrizan por defecto los archivos subidos vía `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)`?

a) `<CocoOptions.cwd>/_uploads/` (el nombre del subdirectorio es configurable)
b) El propio directorio de instalación de la app Streamlit
c) `~/.snowflake/`
d) `dist/`

### Q27. ¿Qué escribe el paso "Build" de App Builder en `examples/app_builder/out/<slug>/`?

a) Solo un archivo `.whl` compilado
b) `brief.json`, `BRIEF.md`, `sketches/*`, y `streamlit_app.py`
c) Un SBOM CycloneDX
d) Solo un archivo `.preview.log`

### Q28. ¿Dónde se publica el SBOM de la build de release?

a) En `examples/app_builder/out/`
b) Como assets del GitHub Release (JSON CycloneDX), generado solo en CI
c) En `_uploads/`
d) Aún no se genera en ningún sitio

### Q29. ¿Qué presenta `render_approvals()`, y en qué orden de botones?

a) Deny, Always allow, Approve once
b) Approve once, Always allow, Deny
c) Approve once, Deny (no hay opción "Always allow")
d) Un único botón "Approve" sin opción de denegar

### Q30. ¿Cuáles de estas familias de herramientas nunca exponen una opción "Always allow" en la interfaz de aprobación? (Opción múltiple — selecciona todas las que apliquen)

a) `AskUserQuestion`
b) `ExitPlanMode`
c) La herramienta SQL
d) Edit
e) Write
f) Grep

## Answer Key

| P | Respuesta | Explicación |
|---|--------|-------------|
| 1 | **b** | Los casos están numerados y progresan `01-simple` → `02-intermediate` → `03-advanced`, aumentando en dificultad. |
| 2 | **a** | `01-simple` es el camino feliz totalmente guiado con datos de muestra; `02-intermediate` usa los datos propios del alumno con puntos de control en lugar de pasos clic a clic. |
| 3 | **b** | `03-advanced` presenta una rotura real (incidente real o entrada "Fixed" del CHANGELOG) que el alumno diagnostica sin pasos guiados. |
| 4 | **b** | Esta es exactamente la cadena de llamadas que usa el ejemplo de referencia del patrón preferido. |
| 5 | **b** | `panel(session, **kwargs) -> CocoChatResult`. |
| 6 | **b** | `output_label=None` oculta el contenedor de salida con borde; la etiqueta por defecto en otro caso es `"CoCo output"`. |
| 7 | **a** | `output_mode` alterna entre el renderizado `"transcript"` (por defecto) y `"field"`. |
| 8 | **b** | `accept_file=True` (o `"multiple"`) activa el adjunto de archivos, que se guarda mediante los helpers de subida en el `cwd` de la sesión. |
| 9 | **a** | `example_questions` es un parámetro documentado de `copilot_rail()`; los otros tres no forman parte de su firma. |
| 10 | **b** | `job=` toma un diccionario (`prompt`, `label`, `status`, `expect_structured`) que encola un prompt para que el rail lo envíe. |
| 11 | **a** | `transcript_display_config()` renderiza el popover de configuración de visualización con controles Last-messages/First-n-characters. |
| 12 | **b** | `app_viewer(app_dir, ...)` requiere una carpeta con `streamlit_app.py` (o el override `script_name`); nunca debe apuntar al propio directorio de la app anfitriona. |
| 13 | **b** | La acción Fix llama a `on_fix` con un prompt de `default_fix_prompt(traceback, app_dir)`, normalmente encolando un trabajo de CoCo. |
| 14 | **b** | La limitación documentada es una vista previa por `app_dir`. |
| 15 | **b** | `approval_timeout_seconds` (por defecto `600.0`, es decir 10 minutos) rige la espera HITL antes de `ApprovalTimeoutError`. |
| 16 | **c** | `CocoOptions.permission_mode` tiene por defecto `"default"`; `"plan"` se usa explícitamente para flujos ExitPlanMode. |
| 17 | **b** | `check_environment()` es la sonda que nunca lanza excepción; `require_environment()` lanza errores tipados en su lugar. |
| 18 | **b** | Cuando existe exactamente un `*.toml` bajo `~/.snowflake/`, se usa sin importar su nombre de archivo. |
| 19 | **b** | Con varios archivos, `connections.toml` gana primero, luego `config.toml`, luego orden alfabético. |
| 20 | **a** | `structured_output.py` muestra `output_schema` + `on_structured_output` dirigiendo JSON hacia un widget en lugar de texto de chat. |
| 21 | **b** | `headless_pipeline.py` es Python asíncrono puro usando `query()`/`CocoSession`, sin import de Streamlit. |
| 22 | **c** | `approval_gate.py` demuestra el componente CCv2 heredado `chat()` todo-en-uno. |
| 23 | **a** | `backlog_desk` es el primer ejemplo basado en rail, sin SQL, respaldado por archivos JSON locales. |
| 24 | **c** | Su Copilot se abre desde un botón "Copilot" de la cabecera o un enlace de acción y se cierra con "Close" — no es una página de navegación. |
| 25 | **b** | `bi_to_semantic` lee workbooks Tableau `.twb`/`.twbx` y/o Power BI `.pbix`/`.pbit`. |
| 26 | **a** | Los helpers de subida escriben en `<CocoOptions.cwd>/_uploads/` por defecto (nombre de subdirectorio configurable). |
| 27 | **b** | El paso Build escribe `brief.json`, `BRIEF.md`, `sketches/*`, y `streamlit_app.py` en `out/<slug>/`. |
| 28 | **b** | El SBOM (CycloneDX) se adjunta como asset del GitHub Release y se produce solo en CI, al lanzar un tag. |
| 29 | **b** | `render_approvals()` ordena sus controles Approve once, Always allow, Deny. |
| 30 | **A, B** | `AskUserQuestion` y `ExitPlanMode` siempre crean una solicitud nueva y nunca muestran "Always allow"; la herramienta SQL y Edit/Write/Grep sí pueden marcarse como always-allowed. |
