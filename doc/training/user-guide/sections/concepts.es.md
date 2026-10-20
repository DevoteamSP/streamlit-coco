# Conceptos

Los objetos con los que un usuario de `streamlit-coco` trabaja directamente,
qué representan, sus estados, y dónde vive cada uno en el código.

## `CocoOptions`

Configuración de una sesión de CoCo: conexión, directorio de trabajo,
modelo, herramientas permitidas/prohibidas, modo de permisos, reglas de
aprobación, esquema de salida, límite de turnos, y passthrough del SDK. Es
un dataclass sencillo (`streamlit_coco/options.py`) — creas uno, lo pasas a
`get_or_create_session` o a `query()`, y lo mutas (una instancia nueva, no
en el sitio) cuando cambia la configuración.

`CocoOptions` no tiene ciclo de vida propio: es un objeto de valor. Su
`options_hash()` es lo que una sesión compara para decidir si debe
reiniciar su worker en segundo plano — cambiar `permission_mode` o
`allowed_tools` entre reruns y llamar a `sync_options()` dispara un
reinicio si el hash difiere.

Se usa en cada página de tareas de esta guía; la tabla completa de campos
está en la [Referencia de la API](reference-api.html).

## `CocoSession`

Una conversación de varios turnos con el agente, respaldada por un
`CortexCodeSDKClient` ejecutándose en un hilo en segundo plano
(`streamlit_coco/session.py`). Una sesión sobrevive a los reruns de
Streamlit cuando se almacena en `st.session_state` mediante
`get_or_create_session()`.

Ciclo de vida: creada inactiva (idle) → `start()` conecta el worker en
segundo plano → `send()`/`run()`/`stream()` impulsan los turnos →
`reset()` limpia la transcripción y reinicia el worker → `close()` derriba
el worker. Una sesión se busca por su `key` mediante `get_session(key)`, y
se derriba explícitamente con `stop_session()`.

## `CocoRunStatus`

El estado en el que se encuentra una sesión (y la interfaz construida
sobre ella), como una enumeración de cadenas: `idle` → `connecting` →
`ready` → `running` → `awaiting_user` → `completed` / `error` /
`cancelled`. `awaiting_user` significa que una llamada a herramienta está
pausada en una aprobación pendiente; la interfaz muestra los controles de
aprobación y deja de sondear nueva salida del agente hasta que se
resuelve. `panel()` y los demás helpers de visualización leen este estado
para decidir qué chrome mostrar (esqueleto de estado, botón Stop, estado
de campo de entrada deshabilitado).

## `CocoEvent`

Una unidad normalizada y serializable a JSON de la actividad del agente
(`streamlit_coco/messages.py`), con `to_dict()`/`from_dict()` para
almacenamiento o transporte. Valores comunes de `type`: `assistant_text`,
`stream_event`, `thinking`, `tool_use`, `tool_result`,
`permission_request`, `result`, `system`, `error`. Una sesión acumula
eventos en `session.events`; la interfaz de transcripción y
`events_to_dataframe()` consumen ambos el mismo flujo de eventos. Los
eventos no tienen ciclo de vida más allá de ser añadidos — cada uno es un
hecho sobre algo que ya ocurrió.

## `CocoChatResult`

El valor de retorno de `panel()` y `chat()` (CCv2 heredado): una
instantánea del resultado de un turno — `last_prompt`, `last_result`,
`pending_approval`, `structured_output`, `events`, y `status`. Se
recalcula en cada rerun vía `session.chat_result()`; nada se muta
directamente sobre él.

## `CocoEnvironment`

El resultado de `check_environment()`: si el SDK está instalado, la ruta y
versión del CLI, y si se encontró una configuración de Snowflake, más los
campos necesarios para renderizar ese estado (`connection_hint`,
`toml_file`, `snowflake_config_display`). `check_environment()` nunca
lanza una excepción — siempre devuelve un `CocoEnvironment`, así que quien
llama puede renderizar una pantalla de diagnóstico en cualquier caso.
`require_environment()` realiza la misma sonda pero lanza un error tipado
(ver [Referencia de la API](reference-api.html)) en lugar de devolver un
resultado no listo, para rutas de código que deben detenerse por completo.

## El modelo de aprobación / permisos

Cada llamada a herramienta que el agente quiere hacer está o bien
auto-permitida (en `CocoOptions.allowed_tools`, o coincidente con
`permission_mode`), o bien pausada a la espera de una decisión humana,
según `require_approval_for` (una lista de nombres de herramienta, o un
callable). `AskUserQuestion` y `ExitPlanMode` siempre se pausan sin
importar esa configuración. Una llamada pausada se convierte en una
aprobación pendiente en la sesión; se resuelve con uno de tres resultados
— **Approve once**, **Always allow**, o **Deny** — ya sea mediante la
interfaz `render_approvals()` dentro de `panel()`, o de forma
programática con `approve_pending()` / `deny_pending()`. "Always allow"
tiene alcance solo de la sesión actual: se borra en `reset()` o al
reiniciar el proceso, nunca se escribe en una política persistida. Ver
[Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html).

## La transcripción

La secuencia ordenada de turnos y eventos que una sesión ha producido, tal
como la renderiza `render_transcript()` (usado dentro de `panel()` en
`output_mode="transcript"`) o leída de vuelta vía `session.transcript` /
`session.messages`. Los parámetros de solo visualización (`max_messages`,
`preview_chars`, `text_renderer`) controlan cuánto se muestra y cómo, sin
cambiar lo que se almacena — "Load earlier" revela más de la misma
transcripción subyacente, no obtiene nada nuevo.

## Glosario

| Término | Definición |
|------|------------|
| `CocoOptions` | Objeto de valor de configuración para una sesión o una llamada a `query()` |
| `CocoSession` | Una conversación de varios turnos, respaldada por un hilo worker del SDK en segundo plano |
| `CocoRunStatus` | El estado actual de la sesión (`idle` … `completed`/`error`/`cancelled`) |
| `CocoEvent` | Una unidad normalizada de actividad del agente (texto del asistente, uso de herramienta, resultado, …) |
| `CocoChatResult` | Instantánea del resultado de un turno, devuelta por `panel()`/`chat()` |
| `CocoEnvironment` | Resultado de una sonda de entorno (disposición del SDK/CLI/configuración de Snowflake) |
| Puerta de aprobación | El flujo de pausa y resolución para una llamada a herramienta coincidente con `require_approval_for` |
| "Always allow" | Una aprobación con alcance de sesión (no persistida) que omite futuros prompts para esa herramienta |
| Transcripción | El historial ordenado de turnos/eventos de una sesión |
| `cwd` | El directorio de trabajo en el que operan las herramientas del agente (`CocoOptions.cwd`) |
| Headless | Ejecutar `query()` o `CocoSession` sin ninguna interfaz Streamlit |
