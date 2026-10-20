# Operaciones

## Ejecutar

No hay ningún proceso de servidor independiente para la librería en sí —
se ejecuta dentro de cualquier app Streamlit que la incruste. Las apps de
ejemplo se ejecutan mediante objetivos del Makefile:

| Objetivo | Ejecuta |
|---|---|
| `make run` | `examples/chat_app.py` (`EXAMPLE` por defecto) |
| `make chat` | `examples/chat_app.py` |
| `make approval` | `examples/approval_gate.py` (CCv2 heredado) |
| `make structured` | `examples/structured_output.py` |
| `make headless` | `examples/headless_pipeline.py` (sin Streamlit) |
| `make backlog` | `examples/backlog_desk/` |
| `make cwd-upload` | `examples/cwd_upload_chat.py` |
| `make bi-semantic` (alias `make tableau-semantic`) | `examples/bi_to_semantic/` |
| `make app-builder` | `examples/app_builder/` |

O ejecuta cualquier ejemplo de Streamlit directamente:
`uv run streamlit run examples/chat_app.py`.

## Programar

No aplica. streamlit-coco no tiene planificador, ni ejecutor de trabajos
en segundo plano, ni componente basado en cron. Toda ejecución es
interactiva, iniciada al abrir una app Streamlit.

## Monitorizar

- La transcripción del agente existe solo en el estado de sesión de
  Streamlit, en memoria, durante la vida de la sesión del navegador. Nada
  se persiste por defecto.
- `app_viewer()` escribe `.preview.log`, `.preview.pid`, y
  `.preview.port` dentro del `app_dir` previsualizado mientras se
  ejecuta un proceso hijo de vista previa — este es el único log en disco
  que produce la librería, y está limitado al subproceso de vista previa,
  no a la sesión del agente.
- No hay registro de auditoría de aprobaciones persistido (quién aprobó
  qué llamada a herramienta, cuándo) — este es el elemento abierto
  **SEC-01**; ver [security](security.html) y [limits](limits.html).
- La visibilidad de depuración sobre los payloads en bruto de las
  herramientas se controla con `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` (ver
  [configuration](configuration.html)); cambia lo que se *muestra en la
  interfaz*, no lo que se escribe en disco.

## Coste y latencia

Las llamadas al LLM pasan por Snowflake Cortex a través del CLI/SDK de
CoCo. El coste y la latencia de esas llamadas son competencia de
Snowflake Cortex — streamlit-coco no rastrea, reporta, ni presupuesta
tokens, créditos de warehouse, ni latencia de llamada. `CocoEvent` lleva
un campo `cost_usd` y un campo `duration_ms` cuando el mensaje del SDK
subyacente los proporciona, pero la librería no agrega, persiste, ni
alerta sobre estos valores; una app que quiera seguimiento de
coste/latencia tiene que leer esos campos ella misma, por evento.

## Limpieza

Entre ejecuciones de demo o al desmontar una sesión:

- `stop_session(session_key="coco", gate_key="coco_started")` — derriba
  la `CocoSession` (cierra el worker en segundo plano) y limpia el flag
  de la puerta de inicio, de modo que la app vuelve a la pantalla de
  puerta de inicio.
- `session.close()` — cierra una sesión específica sin tocar el flag de
  la puerta de inicio.
- Mata cualquier proceso de vista previa en ejecución antes de cambiar
  `app_dir` en `app_viewer()`: usa `stop_app_preview()` (o el botón
  **Stop** de la interfaz). Solo se ejecuta un proceso de vista previa
  por `app_dir` a la vez (ver [limits](limits.html)).
- Limpia los artefactos generados entre pases de demo según se necesite:
  `_uploads/` bajo el `cwd` del agente (subidas del navegador),
  `examples/bi_to_semantic/out/` y
  `examples/bi_to_semantic/../workspaces/bi_to_semantic/` (excluidos de
  git), `examples/app_builder/out/<slug>/` (proyectos de app nombrados —
  eliminar vía la acción **Delete app** de Library/Brief o eliminando la
  carpeta). Ninguno de estos directorios se limpia automáticamente.
