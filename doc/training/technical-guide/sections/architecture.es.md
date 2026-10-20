# Arquitectura

## Componentes

| Componente | Archivo | Rol |
|---|---|---|
| `CocoOptions` | `streamlit_coco/options.py` | Envoltorio de configuración tipado. Se convierte al `CortexCodeAgentOptions` del SDK vía `to_sdk_options()`; calcula `options_hash()` para que el worker en segundo plano se reinicie cuando cambian los permisos de herramienta. |
| `CocoSession` | `streamlit_coco/session.py` | Sesión de varios turnos. Posee un hilo en segundo plano (`threading.Thread`, nombre `coco-session`) que ejecuta un bucle asyncio envolviendo `CortexCodeSDKClient`. Expone `send`, `run`, `stream`, `cancel`, `reset`, `close`, `execute_plan`, `set_permission_mode`. |
| `PermissionManager` | `streamlit_coco/permissions.py` | Coordina los callbacks `can_use_tool` del SDK con las aprobaciones de la interfaz. Rastrea las solicitudes pendientes, el conjunto `always_allowed_tools` por sesión, y resuelve vía `approve_pending` / `deny_pending`. |
| `panel()` / `copilot_rail()` | `streamlit_coco/ui.py`, `streamlit_coco/rail.py` | Interfaz nativa de Streamlit. `panel()` es el primitivo de transcripción/campo/aprobaciones/Stop; `copilot_rail()` lo compone en un Copilot en rail lateral derecho (selector de conexión, trabajos encolados, configuración de visualización de la transcripción, preguntas de ejemplo). |
| `app_viewer()` | `streamlit_coco/viewer.py`, `streamlit_coco/app_preview.py` | Columna de vista previa para una app Streamlit generada por CoCo: lanza un proceso hijo `streamlit run`, lo incrusta en un iframe, y ofrece **Fix with CoCo** raspando `.preview.log`. |
| `bootstrap` | `streamlit_coco/bootstrap.py` | Puerta de inicio impulsada por `check_environment` (`render_start_gate`), `get_or_create_session`, `chat_input_bar`, `reset_session`, `stop_session`, `cwd_uploader`. |
| `diagnostics` | `streamlit_coco/diagnostics.py` | `check_environment()` / `require_environment()` — sondea la instalación del SDK, la accesibilidad del CLI, y la configuración de Snowflake sin iniciar un agente. |

Otros módulos son detalle de implementación (no API pública estable),
pero importan para trabajo de extensión: `tool_names.py` (despacho de
herramienta → `ToolFamily`), `tool_cards.py` / `tool_extract.py`
(renderizado por familia y extracción de diff/SQL), `text_renderer.py`
(renderizado de texto conectable), `messages.py` (normalización de
`CocoEvent` a partir de NDJSON del SDK), `upload.py` (subidas del
navegador a `cwd`), `ask_user.py` / `sql_tool.py` (helpers de interfaz por
herramienta).

## Mapa del repositorio

```text
streamlit_coco/          la librería (paquete importable)
  options.py              CocoOptions
  session.py              CocoSession, CocoChatResult, CocoRunStatus
  permissions.py          PermissionManager, approve_pending/deny_pending
  query.py                query() headless
  messages.py              CocoEvent, normalización NDJSON -> evento
  diagnostics.py          check_environment / require_environment
  bootstrap.py            puerta de inicio, chat_input_bar, helpers de sesión
  ui.py                   panel(), render_approvals(), render_plan_banner()
  rail.py                 copilot_rail(), transcript_display_config()
  viewer.py, app_preview.py   app_viewer() y sus helpers de proceso
  display.py              render_transcript, render_output_field, status
  upload.py               upload_to_cwd, cwd_uploader
  tool_names.py, tool_cards.py, tool_extract.py   despacho por familia de herramienta
  text_renderer.py        renderizado de texto conectable
  errors.py                jerarquía CocoError tipada
  component.py, frontend/  componente chat() CCv2 heredado
examples/                 apps de demo de primera parte (ver abajo)
tests/                    unidad + smoke; tests/e2e/ Playwright
doc/                      documentación de producto, seguridad, despliegue, testing
doc/training/             este pack de entrenamiento
.github/workflows/        ci.yml, security.yml, release.yml
Makefile                  objetivos install/test/lint/run/build/publish
```

## Flujo de datos

```text
App Streamlit
  -> streamlit-coco  (CocoOptions, CocoSession, panel()/copilot_rail())
  -> cortex-code-agent-sdk  (CortexCodeSDKClient, CortexCodeAgentOptions)
  -> CLI de CoCo ("cortex")  -- lanzado como subproceso local
  -> Snowflake Cortex  (LLM + herramientas, usando el rol de Snowflake conectado)
```

El hilo en segundo plano de la sesión impulsa el cliente del SDK y recibe
un flujo de eventos NDJSON de vuelta desde el subproceso del CLI a
través de un transporte local (sin salto de red en el objetivo de
despliegue local). `message_to_events()` / `_blocks_to_events()` en
`messages.py` normalizan cada mensaje del SDK (`AssistantMessage`,
`ResultMessage`, `StreamEvent`, bloques de uso/resultado de herramienta)
en registros `CocoEvent` que consumen tanto la interfaz como los
llamadores headless. Cuando una llamada a herramienta necesita
aprobación, el SDK invoca `can_use_tool` (construido por
`build_can_use_tool()` en `permissions.py`); esta llamada **bloquea el
hilo worker** en `PermissionManager.wait_for_decision()` hasta que la
interfaz la resuelve (o hasta que transcurre `approval_timeout_seconds`,
lanzando `ApprovalTimeoutError`) — ninguna otra herramienta se ejecuta en
ese turno hasta que se toma la decisión.

## Invariantes que no deben romperse

- **Los imports headless principales nunca cargan Streamlit.**
  `CocoSession`, `query`, `CocoOptions`, las funciones de permisos, y la
  jerarquía de errores se importan limpiamente sin ningún import de
  `streamlit` en la ruta — esto es lo que permite que
  `examples/headless_pipeline.py` se ejecute desde una terminal simple.
  Los exports de la interfaz (`panel`, `copilot_rail`, `chat_input_bar`,
  …) se resuelven de forma perezosa mediante
  `streamlit_coco.__getattr__` (`_LAZY_ATTRS` en
  `streamlit_coco/__init__.py`), no se importan de forma ansiosa en el
  momento de importar el paquete.
- **Las puertas de aprobación interceptan antes de la ejecución de la
  herramienta, no después.** `can_use_tool` es el hook previo a la
  ejecución del SDK; `PermissionManager` crea la solicitud pendiente y
  bloquea el worker ahí. Una herramienta que necesita aprobación nunca se
  ejecuta especulativamente para revertirse después — simplemente no se
  ejecuta hasta que se aprueba.
- **"Always allow" es por sesión, solo en memoria.** Vive en
  `PermissionManager.always_allowed_tools`, un `set` simple sobre el
  objeto de sesión. Nunca se escribe en disco y nunca sobrevive a
  `reset()`, `close()`, ni a un reinicio del proceso.
- **`AskUserQuestion` y `ExitPlanMode` nunca usan "Always allow".**
  `permissions.py` trata como caso especial a ambas familias de
  herramienta para crear siempre una solicitud de aprobación nueva,
  incluso si un "always allow" previo aplicaría en otro caso.
- **El worker se reinicia cuando cambian los permisos de herramienta, no
  en cada edición de opciones.** `CocoOptions.options_hash()` solo
  aplica hash a los campos que afectan a lo que una herramienta puede
  hacer (`allowed_tools`, `disallowed_tools`, `permission_mode`,
  `require_approval_for`, `add_dirs`, …); `CocoSession` compara este
  hash y reinicia el worker en segundo plano solo cuando cambia.
- **`app_viewer()` nunca importa `copilot_rail()`, y viceversa.** El
  componente de vista previa es agnóstico del anfitrión: no conoce las
  colas de trabajos. Una app anfitriona compone ambos y conecta `on_fix`
  ella misma.

## Pipeline detrás de los comandos de demo del Makefile

| Objetivo | Ejemplo | Primitivos conectados |
|---|---|---|
| `make chat` | `examples/chat_app.py` | `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`. El patrón preferido. |
| `make approval` | `examples/approval_gate.py` | CCv2 heredado `chat()` — componente todo-en-uno con su propia entrada incorporada. |
| `make structured` | `examples/structured_output.py` | `CocoOptions.output_schema` + `on_structured_output` dirigiendo el JSON del agente a un widget de la app en lugar de texto de chat. |
| `make headless` | `examples/headless_pipeline.py` | `query()` y `CocoSession` impulsados desde Python `async` simple — ningún import de Streamlit en ningún punto de la ejecución. |
| `make cwd-upload` | `examples/cwd_upload_chat.py` | `chat_input_bar(accept_file=...)` / `cwd_uploader()` → `upload_to_cwd()` en el `cwd` del agente. |
| `make backlog` | `examples/backlog_desk/` | App multipágina (Board / Epic / Ticket / Release) sobre JSON local, Copilot en rail lateral derecho abierto desde un botón de cabecera, sin herramienta SQL. |
| `make bi-semantic` (alias `make tableau-semantic`) | `examples/bi_to_semantic/` | Parseo determinista (Estate map, KPI inventory) → arbitraje `request_input(schema=...)` → escritura protegida por aprobación de una vista semántica + política de row access + consumidor generado, previsualizado vía `app_viewer()`. |
| `make app-builder` | `examples/app_builder/` | El catálogo de types (`types/<id>/type.json`) impulsa un brief; `add_dirs` monta el `SKILL.md` del type (+ `types/shared/SKILL.md`) para que CoCo escriba `streamlit_app.py` bajo aprobación; `copilot_rail()` + `app_viewer()` para Build/Preview. |

## Orquestación de las apps de ejemplo

Las tres apps de ejemplo que importan como superficies de producto
distintas:

- **`examples/chat_app.py`** — la implementación de referencia del
  patrón preferido (`panel()` + `chat_input_bar`). El ejecutor de
  prompts de prueba de la barra lateral lee
  `examples/testdata/prompts.json`.
- **`examples/backlog_desk/`** — primer ejemplo basado en rail, sin SQL.
  El Copilot no es una página de navegación; se abre desde un botón
  **Copilot** de la cabecera o un enlace de acción y se cierra con
  **Close**. Sus "skills" son plantillas de prompt (Summarize sprint,
  Draft release notes, Propose ticket update, Check definition of done),
  no archivos `.cortex/skills/`.
- **`examples/bi_to_semantic/`** y **`examples/app_builder/`** — los dos
  ejemplos que componen `copilot_rail()` con `app_viewer()`: una
  escritura de CoCo va seguida de una vista previa en vivo de la app
  Streamlit generada, con **Fix with CoCo** conectado a
  `default_fix_prompt()` y un trabajo encolado.

Ver [extending](extending.html) para cómo añadir una cuarta app de
ejemplo a esta lista, y [data-and-contracts](data-and-contracts.html)
para los contratos de archivo que cada una lee y escribe.
