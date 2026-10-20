# Configuración

Cada superficie de configuración que expone streamlit-coco: los campos de
`CocoOptions`, las variables de entorno, y el archivo de conexiones de
Snowflake que lee.

## Campos de `CocoOptions`

`CocoOptions` (`streamlit_coco/options.py`) es un dataclass. Todos los
campos son definibles por palabra clave; no hay ningún archivo de
configuración para la librería en sí — una app construye una instancia de
`CocoOptions` en código.

| Nombre | Tipo | Por defecto | Efecto | Ejemplo |
|---|---|---|---|---|
| `connection` | `str \| None` | `None` | Nombre de la conexión del Snowflake CLI a usar. `None` usa la conexión por defecto del CLI. | `CocoOptions(connection="analytics")` |
| `cwd` | `str` | `"."` | Directorio de trabajo en el que operan las herramientas del agente (Read/Write/Bash/…). | `CocoOptions(cwd="./workspace")` |
| `model` | `str \| None` | `None` | Identificador de modelo pasado al SDK. Preferir `"auto"` cuando se define explícitamente. | `CocoOptions(model="auto")` |
| `allowed_tools` | `list[str]` | `[]` | Herramientas que pueden ejecutarse sin un prompt de aprobación cuando está en efecto la aprobación basada en listas. | `CocoOptions(allowed_tools=["Read", "Glob", "Grep"])` |
| `disallowed_tools` | `list[str]` | `[]` | Herramientas bloqueadas por completo, sin importar la aprobación. | `CocoOptions(disallowed_tools=["Bash"])` |
| `permission_mode` | `str` | `"default"` | Modo de permisos del SDK, por ejemplo `"plan"` para flujos `ExitPlanMode`. | `CocoOptions(permission_mode="plan")` |
| `profile` | `str \| None` | `None` | Nombre de perfil del SDK. | `CocoOptions(profile="ci")` |
| `cli_path` | `str \| None` | `None` | Anula la ruta al binario del CLI `cortex`. Mismo efecto que `CORTEX_CODE_CLI_PATH`; este campo tiene precedencia cuando ambos están definidos. | `CocoOptions(cli_path="/opt/cortex/bin/cortex")` |
| `mcp_servers` | `dict` | `{}` | Configuración de servidores MCP reenviada al SDK. | `CocoOptions(mcp_servers={"docs": {...}})` |
| `hooks` | `dict` | `{}` | Configuración de hooks del SDK. | `CocoOptions(hooks={})` |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Herramientas que se pausan a la espera de aprobación human-in-the-loop. `AskUserQuestion` y `ExitPlanMode` siempre solicitan sin importar esta lista. Un callable recibe `(tool_name, tool_input, context)` y devuelve `bool`. | `CocoOptions(require_approval_for=["Edit", "Write", "Bash"])` |
| `output_schema` | `dict \| None` | `None` | JSON Schema reenviado al SDK como `output_format`. La librería elimina `$schema` / `$id` antes de reenviarlo (ver [help.html#schema-dollar-schema-rejected](../help.html#schema-dollar-schema-rejected)). | `CocoOptions(output_schema={"type": "object", "properties": {...}})` |
| `max_turns` | `int \| None` | `None` | Limita el número de turnos del agente en una ejecución. | `CocoOptions(max_turns=10)` |
| `approval_timeout_seconds` | `float` | `600.0` | Segundos a esperar por una decisión human-in-the-loop antes de lanzar `ApprovalTimeoutError`. | `CocoOptions(approval_timeout_seconds=120.0)` |
| `extra_sdk_options` | `dict` | `{}` | Kwargs de passthrough fusionados en las opciones del SDK, por ejemplo `add_dirs` para montar directorios adicionales (usado por los paquetes de skill `types/` de App Builder). | `CocoOptions(extra_sdk_options={"add_dirs": ["/path/to/types/shared"]})` |

Dos métodos que vale la pena conocer al configurar una sesión:

- `options_hash()` — un hash estable sobre los campos que afectan a los
  permisos de herramienta. `CocoSession` reinicia su worker en segundo
  plano solo cuando este hash cambia entre llamadas (ver
  [architecture](architecture.html)).
- `to_sdk_options(*, can_use_tool=None)` — construye el
  `CortexCodeAgentOptions` del SDK; lanza `SDKNotInstalledError` si
  `cortex-code-agent-sdk` no está instalado.

## Variables de entorno

| Nombre | Tipo | Por defecto | Efecto | Ejemplo |
|---|---|---|---|---|
| `CORTEX_CODE_CLI_PATH` | cadena de ruta | sin definir (recurre a la búsqueda en `PATH`) | Anula la ruta del CLI `cortex` usada por los diagnósticos y la resolución de opciones cuando no está en `PATH` y `CocoOptions.cli_path` no está definido. | `export CORTEX_CODE_CLI_PATH=/opt/cortex/bin/cortex` |
| `STREAMLIT_COCO_DEBUG` | `"1"` / `"true"` / `"yes"` / `"on"` (sin distinguir mayúsculas) | sin definir / false | Muestra los payloads en bruto de solicitud/respuesta de las herramientas en la transcripción ("Raw tool payload"). Mismo efecto que `COCO_DEBUG`; que cualquiera de los dos sea verdadero activa el modo debug. | `export STREAMLIT_COCO_DEBUG=1` |
| `COCO_DEBUG` | mismo conjunto de valores verdaderos que arriba | sin definir / false | Alias de `STREAMLIT_COCO_DEBUG`. `is_debug_mode()` también comprueba `st.session_state["coco_debug"]` cuando no hay ninguna variable de entorno definida. | `export COCO_DEBUG=1` |
| `TTS_DATA_MODE` | cadena | `"disconnected"` cuando lo define el ejemplo | Solo lo lee la app consumidora generada por `examples/bi_to_semantic` (pasada a través de `app_viewer(env=...)`), no la librería en sí. Selecciona el modo de datos desconectado frente a conectado para esa app generada. | `app_viewer(app_dir, env={"TTS_DATA_MODE": "disconnected"})` |

`is_debug_mode(*, session_state=None)` (re-exportado en
`streamlit_coco/tool_names.py`, definido en `streamlit_coco/debug.py`)
es la única fuente de verdad sobre si se muestra la interfaz de debug;
comprueba primero las dos variables de entorno, luego
`st.session_state["coco_debug"]`.

## Archivo de conexión de Snowflake

CoCo se autentica a través del propio archivo de conexión del Snowflake
CLI, nunca mediante configuración de la librería:

- Ubicación por defecto: `~/.snowflake/connections.toml`.
- El `~/.snowflake/config.toml` heredado también se detecta (sus
  perfiles viven bajo una tabla `[connections]` de nivel superior en
  lugar de entradas `[connections.<name>]` en la raíz).
- Resolución de `toml_file` (usada por `check_environment`, el selector
  Config file de `copilot_rail`, y `list_snowflake_connections`):
  - un nombre de archivo simple se resuelve bajo `~/.snowflake/`; una
    ruta se usa tal cual.
  - si se omite: cuando existe exactamente un archivo `*.toml` bajo
    `~/.snowflake/`, se usa ese archivo sin importar su nombre; con
    varios archivos presentes, `connections.toml` gana, luego
    `config.toml`, luego el resto de archivos alfabéticamente.

Ejemplo de entrada de conexión:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema según se necesiten — ver security.html
```

Helpers relacionados: `list_snowflake_toml_files()`,
`list_snowflake_connections(toml_file=None)`,
`resolve_snowflake_config_path(toml_file=None, *, must_exist=True)`,
`default_snowflake_connection_name(toml_file=None)`. Todos viven en
`streamlit_coco/diagnostics.py` y son ejercitados por
`check_environment()` / `require_environment()` — ver
[install](install.html) para el flujo de verificación y
[help.html#snowflake-config-not-found](../help.html#snowflake-config-not-found)
cuando falla la sonda.
