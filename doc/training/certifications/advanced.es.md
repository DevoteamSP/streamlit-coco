# streamlit-coco — Certificación Advanced

**Umbral de aprobación: 24/30.** Prerrequisito: ≥ 3 meses de uso.

### Q1. ¿Qué cambió la corrección de `0.1.8` en la página Studio de App Builder?

a) "Save & regenerate" ahora escribe `BRIEF.md` a partir de los widgets del expander antes de encolar a CoCo, cerrando una condición de carrera en la que la página Brief podía sobrescribir el archivo recién editado en el mismo turno
b) La página Brief obtuvo un nuevo botón "Publish"
c) `output_schema` dejó de eliminar `$schema`/`$id`
d) El puerto de vista previa de App Builder cambió de 8513 a 8511

### Q2. ¿Qué cambió la corrección de `0.1.7` sobre `make audit` / `pip-audit` en CI?

a) Cambió de `pip-audit` a `safety`
b) Añadió `--skip-editable`, evitando un fallo falso-positivo de "dependency not found on PyPI" justo después de un bump de versión previo al tag
c) Desactivó `pip-audit` por completo en CI
d) Movió el trabajo de audit de `security.yml` a `release.yml`

### Q3. ¿Cuáles dos cosas abordó la corrección de `0.1.6`?

a) Añadió un nuevo campo `output_schema` y eliminó `on_structured_output`
b) Eliminó `$schema`/`$id` antes de pasar el JSON Schema al SDK de CoCo, y reemplazó el `use_container_width` obsoleto por `width="stretch"`
c) Añadió `max_turns` y eliminó `approval_timeout_seconds`
d) Cambió el ejemplo de salida estructurada de `panel()` a `chat()`

### Q4. ¿Qué error de JSON Schema evitó específicamente la corrección de `0.1.6`?

a) `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`, de un archivo de contrato que incluye una URI de draft
b) `KeyError: 'properties'`
c) `TypeError: schema must be a dict`
d) `ValidationError: additionalProperties not allowed`

### Q5. ¿Qué cambió en el flujo de seguridad de `0.1.5`?

a) CodeQL se añadió por primera vez
b) CodeQL se eliminó (una organización privada necesita una licencia GHAS); Gitleaks y pip-audit se mantuvieron
c) Gitleaks se reemplazó por el `gitleaks-action@v2` con licencia
d) pip-audit se eliminó en favor de otro scanner

### Q6. ¿Qué cambió la corrección de `0.1.0` sobre las tarjetas de herramienta Grep/Glob completadas?

a) Ahora muestran un resumen compacto en lugar de un volcado completo del resultado
b) Ahora muestran solo JSON en bruto
c) Se eliminaron por completo de la transcripción
d) Ahora requieren aprobación manual cada vez

### Q7. Una sesión lanza `SDKNotInstalledError`. ¿Qué indica esto, y cuál es la solución?

a) El CLI de CoCo no está en `PATH`; define `CORTEX_CODE_CLI_PATH`
b) Falta el SDK de Python (`cortex-code-agent-sdk`); ejecuta `pip install streamlit-coco[sdk]` (o `make install`)
c) El nombre de la conexión de Snowflake es incorrecto; corrige `connections.toml`
d) La aprobación expiró; aumenta `approval_timeout_seconds`

### Q8. Una sesión lanza `CLIProbeError`. ¿Qué significa esto?

a) El binario `cortex` no se encontró en ningún lugar de `PATH`
b) Existe un binario en la ruta configurada pero no respondió correctamente a `--version`
c) El nombre de la conexión de Snowflake no existe en `connections.toml`
d) El paquete del SDK de Python no está instalado

### Q9. Una sesión se queda atascada en "Starting CoCo…" sin más avance. ¿Cuál es el primer paso de diagnóstico recomendado?

a) Reinstalar `streamlit-coco` desde PyPI
b) Revisar los logs de la terminal y activar el modo debug (`STREAMLIT_COCO_DEBUG=1`)
c) Eliminar `~/.snowflake/connections.toml` y recrearlo
d) Cambiar `permission_mode` a `"plan"`

### Q10. El campo de entrada del chat permanece deshabilitado justo después de arrancar la app. ¿Cuál es la causa probable y la solución?

a) `SessionNotReadyError` / un estado de error — corrige el entorno y reinicia la sesión desde la barra lateral
b) `CwdUploadError` por una extensión de archivo rechazada
c) `ApprovalTimeoutError` tras 600 segundos sin respuesta
d) Un `output_schema` ausente

### Q11. ¿Cuál es el comportamiento `overwrite` por defecto de `upload_to_cwd()`, y en qué se diferencia del valor por defecto de subida de `chat_input_bar()`?

a) Ambos tienen por defecto `"replace"`
b) `upload_to_cwd()` tiene por defecto `"error"`; `chat_input_bar()` fija por defecto su `upload_overwrite` en `"replace"`
c) `upload_to_cwd()` tiene por defecto `"skip"`; `chat_input_bar()` tiene por defecto `"error"`
d) Ambos tienen por defecto `"skip"`

### Q12. ¿Qué busca el parser de logs de `app_viewer()` para detectar un error, y cuál es una limitación conocida?

a) Busca `Uncaught app exception` / `Traceback (most recent call last):`; una línea con marca de tiempo posterior puede leerse como "error cleared" aunque el error persista
b) Parsea el DOM de la app previsualizada directamente, ya que comparte origen con el anfitrión
c) Se basa únicamente en el código de salida del proceso hijo
d) Consulta el endpoint `/healthz` del servidor Streamlit

### Q13. ¿Por qué no puede la app anfitriona de `app_viewer()` leer directamente el traceback del DOM de la app previsualizada?

a) La app hija se ejecuta en un iframe en otro origen, así que "Fix with CoCo" es solo raspado de logs
b) Streamlit deshabilita el acceso al DOM para todos los iframes por política
c) La app hija se renderiza completamente en el servidor sin DOM
d) `on_fix` nunca está conectado en ningún ejemplo de primera parte

### Q14. ¿Cuándo se dispara `ApprovalTimeoutError`?

a) La herramienta se ejecuta automáticamente de todos modos una vez que aplicaría "Always allow"
b) Después de que transcurren `approval_timeout_seconds` (por defecto 600s / 10 min) sin respuesta
c) Solo para la familia de herramientas SQL
d) Inmediatamente cada vez que se renderiza una tarjeta de herramienta, sin importar la configuración de timeout

### Q15. ¿Persiste alguna vez "Always allow" a través de un reinicio del proceso Streamlit?

a) Sí, se escribe en la configuración de `~/.snowflake/`
b) No — tiene alcance de sesión únicamente y se borra al reiniciar o al reset
c) Sí, pero solo para la familia de herramientas SQL
d) Sí, si `require_approval_for` es una lista en lugar de un callable

### Q16. ¿Qué anula la variable de entorno `CORTEX_CODE_CLI_PATH`?

a) El nombre de la conexión de Snowflake
b) La ruta del CLI `cortex`, cuando no está en `PATH` ni se pasa como `CocoOptions.cli_path`
c) El subdirectorio de subida usado por `cwd_uploader()`
d) La duración del timeout de aprobación

### Q17. ¿Qué valores trata `is_debug_mode()` como verdaderos para `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG`?

a) Cualquier cadena no vacía
b) `"1"`, `"true"`, `"yes"`, `"on"` (sin distinguir mayúsculas), o un `st.session_state["coco_debug"]` verdadero
c) Solo el entero `1`, nada más
d) `"debug"` o `"verbose"`

### Q18. ¿Dónde se lee `TTS_DATA_MODE`, y qué afecta?

a) Es una variable de entorno global leída por `streamlit_coco/diagnostics.py` para seleccionar la conexión de Snowflake
b) Solo la lee el proceso hijo de vista previa de `examples/bi_to_semantic` (vía `app_viewer(env=...)`) para seleccionar el modo de datos desconectado frente a conectado de la app consumidora generada
c) Controla si se muestran los payloads de `STREAMLIT_COCO_DEBUG`
d) Es una variable obligatoria para cada app de ejemplo

### Q19. ¿Cuál es el estado del hallazgo de seguridad SEC-01?

a) Resuelto en `0.1.5` — ahora se persiste un registro de auditoría de aprobaciones
b) Abierto, objetivo v0.2 — persistir un registro de auditoría de aprobaciones (quién aprobó qué, cuándo)
c) No se rastrea; no hay requisito de registro de auditoría
d) Resuelto en `0.1.0`

### Q20. ¿Cuál es el estado de SEC-02?

a) Resuelto — un documento dedicado de recomendación de rol de mínimo privilegio está incluido en el repositorio
b) Abierto, objetivo v0.2 — documentar una recomendación dedicada de rol de mínimo privilegio; la página de seguridad actual solo da orientación provisional
c) No aplica; la librería gestiona los grants de Snowflake directamente
d) Resuelto en `0.1.5` junto con la eliminación de CodeQL

### Q21. ¿Cuál es el estado actual de CodeQL en el CI de este repositorio?

a) Se ejecuta en cada PR, como sigue afirmando la tabla resumen de `findings-report.md`
b) Se eliminó en `0.1.5` porque la organización privada de GitHub carece de licencia GHAS; hoy solo se ejecutan Gitleaks y pip-audit
c) Solo se ejecuta en la programación semanal del lunes, no en los PR
d) Se reemplazó por otro analizador estático en `0.1.6`

### Q22. ¿Qué dos scanners se ejecutan realmente en `security.yml` hoy, y con qué disparadores?

a) CodeQL y Gitleaks, solo en cada push
b) Gitleaks (CLI) y `pip-audit --skip-editable`, en cada PR, cada push a `main`, y semanalmente (lunes)
c) pip-audit y un scanner de dependencias, solo cada noche
d) Solo Gitleaks, en los tags de release

### Q23. ¿Qué elementos de seguridad están ABIERTOS (no resueltos) según el modelo de amenazas? (Opción múltiple — selecciona todas las que apliquen)

a) SEC-01 — registro de auditoría de aprobaciones persistido
b) SEC-02 — documento de recomendación de rol de mínimo privilegio
c) SEC-03 — confirmar `uv.lock`
d) SEC-04 — generación de SBOM en CI

### Q24. Según la revisión manual en `findings-report.md` (versión auditada `0.1.0`), ¿cuál de estos NO encontró la revisión en el código fuente?

a) `shell=True`, credenciales embebidas, o uso de `eval()`/`exec()`
b) Cualquier uso de `pandas`
c) Cualquier widget de Streamlit
d) Cualquier type hint

### Q25. ¿Qué dispara el reinicio del worker en segundo plano de una `CocoSession`?

a) Cualquier cambio en cualquier campo de `CocoOptions`
b) Un cambio en `options_hash()`, calculado solo a partir de los campos que afectan a los permisos de herramienta (por ejemplo `allowed_tools`, `disallowed_tools`, `permission_mode`, `require_approval_for`)
c) Cada llamada a `session.send()`
d) Un rerun de Streamlit, sin importar los cambios de opciones

### Q26. ¿Qué hace `wrap_exception()`?

a) Reintenta una llamada fallida al SDK hasta tres veces antes de lanzar una excepción
b) Mapea las excepciones en bruto del SDK/runtime a las subclases tipadas `CocoError` de la librería, mediante detección de mensaje más un kwarg `context=` (por ejemplo `"session_start"`, `"query"`, `"approval"`)
c) Suprime todas las excepciones y las registra silenciosamente
d) Convierte cualquier excepción en `SDKNotInstalledError`

### Q27. ¿Qué subclase también `ApprovalTimeoutError`, además de `CocoError`?

a) `ValueError`
b) `TimeoutError`
c) `ConnectionError`
d) `KeyError`

### Q28. ¿Qué subclase también `SDKNotInstalledError`, además de `CocoError`?

a) `ImportError`
b) `RuntimeError`
c) `OSError`
d) `AttributeError`

### Q29. ¿Qué ejecuta el flujo de trabajo de CI `ci.yml` en cada PR a `main`?

a) Tests unitarios y e2e, sin un agente CoCo en vivo
b) Solo las listas de verificación manuales/en vivo que requieren un CLI real y Snowflake
c) Solo `make audit`
d) Una build de release completa y publicación a PyPI

### Q30. ¿Por qué pudo `make audit` fallar de forma espuria justo después de un bump de versión, antes de la corrección de `0.1.7`?

a) `pip-audit` trató la versión local recién incrementada, aún no publicada, como "dependency not found on PyPI" — corregido añadiendo `--skip-editable`
b) `ruff` marcó la cadena de versión como inválida
c) El lockfile no estaba confirmado
d) CodeQL bloqueó el pipeline

## Answer Key

| P | Respuesta | Explicación |
|---|--------|-------------|
| 1 | **a** | CHANGELOG `0.1.8` Fixed: Save & regenerate ahora escribe `BRIEF.md` antes de encolar a CoCo, cerrando la condición de carrera de sobrescritura. |
| 2 | **b** | CHANGELOG `0.1.7` Fixed: `--skip-editable` evita un fallo de audit falso de "not found on PyPI" tras un bump de versión. |
| 3 | **b** | CHANGELOG `0.1.6` Fixed cubre tanto la eliminación de `$schema`/`$id` como el cambio de `use_container_width` a `width="stretch"`. |
| 4 | **a** | El texto exacto del error citado en la entrada Fixed de `0.1.6` es el rechazo de referencia de esquema de URI de draft. |
| 5 | **b** | CHANGELOG `0.1.5` Changed (Security): CodeQL eliminado (falta de licencia GHAS), Gitleaks y pip-audit mantenidos. |
| 6 | **a** | CHANGELOG `0.1.0` Fixed: las tarjetas completadas de Grep/Glob muestran un resumen compacto en lugar de un volcado completo. |
| 7 | **b** | `SDKNotInstalledError` significa que falta el extra opcional del SDK; la solución es `pip install streamlit-coco[sdk]` o `make install`. |
| 8 | **b** | `CLIProbeError` es específicamente "binario encontrado pero `--version` falló", distinto de `CLINotFoundError`. |
| 9 | **b** | La solución de la tabla de resolución de problemas para una conexión atascada es revisar los logs de la terminal y activar `STREAMLIT_COCO_DEBUG=1`. |
| 10 | **a** | El campo de entrada deshabilitado tras el arranque se corresponde con `SessionNotReadyError`/estado de error; corrige el entorno y reinicia desde la barra lateral. |
| 11 | **b** | El valor por defecto propio de `upload_to_cwd()` es `overwrite="error"`; `chat_input_bar()` fija su `upload_overwrite` por defecto en `"replace"`. |
| 12 | **a** | El parser busca esas dos cadenas; una línea con marca de tiempo posterior puede malinterpretarse como que borra el error. |
| 13 | **a** | La vista previa hija es otro origen (puerto diferente), así que solo el log raspado — no el DOM — está disponible para "Fix with CoCo". |
| 14 | **b** | `ApprovalTimeoutError` se dispara una vez que transcurren `approval_timeout_seconds` (por defecto 600s) sin decisión. |
| 15 | **b** | "Always allow" vive solo en `PermissionManager.always_allowed_tools` en memoria; se borra en `reset()`, `close()`, o al reiniciar. |
| 16 | **b** | `CORTEX_CODE_CLI_PATH` anula la búsqueda de ruta del CLI cuando este no está en `PATH` y no se pasó `cli_path`. |
| 17 | **b** | El conjunto documentado de valores verdaderos de `is_debug_mode()` es `"1"`/`"true"`/`"yes"`/`"on"` (sin distinguir mayúsculas) o un indicador verdadero en el estado de sesión. |
| 18 | **b** | `TTS_DATA_MODE` solo se lee dentro del proceso hijo de vista previa de `bi_to_semantic`, vía `app_viewer(env=...)`. |
| 19 | **b** | SEC-01 figura abierto, objetivo v0.2, en `threat-model.md` §7. |
| 20 | **b** | SEC-02 figura abierto, objetivo v0.2; la orientación actual de la página de seguridad es provisional, no el entregable rastreado. |
| 21 | **b** | `0.1.5` eliminó el trabajo de CodeQL por motivos de licencia; `security.yml` hoy solo ejecuta Gitleaks y pip-audit. |
| 22 | **b** | Gitleaks (CLI) y `pip-audit --skip-editable` se ejecutan en PR, push a main, y la programación semanal del lunes. |
| 23 | **A, B** | SEC-01 y SEC-02 están abiertos (objetivo v0.2); SEC-03 (lockfile) y SEC-04 (SBOM) están ambos resueltos. |
| 24 | **a** | La revisión manual declara explícitamente que no se encontraron `shell=True`, credenciales embebidas, ni `eval()`/`exec()`. |
| 25 | **b** | `options_hash()` solo aplica hash a los campos que afectan a los permisos de herramienta; `CocoSession` reinicia su worker solo cuando ese hash cambia. |
| 26 | **b** | `wrap_exception()` detecta el mensaje de la excepción en bruto y usa `context=` para elegir la subclase `CocoError` correcta. |
| 27 | **b** | `ApprovalTimeoutError` está documentado como también `TimeoutError`. |
| 28 | **a** | `SDKNotInstalledError` está documentado como también `ImportError`. |
| 29 | **a** | CI ejecuta tests unitarios y e2e en cada PR a `main`, sin un agente CoCo en vivo; las comprobaciones en vivo son solo manuales. |
| 30 | **a** | Antes de `0.1.7`, `pip-audit` sin `--skip-editable` reportaba la versión local recién incrementada como ausente en PyPI. |
