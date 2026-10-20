# Preguntas frecuentes

## ¿Cómo instalo streamlit-coco?

`pip install streamlit-coco[sdk]`. Los pasos completos, prerrequisitos y
verificación están en Enablement [`setup.html`](../../enablement/setup.html).

## ¿Está lista para producción?

No — la versión que describe esta guía es alpha (ver el
[índice](../index.html) para saber cuál es exactamente).

## ¿Necesita una conexión de Snowflake?

Para cualquier funcionalidad respaldada por CoCo, sí — el agente se
ejecuta a través del CLI/SDK de Cortex Code contra una conexión de
Snowflake configurada. Algunas pantallas de las apps de ejemplo funcionan
sin una: las pantallas de estate-map y KPI-inventory de BI → Semantic
parsean workbooks de forma determinista, y el consumidor Streamlit
determinista que generan no necesita warehouse para verse.

## ¿Qué LLM usa?

El modelo que sea que use Cortex Code por debajo. No se requiere ninguna
configuración de modelo más allá de `CocoOptions.model` (déjalo en
`None`, o define `"auto"`).

## ¿Puedo personalizar qué herramientas necesitan aprobación?

Sí — `CocoOptions.allowed_tools` y `CocoOptions.require_approval_for`.
`AskUserQuestion` y `ExitPlanMode` siempre requieren aprobación sin
importar ninguna de las dos configuraciones. Ver
[Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html).

## ¿Qué pasa si deniego una aprobación?

La llamada a la herramienta no se ejecuta. El turno del agente continúa
desde ahí, opcionalmente con el motivo pasado a `deny_pending()`.

## ¿Hay un registro persistido de las decisiones de aprobación?

No — las decisiones de aprobación, incluido "Always allow", se
mantienen solo en la sesión y no se escriben en un registro de auditoría
persistido.

## ¿En qué se diferencia de usar el CLI de CoCo directamente?

La librería añade la plomería específica de Streamlit que el CLI no
proporciona por sí solo: estado de sesión seguro frente a reruns,
renderizado en streaming, tarjetas de herramienta, y la interfaz de
aprobación.

## ¿Funciona la subida de archivos?

Sí — `upload_to_cwd()` / `cwd_uploader()` /
`chat_input_bar(accept_file=...)` escriben en el `cwd` del agente. Ver
[Quiero añadir subida de archivos](task-add-file-uploads.html).

## ¿Qué es `copilot_rail()`?

Un Copilot en rail lateral derecho construido alrededor de `panel()`,
para incrustar CoCo dentro de una app multipágina más grande en lugar de
como un chat de página completa. Ver las entradas de Backlog Desk y BI →
Semantic en [Referencia de apps de ejemplo](reference-examples.html).

## ¿Funciona con Streamlit in Snowflake (SiS) o SPCS?

No hoy. Local — Streamlit, el CLI de CoCo y la configuración de
Snowflake en la misma máquina — es el único objetivo de despliegue que
lanza esta versión.

## ¿Cómo veo los payloads en bruto de solicitud/respuesta de las herramientas?

Define `STREAMLIT_COCO_DEBUG=1` o `COCO_DEBUG=1` (o
`st.session_state["coco_debug"] = True`). Si los payloads aún no
aparecen, ver
[`help.html#debug-mode-not-showing-payloads`](../../technical-guide/help.html#debug-mode-not-showing-payloads).

## La sesión dice "Starting CoCo…" y nunca conecta — ¿qué reviso?

Ver
[`help.html#session-stuck-connecting`](../../technical-guide/help.html#session-stuck-connecting)
y, si la propia conexión es el problema,
[`help.html#coco-connection-error`](../../technical-guide/help.html#coco-connection-error) /
[`help.html#snowflake-config-not-found`](../../technical-guide/help.html#snowflake-config-not-found).

## `make audit` falla justo después de subir la versión en `pyproject.toml` — ¿es real?

Normalmente no — ver
[`help.html#pip-audit-editable-false-positive`](../../technical-guide/help.html#pip-audit-editable-false-positive).

## La página Studio de App Builder parece sobrescribir mis ediciones del brief al hacer Save & regenerate

Ver
[`help.html#app-builder-brief-overwrite-race`](../../technical-guide/help.html#app-builder-brief-overwrite-race).

## ¿Dónde encuentro la lista actual de gaps conocidos para este asset?

`dsp-assets/audits/streamlit-coco/` contiene el último informe de gaps;
esta guía no repite su contenido ya que cambia entre releases.
