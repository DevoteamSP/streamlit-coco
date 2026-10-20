# Referencia de la API

La API pública de Python de `streamlit-coco`, tal como se exporta desde
`streamlit_coco` (ver el [índice](../index.html) para la versión exacta
que describe esta guía). Los módulos privados (`bridge`, `tool_cards`,
`tool_extract`, y otros no listados aquí) son detalles de implementación,
no API estable — no se documentan como entradas de referencia.

## `CocoOptions`

El dataclass de configuración para una sesión o una llamada a `query()`
(`streamlit_coco/options.py`).

| Campo | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `connection` | `str \| None` | `None` | Nombre de la conexión del Snowflake CLI a usar |
| `cwd` | `str` | `"."` | Directorio de trabajo en el que operan las herramientas del agente |
| `model` | `str \| None` | `None` | Selección de modelo; preferir `"auto"` cuando se define |
| `allowed_tools` | `list[str]` | `[]` | Herramientas que pueden ejecutarse sin aprobación |
| `disallowed_tools` | `list[str]` | `[]` | Herramientas bloqueadas por completo |
| `permission_mode` | `str` | `"default"` | Modo de permisos general, por ejemplo `"plan"` para flujos `ExitPlanMode` |
| `profile` | `str \| None` | `None` | Nombre de perfil del SDK |
| `cli_path` | `str \| None` | `None` | Anula la ruta del CLI `cortex` (`CORTEX_CODE_CLI_PATH` también funciona) |
| `mcp_servers` | `dict` | `{}` | Configuración de servidores MCP reenviada al SDK |
| `hooks` | `dict` | `{}` | Passthrough de hooks del SDK |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Herramientas que se pausan a la espera de aprobación humana; `AskUserQuestion`/`ExitPlanMode` siempre se pausan |
| `output_schema` | `dict \| None` | `None` | JSON Schema reenviado al SDK como `output_format` (`$schema`/`$id` eliminados antes del reenvío) |
| `max_turns` | `int \| None` | `None` | Limita el número de turnos del agente |
| `approval_timeout_seconds` | `float` | `600.0` | Segundos a esperar por una aprobación pendiente antes de `ApprovalTimeoutError` |
| `extra_sdk_options` | `dict` | `{}` | Kwargs de passthrough reenviados al propio objeto de opciones del SDK |

### Métodos

- `options_hash() -> str` — un hash estable de las opciones que cambia
  solo cuando cambia un valor que afecta a la sesión en ejecución (usado
  para decidir si el worker en segundo plano debe reiniciarse).
- `to_sdk_options(*, can_use_tool=None)` — construye el objeto de opciones
  nativo del SDK; lanza `SDKNotInstalledError` si el SDK no está
  instalado.
- `auto_allow_tools() -> list[str]` — el conjunto efectivo de herramientas
  que se ejecutan sin aprobación.
- `tools_requiring_approval() -> list[str]` — el conjunto efectivo de
  herramientas que se pausan a la espera de aprobación.

```python
options = st_coco.CocoOptions(
    connection="my_connection",
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
    approval_timeout_seconds=300.0,
)
```

Usado por: [Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)

## `CocoRunStatus`

Una enumeración `str` (`streamlit_coco/session.py`) que da el estado
actual de una sesión.

| Valor | Significado |
|---|---|
| `idle` | Ninguna actividad de sesión iniciada aún |
| `connecting` | El worker en segundo plano está arrancando |
| `ready` | Conectado, a la espera de un prompt |
| `running` | Un turno está en curso |
| `awaiting_user` | Una llamada a herramienta está pausada a la espera de aprobación |
| `completed` | El turno terminó con normalidad |
| `error` | El turno o la sesión fallaron |
| `cancelled` | El turno se canceló |

```python
if session.chat_result().status == st_coco.CocoRunStatus.awaiting_user:
    st.warning("Waiting on an approval.")
```

Usado por: [Conceptos](concepts.html#cocorunstatus)

## `CocoChatResult`

Una instantánea en dataclass del resultado de un turno, devuelta por
`panel()`, `chat()` y `session.chat_result()`.

| Campo | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `last_prompt` | `str \| None` | — | El prompt más reciente enviado |
| `last_result` | `CocoEvent \| None` | — | El evento terminal más reciente |
| `pending_approval` | `dict \| None` | — | La solicitud de aprobación pendiente, si existe |
| `structured_output` | `Any` | — | El último payload estructurado, si se definió `output_schema` |
| `events` | `list[CocoEvent]` | — | Todos los eventos de la sesión hasta ahora |
| `status` | `CocoRunStatus` | — | El estado de ejecución actual |

```python
result = session.chat_result()
if result.pending_approval:
    st.info(f"Waiting on: {result.pending_approval['tool_name']}")
```

Usado por: [Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html)

## `CocoSession`

Una sesión de varios turnos respaldada por un `CortexCodeSDKClient` en un
hilo en segundo plano (`streamlit_coco/session.py`).

| Miembro | Efecto |
|---|---|
| `send(prompt)` | Encola un prompt; lanza `SessionStartError`/`SessionNotReadyError` si no está listo |
| `start()` | Inicia el worker en segundo plano |
| `ensure_ready(timeout=120)` | Espera a la disponibilidad; lanza `SessionNotReadyError` en timeout o fallo de arranque |
| `run(prompt, *, timeout=None)` | Envía un prompt y espera su resultado |
| `stream()` | Itera de forma asíncrona los eventos del turno actual/siguiente |
| `set_permission_mode(mode)` | Cambia el modo de permisos |
| `execute_plan(...)` | Ejecuta un plan producido bajo `permission_mode="plan"` |
| `cancel()` | Cancela el turno en curso |
| `close()` | Derriba el worker en segundo plano |
| `reset()` | Limpia la transcripción y reinicia el worker |
| `chat_result()` | Devuelve el `CocoChatResult` actual |
| `is_running` / `is_ready` / `is_connecting` / `needs_polling` | Propiedades booleanas de estado |
| `transcript` / `messages` / `events` | El historial acumulado de turnos/eventos |
| `last_error` / `init_info` / `structured_output` | Diagnósticos y el último payload estructurado |
| `permission_manager` | El gestor del estado de aprobación de la sesión |
| `add_event_listener(cb)` | Registra un callback invocado por cada evento nuevo |
| `sync_options(options)` | Aplica nuevas `CocoOptions`; reinicia el worker si `options_hash()` cambió |
| `set_show_structured_inline(bool)` | Activa/desactiva el renderizado en línea de la salida estructurada |

```python
session = st_coco.CocoSession(options=options, key="copilot")
session.start()
result = await session.run("List the tables in my schema.")
```

Usado por: [Quiero ejecutar CoCo en modo headless](task-run-headless.html)

### Helpers del registro de sesiones

| Función | Efecto |
|---|---|
| `get_session(key) -> CocoSession \| None` | Busca una sesión existente por clave en el registro del proceso |
| `get_or_create_session(options, *, key="coco", sync_options=True) -> CocoSession` | Helper de Streamlit: obtiene o crea una sesión en `st.session_state[key]` |
| `reset_session(options, session_key="coco", warm_up=False) -> CocoSession` | Reinicia (o crea) la sesión en `session_key` |
| `stop_session(session_key="coco", gate_key="coco_started") -> None` | Derriba la sesión y limpia el flag de la puerta de inicio |

```python
session = st_coco.get_or_create_session(options, key="coco")
```

Usado por: [Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)

## Interfaz — patrón preferido

### `panel(session, **kwargs) -> CocoChatResult`

Renderiza la salida nativa de transcripción o campo, los controles de
aprobación, y un botón Stop para una sesión.

| Parámetro | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `output_mode` | `str` | `"transcript"` | `"transcript"` o `"field"` |
| `output_label` | `str \| None` | `"CoCo output"` | `None` oculta el contenedor de salida con borde |
| `show_tool_details` | `bool` | `True` | Muestra el detalle de la tarjeta de herramienta |
| `show_thinking` | `bool` | `False` | Muestra los bloques de thinking |
| `show_approvals` | `bool` | `True` | Renderiza los controles de aprobación |
| `show_stop` | `bool` | `True` | Muestra el botón Stop mientras se sondea |
| `show_status` | `bool` | `True` | Muestra el chrome de estado de conexión/turno |
| `show_plan_banner` | `bool` | `True` | Muestra el banner de modo plan y la llamada a la acción Execute plan |
| `warm_up` | `bool` | `False` | Llama a `session.start()` al montar cuando está inactiva |
| `status_expanded` | `str` | `"auto"` | `"auto"` / `"always"` / `"never"` |
| `approval_key_prefix` | `str` | `"coco"` | Espacio de nombres de la clave del widget |
| `use_fragment` | `bool` | `True` | Sondea dentro de un `@st.fragment` |
| `run_every` | `float` | `0.25` | Intervalo de sondeo en segundos; pausado mientras hay una aprobación pendiente |
| `text_renderer` | `str \| Callable \| None` | `None` | `"markdown"` (por defecto) / `"write"` / `"text"` / `"caption"` / `"code"` o un callable |
| `show_copy` | `bool` | `True` | Muestra los controles de portapapeles |
| `max_messages` | `int \| None` | `None` | Ventana de la transcripción; **Load earlier** revela elementos más antiguos |
| `preview_chars` | `int \| None` | `None` | Limita el texto de usuario/asistente a los primeros N caracteres |
| `on_structured_output` | `Callable[[dict, CocoChatResult], None] \| None` | `None` | Se llama cuando llega un payload estructurado |
| `structured_output_container` | contenedor \| `None` | `None` | Contenedor donde renderizar la salida estructurada |

```python
st_coco.panel(session, output_mode="transcript", show_thinking=False)
```

Usado por: [Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)

### `copilot_rail(session, *, title="Copilot", …) -> None`

Un Copilot en rail lateral derecho alrededor de `panel()`, para apps
multipágina.

| Parámetro | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `session` | `CocoSession` | — | La sesión a renderizar |
| `connected` | `bool` | `True` | Si el rail se muestra como conectado |
| `connections` | `list \| None` | `None` | Opciones de conexión, si se ofrece cambiar |
| `toml_file` | `str \| None` | `None` | Archivo de configuración de Snowflake del que leer conexiones |
| `on_connect` / `on_disconnect` | `Callable \| None` | `None` | Callbacks de ciclo de vida de la conexión |
| `job` | `dict \| None` | `None` | Un trabajo encolado: `{prompt, label, status, expect_structured}` |
| `on_job_sent` / `on_job_finished` | `Callable \| None` | `None` | Callbacks de ciclo de vida del trabajo |
| `show_copy` | `bool` | `False` | Muestra los controles de portapapeles |
| `show_transcript_filters` | `bool` | `True` | Muestra el popover de configuración de visualización de la transcripción |
| `example_questions` | `list \| None` | `None` | Diccionarios `{title, question}` o tuplas `(title, question)` |
| `deferred` | `bool` | `False` | Difiere el renderizado (también configurable por pregunta de ejemplo) |

```python
st_coco.copilot_rail(session, title="Copilot", example_questions=[
    ("Summarize", "Summarize this sprint."),
])
```

Usado por: [Referencia de apps de ejemplo](reference-examples.html)

### `transcript_display_config` / `transcript_view_pills`

`transcript_display_config(*, key=…, last_n=8, preview_chars=200) ->
tuple[int | None, int | None]` — el popover de icono de configuración de
visualización (`:material/display_settings:`) con píldoras y sliders de
Last messages / First n characters.

`transcript_view_pills(*, key=…, last_n=8, preview_chars=200)` — las
mismas píldoras como widget independiente, sin el chrome del popover.

```python
last_n, preview_chars = st_coco.transcript_display_config(key="rail")
```

Usado por: [Conceptos](concepts.html#the-transcript)

### `app_viewer(app_dir, *, key="coco_app_viewer", …) -> None`

Incrusta una vista previa en vivo de una app que el agente acaba de
escribir.

| Parámetro | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `app_dir` | `str` | — (obligatorio) | Carpeta que contiene `streamlit_app.py` |
| `key` | `str` | `"coco_app_viewer"` | Espacio de nombres de la clave del widget |
| `port` | `int \| None` | `None` | El primer puerto libre del rango 8511–8520 si no se define |
| `address` | `str` | `"127.0.0.1"` | Dirección de bind para el proceso de vista previa |
| `env` | `dict \| None` | `None` | Variables de entorno adicionales para el proceso hijo |
| `iframe_height` | `int` | `520` | Altura del iframe de vista previa en píxeles |
| `show_fix` | `bool` | `True` | Muestra la acción "Fix with CoCo" |
| `on_fix` | `Callable[[str], None] \| None` | `None` | Callback que recibe el prompt de corrección |
| `on_close` | `Callable \| None` | `None` | Callback cuando se cierra la vista previa |
| `title_extra` | `str \| None` | `None` | Texto extra añadido al título |
| `title` | `str` | `"Preview"` | Título del panel |
| `script_name` | `str` | `"streamlit_app.py"` | Nombre de archivo del punto de entrada dentro de `app_dir` |

Funciones helper sin Streamlit: `start_app_preview`, `stop_app_preview`,
`preview_running`, `preview_url`, `last_preview_exception`,
`preview_log_tail`, `default_fix_prompt(traceback, app_dir) -> str`.

```python
st_coco.app_viewer("examples/app_builder/out/my-app", title="Preview")
```

Usado por: [Quiero ejecutar las apps de ejemplo](task-run-the-example-apps.html)

### `chat_input_bar(session, *, placeholder=…, connecting_placeholder=…, key=None, accept_file=False, …) -> str | None`

La barra de entrada del chat, con adjunto de archivo opcional.

| Parámetro | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `accept_file` | `bool \| str` | `False` | `True` o `"multiple"` para aceptar subidas |
| `file_type` | `list[str] \| None` | `None` | Restringe las extensiones aceptadas |
| `max_upload_size` | `int \| None` | `None` | Anula el tamaño máximo de subida por defecto |
| `upload_subdir` | `str` | `"_uploads"` | Subdirectorio de `cwd` donde se escriben las subidas |
| `upload_overwrite` | `str` | `"replace"` | `"error"` / `"replace"` / `"skip"` |
| `inject_upload_paths` | `bool` | `True` | Añade las rutas de los archivos subidos al texto del prompt |

```python
prompt = st_coco.chat_input_bar(session, accept_file=True, upload_overwrite="replace")
```

Usado por: [Quiero añadir subida de archivos](task-add-file-uploads.html)

## Helpers de subida

### `upload_to_cwd(target, files, *, subdir="_uploads", overwrite="error", max_bytes=DEFAULT_MAX_BYTES, allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS) -> list[UploadedPath]`

Escribe archivos subidos en el directorio de trabajo de una sesión, unas
opciones, o una ruta. `target` puede ser una ruta, un `CocoOptions`, o un
`CocoSession`. Lanza `CwdUploadError` ante un nombre de archivo incorrecto
(protección contra path-traversal), una extensión no permitida, un
payload de tamaño excesivo, o un conflicto de sobrescritura.

```python
paths = st_coco.upload_to_cwd(session, files, overwrite="error")
```

Usado por: [Quiero añadir subida de archivos](task-add-file-uploads.html)

### `cwd_uploader(target, *, label=…, overwrite="error", …) -> list[UploadedPath]`

Un `st.file_uploader` de barra lateral/chrome conectado a
`upload_to_cwd()`, con una leyenda de inventario de los archivos ya
subidos.

```python
uploaded = st_coco.cwd_uploader(session, label="Upload a reference file")
```

Usado por: [Quiero añadir subida de archivos](task-add-file-uploads.html)

### Constantes de subida (`streamlit_coco/upload.py`)

| Nombre | Tipo | Por defecto | Efecto |
|---|---|---|---|
| `DEFAULT_UPLOAD_SUBDIR` | `str` | `"_uploads"` | Nombre del subdirectorio de subida por defecto |
| `DEFAULT_MAX_BYTES` | `int` | `10 * 1024 * 1024` (10 MiB) | Límite de tamaño por archivo por defecto |
| `DEFAULT_ALLOWED_EXTENSIONS` | `frozenset[str]` | una lista fija de permitidas | Extensiones de archivo permitidas por defecto; leer la constante del código fuente para la lista exacta en lugar de asumir una |

Usado por: [Quiero añadir subida de archivos](task-add-file-uploads.html)

## Aprobaciones y prompting

### `send_prompt(session, prompt) -> None`

Recorta y encola un prompt en una sesión; expone cualquier `CocoError`
vía `st.error` en lugar de lanzarla hacia la página.

```python
st_coco.send_prompt(session, "Summarize this sprint.")
```

Usado por: [Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)

### `render_approvals(session, *, key_prefix="coco") -> bool`

Renderiza la interfaz de aprobación HITL para una solicitud pendiente.
Orden de botones: **Approve once** · **Always allow** · **Deny**. Las
solicitudes de `AskUserQuestion` y `ExitPlanMode` nunca muestran **Always
allow**.

```python
st_coco.render_approvals(session, key_prefix="coco")
```

Usado por: [Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html)

### `render_plan_banner(session, …) -> bool`

Renderiza el banner de modo plan con una llamada a la acción **Execute
plan**.

```python
st_coco.render_plan_banner(session)
```

Usado por: [Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html)

### `approve_pending(session, request_id, *, always=False, updated_input=None)` / `deny_pending(session, request_id, *, reason=None)`

Resolvers de bajo nivel para una aprobación pendiente, para interfaces de
aprobación personalizadas.

```python
st_coco.approve_pending(session, request_id, always=False)
st_coco.deny_pending(session, request_id, reason="not now")
```

Usado por: [Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html)

## Helpers de visualización

| Función | Efecto |
|---|---|
| `render_transcript(session, …, text_renderer=None)` | Renderiza la transcripción de forma independiente (lo que `panel()` usa internamente) |
| `render_output_field(session, …, text_renderer=None)` | Renderiza solo el último campo de salida |
| `render_session_status(session, …)` | Renderiza el chrome de estado/conexión de forma independiente |
| `get_latest_assistant_text(session) -> str` | Devuelve el último texto del asistente como una cadena plana |

```python
latest = st_coco.get_latest_assistant_text(session)
```

Usado por: [Conceptos](concepts.html#the-transcript)

## Bootstrap y puerta de inicio

### `render_environment_status(env=None, *, connection=None, toml_file=None, stacked=False, show_title=True)`

Renderiza el bloque de estado SDK/CLI/configuración de Snowflake, dado un
`CocoEnvironment` (o sondeando uno propio si `env` se omite).

```python
st_coco.render_environment_status(connection="my_connection")
```

Usado por: [Primeros pasos](getting-started.html)

### `render_start_gate(options, *, session_key=…, gate_key=…, warm_up=True, env=None) -> bool`

Renderiza la pantalla de aterrizaje (estado del entorno más una acción
**Start**) y devuelve `False` mientras el entorno no esté listo o el
usuario no haya confirmado. Quien llama debe llamar a `st.stop()` en
`False` — la puerta no detiene el script por sí misma.

```python
if not st_coco.render_start_gate(options):
    st.stop()
```

Usado por: [Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)

## CCv2 heredado

### `chat(**kwargs) -> CocoChatResult`

Un widget todo-en-uno de Custom Component v2 con entrada incorporada,
anterior a `panel()`. Preferir `panel()` para apps nuevas. Parámetros
destacados: `session` / `options`, `key`, `height`, `placeholder`,
`use_fragment`, `run_every`, `output_mode`, `on_structured_output`, y
callbacks opcionales `on_event` / de envío / aprobación / cancelación.

```python
result = st_coco.chat(options=options, key="legacy")
```

Usado por: [Quiero ejecutar las apps de ejemplo](task-run-the-example-apps.html)

### `request_input(question, *, key="coco_input", default="", schema=None, …) -> str | dict | None`

Un formulario de aclaración propio de la app, mostrado entre turnos — no
es un canal CCv2. Devuelve un `dict` cuando se da `schema=`, en otro caso
un `str` (o `None` si no se responde).

```python
answer = st_coco.request_input("Which environment?", schema={"type": "string"})
```

Usado por: [Referencia de apps de ejemplo](reference-examples.html)

## Headless

### `async query(prompt, *, options=None, output_schema=None) -> AsyncIterator[CocoEvent]`

Un envoltorio de un solo turno que se ejecuta sin ningún objeto de sesión
ni import de Streamlit. Lanza `SDKNotInstalledError`, `QueryError`, u otra
subclase de `CocoError` en caso de fallo.

```python
async for event in st_coco.query("List the tables in my schema.", options=options):
    ...
```

Usado por: [Quiero ejecutar CoCo en modo headless](task-run-headless.html)

### `events_to_dataframe(events) -> DataFrame`

Aplana una lista de `CocoEvent` en un `DataFrame` de pandas (requiere
pandas instalado).

```python
df = st_coco.events_to_dataframe(session.events)
```

Usado por: [Quiero ejecutar CoCo en modo headless](task-run-headless.html)

## `CocoEvent`

Una unidad normalizada y serializable a JSON de la actividad del agente
(`streamlit_coco/messages.py`), con `to_dict()` / `from_dict()` para
almacenamiento o transporte.

| Campo | Efecto |
|---|---|
| `type` | Uno de `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error` |
| `text` / `delta` | Contenido de texto o delta transmitido |
| `name` / `tool_use_id` / `tool_name` / `tool_input` / `input` | Identificación de la llamada a herramienta y sus argumentos |
| `content` / `is_error` | Contenido del resultado de la herramienta y flag de error |
| `request_id` | Identifica una solicitud de aprobación pendiente |
| `subtype` / `duration_ms` / `cost_usd` | Metadatos del resultado |
| `structured_output` | El payload estructurado, cuando está presente |
| `message` / `code` / `metadata` | Detalle de error/sistema |

```python
event = st_coco.CocoEvent.from_dict(raw)
event.to_dict()
```

Usado por: [Conceptos](concepts.html#cocoevent)

## Entorno y errores

### `check_environment(*, connection=None, cli_path=None, toml_file=None) -> CocoEnvironment`

Sondea el SDK, el CLI y la configuración de Snowflake. Nunca lanza una
excepción.

| Campo / propiedad | Efecto |
|---|---|
| `sdk_installed` / `sdk_version` | Si el SDK es importable, y su versión |
| `cli_path` / `cli_version` | La ruta del CLI resuelta y su versión reportada |
| `snowflake_config_file` / `connection_hint` / `toml_file` | Detalle de resolución de la configuración de Snowflake |
| `ready` | `True` cuando está presente todo lo necesario para iniciar una sesión |
| `cli_ok` | `True` cuando el CLI respondió correctamente a la sonda |
| `snowflake_config_found` / `snowflake_config_display` / `snowflake_config_missing_label` | Presencia y texto de visualización de la configuración de Snowflake |

```python
env = st_coco.check_environment(connection="my_connection")
```

Usado por: [Primeros pasos](getting-started.html)

### `require_environment(*, connection=None, cli_path=None, toml_file=None, require_snowflake_config=False) -> CocoEnvironment`

Igual que `check_environment()`, pero lanza un error tipado en lugar de
devolver un resultado no listo.

```python
env = st_coco.require_environment(connection="my_connection", require_snowflake_config=True)
```

Usado por: [Primeros pasos](getting-started.html)

### Helpers de configuración de Snowflake

| Función | Efecto |
|---|---|
| `list_snowflake_toml_files() -> list[Path]` | Archivos `*.toml` bajo `~/.snowflake/`, `connections.toml`/`config.toml` primero |
| `list_snowflake_connections(toml_file=None) -> list[str]` | Nombres de perfil; el `config.toml` heredado lee `[connections]`, los demás archivos leen tablas de nivel superior |
| `resolve_snowflake_config_path(toml_file=None, *, must_exist=True)` | Resuelve un nombre de archivo simple o una ruta a un archivo de configuración bajo `~/.snowflake/` |
| `default_snowflake_connection_name(toml_file=None)` | El nombre de conexión usado cuando no se da ninguno |

```python
files = st_coco.list_snowflake_toml_files()
```

Usado por: [Primeros pasos](getting-started.html)

### Jerarquía de excepciones (`streamlit_coco/errors.py`)

| Clase | Se lanza cuando | Mensaje |
|---|---|---|
| `CocoError` | Clase base de todas las excepciones de abajo | — |
| `SDKNotInstalledError` (también `ImportError`) | El SDK no está instalado | `cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | El CLI `cortex` no está en `PATH` | `CoCo CLI not found on PATH... or set CORTEX_CODE_CLI_PATH.` (o `not found at {cli_path!r}`) |
| `CLIProbeError` | El binario del CLI existe pero no responde a `--version` | `CoCo CLI at {cli_path!r} did not respond to --version` |
| `SnowflakeConfigNotFoundError` | No se encontró ningún archivo de configuración de Snowflake | `No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml)...` |
| `CocoConnectionError` | Nombre de conexión incorrecto o fallo de autenticación | — |
| `SessionStartError` | El worker en segundo plano falló al arrancar | — |
| `SessionNotReadyError` | La sesión no está lista (timeout de conexión / fallo de arranque) | — |
| `ApprovalTimeoutError` (también `TimeoutError`) | Sin respuesta de aprobación dentro de `approval_timeout_seconds` | `Approval timed out for tool {tool_name}` |
| `QueryError` | Una llamada headless `query()` falló | — |
| `CwdUploadError` | Una subida falló (tamaño / extensión / ruta / sobrescritura) | — |

`wrap_exception()` mapea las excepciones en bruto del SDK/runtime a estas
mediante el mensaje y un kwarg `context=` (`"session_start"`,
`"session_ready"`/`"session"`, `"query"`, `"approval"`).

```python
try:
    env = st_coco.require_environment(connection="my_connection")
except st_coco.SDKNotInstalledError:
    st.error("Install the SDK: pip install streamlit-coco[sdk]")
```

Usado por: [Preguntas frecuentes](faq.html)

## Helpers de herramientas

| Función | Efecto |
|---|---|
| `tool_family(name)` | Mapea un nombre de herramienta a su enumeración de familia, para la visualización de la tarjeta de herramienta |
| `is_sql_tool(name)` | `True` para la herramienta SQL |
| `is_ask_user_question(name)` | `True` para `AskUserQuestion` |
| `is_exit_plan_mode(name)` | `True` para `ExitPlanMode` |
| `is_debug_mode(*, session_state=None)` | `True` cuando `STREAMLIT_COCO_DEBUG` o `COCO_DEBUG` es verdadero (`1`/`true`/`yes`/`on`, sin distinguir mayúsculas), o `st.session_state["coco_debug"]` es verdadero |

```python
if st_coco.is_debug_mode():
    st.caption("Debug mode is on.")
```

Usado por: [Preguntas frecuentes](faq.html)

## Metadatos del paquete

`st_coco.__version__` — la versión instalada del paquete, por ejemplo
`"0.1.9"`.

```python
import streamlit_coco as st_coco
print(st_coco.__version__)
```

Usado por: [Primeros pasos](getting-started.html)
