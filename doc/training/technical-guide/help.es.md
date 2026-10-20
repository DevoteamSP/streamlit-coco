# Ayuda

Por área y síntoma. Cada encabezado de abajo lleva un `{#anchor}` estable
al que otras páginas enlazan como `help.html#<anchor>`.

## Entorno y conexión

### SDK no instalado {#sdk-not-installed}

**Ves:** `cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]`
**Causa probable:** `streamlit-coco` se instaló sin el extra `[sdk]`, así
que `cortex_code_agent_sdk` no es importable.
**Diagnostica:** `python -c "import cortex_code_agent_sdk"`
**Solución:** `pip install "streamlit-coco[sdk]"` (o `make install`, que
ejecuta `uv sync --extra dev`).
**Si eso falla:** confirma que el entorno Python activo es aquel desde el
que realmente se ejecuta Streamlit (`which python`, `which streamlit`);
un segundo virtualenv con el SDK instalado no ayuda si la app se ejecuta
en otro diferente.

### CLI de CoCo no encontrado {#cli-not-found}

**Ves:** `CoCo CLI not found on PATH. Install the cortex CLI and ensure `cortex --version` works, or set CORTEX_CODE_CLI_PATH.` (o, cuando se pasó `cli_path` explícitamente, `CoCo CLI not found at '<path>'`)
**Causa probable:** el binario `cortex` no está instalado, o está
instalado en algún lugar que no está en `PATH`.
**Diagnostica:** `cortex --version`; `echo $CORTEX_CODE_CLI_PATH`.
**Solución:** instala el CLI de CoCo, o define `export
CORTEX_CODE_CLI_PATH=/path/to/cortex`, o pasa `cli_path=` en
`CocoOptions` (ver [configuration](sections/configuration.html)).
**Si eso falla:** comprueba que la ubicación de instalación del CLI
coincide con lo que la shell que lanza Streamlit realmente ve — un CLI
instalado bajo un perfil de usuario o shell diferente no estará en
`PATH` para el proceso de Streamlit.

### Sonda del CLI fallida {#cli-probe-failed}

**Ves:** `CoCo CLI at '<path>' did not respond to --version`
**Causa probable:** existe un binario en la ruta resuelta pero no es un
CLI `cortex` funcional (archivo equivocado, instalación rota, o
permisos).
**Diagnostica:** ejecuta `cortex --version` manualmente y comprueba tanto
el código de salida como la salida en sí; `ls -l "$(which cortex)"` para
comprobar permisos.
**Solución:** reinstala el CLI; corrige los permisos de ejecución
(`chmod +x`) si es necesario.
**Si eso falla:** pide al mantenedor/propietario del CLI un binario
conocido como bueno y compara checksums.

### Configuración de Snowflake no encontrada {#snowflake-config-not-found}

**Ves:** `No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml) with an authenticated connection.`
**Causa probable:** no existe ningún archivo `*.toml` bajo
`~/.snowflake/`.
**Diagnostica:** `ls ~/.snowflake/*.toml`, o
`st_coco.list_snowflake_toml_files()`.
**Solución:** crea `~/.snowflake/connections.toml` con al menos una
entrada `[connections.<name>]` — ver
[configuration](sections/configuration.html) para la forma.
**Si eso falla:** confirma que `HOME` resuelve al directorio esperado en
el entorno que ejecuta Streamlit (los contenedores y las cuentas de
servicio a veces tienen un `HOME` diferente).

### Error de conexión de CoCo {#coco-connection-error}

**Ves:** un mensaje `CocoConnectionError` — el texto subyacente nombra la
conexión o un fallo de autenticación (por ejemplo "connection not
found," "unknown connection," u otro fallo de autenticación/conexión).
**Causa probable:** el nombre de conexión pasado a
`CocoOptions(connection=...)` no coincide con ningún perfil en el
archivo TOML resuelto, o las credenciales del perfil están obsoletas o
son inválidas.
**Diagnostica:** `st_coco.list_snowflake_connections(toml_file=...)` para
listar los nombres de perfil conocidos; prueba la misma conexión con el
Snowflake CLI directamente.
**Solución:** corrige el nombre de la conexión, o corrige los campos
`account`/`user`/`authenticator` del perfil en `connections.toml`.
**Si eso falla:** confirma que el identificador de cuenta y el
autenticador coinciden con lo que emitió tu administrador de Snowflake;
vuelve a ejecutar el flujo de autenticación de navegador externo o de
par de claves fuera de streamlit-coco primero para aislar si el
problema es el archivo de conexión o la propia credencial.

## Ciclo de vida de la sesión

### Sesión atascada en "Starting CoCo…" {#session-stuck-connecting}

**Ves:** el estado del panel/rail se queda en "Starting CoCo…" y nunca
llega a listo.
**Causa probable:** un problema de CLI o de red durante la conexión (el
subproceso del CLI nunca devuelve una señal de listo).
**Diagnostica:** revisa la terminal que ejecuta Streamlit en busca de
errores del CLI; activa la salida de debug con `STREAMLIT_COCO_DEBUG=1`
(ver [debug-mode-not-showing-payloads](#debug-mode-not-showing-payloads)).
**Solución:** corrige el problema de entorno subyacente (CLI/conexión —
ver las entradas de Entorno y conexión arriba), luego reinicia la
sesión.
**Si eso falla:** captura la salida de la terminal y regístrala contra
el CLI/SDK, ya que el fallo está ocurriendo por debajo del propio
mapeo de errores de la librería.

### Sesión no lista {#session-not-ready}

**Ves:** un `SessionNotReadyError`, o el estado de la sesión muestra
`error`.
**Causa probable:** timeout de conexión o fallo de arranque —
`ensure_ready(timeout=120)` se rindió, o el worker reportó un fallo de
arranque.
**Diagnostica:** revisa `session.last_error` y `session.init_info`;
revisa la salida de `render_session_status()` en la interfaz.
**Solución:** corrige el problema de entorno que señala `last_error`,
luego llama a `reset_session(...)` (o usa la acción de reset de la
barra lateral/puerta de inicio) para reiniciar la sesión.
**Si eso falla:** vuelve a ejecutar `check_environment()` de forma
independiente para confirmar el estado SDK/CLI/Snowflake fuera de una
sesión en vivo antes de reintentar.

### Campo de entrada deshabilitado tras el arranque {#input-disabled-after-boot}

**Ves:** el campo de entrada del chat permanece deshabilitado incluso
después de que la puerta de inicio indica que la sesión arrancó.
**Causa probable:** la sesión terminó en estado `SessionNotReadyError` /
`ERROR` justo después de arrancar (misma causa subyacente que
[session-not-ready](#session-not-ready)).
**Diagnostica:** revisa la insignia de estado de la sesión /
`render_session_status()`.
**Solución:** corrige el entorno, luego reinicia la sesión desde la
barra lateral (`stop_session()` seguido de reiniciar la puerta de
inicio).
**Si eso falla:** ver el paso de escalada de
[session-not-ready](#session-not-ready).

## Aprobaciones

### Aprobación expirada {#approval-timeout}

**Ves:** `Approval timed out for tool <tool_name>` (`ApprovalTimeoutError`).
**Causa probable:** nadie resolvió la aprobación pendiente dentro de
`CocoOptions.approval_timeout_seconds` (por defecto `600.0`, 10
minutos).
**Diagnostica:** confirma que se pasó `show_approvals=True` a
`panel()`/`copilot_rail()` para que la interfaz de aprobación
realmente se renderizara; comprueba si los botones de aprobación eran
accesibles (no cubiertos por otro diálogo).
**Solución:** responde dentro de la ventana la próxima vez, o aumenta
`approval_timeout_seconds` para sesiones que esperan una revisión humana
más larga, luego reenvía el prompt.
**Si eso falla:** llama a `approve_pending()` / `deny_pending()`
directamente contra la sesión para una interfaz de aprobación
personalizada que no dependa del tiempo por defecto de
`render_approvals()`.

### "Always allow" no persiste {#always-allow-scope}

**Ves:** una herramienta que fue "Always allowed" antes vuelve a pedir
aprobación tras un reset de sesión o un reinicio de la app.
**Causa probable:** esto es esperado. `PermissionManager.always_allowed_tools`
es un conjunto en memoria sobre la `CocoSession` en vivo; nunca se
escribe en disco y se borra con `session.reset()`, `session.close()`, y
al reiniciar el proceso.
**Diagnostica:** comprueba si ocurrió un reset/reinicio entre las dos
aprobaciones (reset de barra lateral, `stop_session()`, o una recarga
de página que creó una sesión nueva).
**Solución:** haz clic en **Always allow** de nuevo en la sesión nueva;
no hay forma de hacer que "Always allow" sobreviva a un reset, por
diseño (ver [security](sections/security.html)).
**Si eso falla:** si se requiere una política duradera por herramienta
entre sesiones, eso no está implementado hoy — rastréalo contra SEC-01
en [limits](sections/limits.html) en lugar de buscar una configuración
oculta.

## Subida de archivos

### Subida rechazada: extensión {#upload-rejected-extension}

**Ves:** `Disallowed file extension for '<name>' (allowed: <list>)` (`CwdUploadError`).
**Causa probable:** el sufijo del archivo subido no está en
`DEFAULT_ALLOWED_EXTENSIONS` (o en un `allowed_extensions` provisto por
quien llama).
**Diagnostica:** compara la extensión del archivo con la constante de
lista permitida en `streamlit_coco/upload.py`.
**Solución:** convierte/renombra el archivo a un tipo permitido, o llama
a `upload_to_cwd(..., allowed_extensions={...})` con una lista más
amplia para esa app.
**Si eso falla:** confirma si el archivo realmente necesita llegar al
`cwd` del agente — algunos flujos de trabajo solo necesitan que se le
diga al agente el contenido, no el archivo en bruto.

### Subida rechazada: tamaño {#upload-rejected-size}

**Ves:** `File '<name>' is <n> bytes; max allowed is <max_bytes>` (`CwdUploadError`).
**Causa probable:** el archivo excede `DEFAULT_MAX_BYTES` (10 MiB) o un
`max_bytes` provisto por quien llama.
**Diagnostica:** compara el tamaño real del archivo con el límite
configurado.
**Solución:** divide o comprime el archivo, o llama a
`upload_to_cwd(..., max_bytes=...)` con un límite más alto para esa app.
**Si eso falla:** considera si el archivo pertenece a un stage de
Snowflake en lugar de la cuarentena local de `cwd` — los conjuntos de
datos grandes quedan explícitamente fuera de alcance de esta ruta de
subida (ver `doc/features/file-upload/file-upload.md`).

### Conflicto de nombre en la subida {#upload-name-conflict}

**Ves:** `File already exists: <relative path> (pass overwrite='replace' or 'skip')` (`CwdUploadError`).
**Causa probable:** `overwrite="error"` (el valor por defecto de
`upload_to_cwd`) y ya existe un archivo con el mismo nombre saneado bajo
el subdirectorio de subida.
**Diagnostica:** lista el directorio de subida
(`list_cwd_uploads(target)`) para ver el archivo existente.
**Solución:** pasa `overwrite="replace"` o `overwrite="skip"` a
`upload_to_cwd()` / `cwd_uploader()`, o renombra el archivo antes de
subirlo. Ten en cuenta que `chat_input_bar(accept_file=...)` ya define
por defecto `upload_overwrite="replace"`, así que esto surge
principalmente a través de llamadas directas a `upload_to_cwd()` o un
`cwd_uploader()` configurado con `overwrite="error"`.
**Si eso falla:** si se esperan colisiones y siempre deberían ganar,
cambia el modo de sobrescritura por defecto de quien llama en lugar de
gestionar cada conflicto manualmente.

## Vista previa de app

### La vista previa no arranca {#preview-wont-start}

**Ves:** hacer clic en **Run** en `app_viewer()` no produce ningún
iframe ni URL accesible.
**Causa probable:** el rango de puertos libres (`8511`–`8520`) está
agotado, `app_dir` no tiene `streamlit_app.py` (o un `script_name`
diferente), o un proceso de vista previa obsoleto para el mismo
`app_dir` ya está reteniendo el puerto.
**Diagnostica:** comprueba `preview_running(app_dir)` /
`preview_url(app_dir)`; revisa `.preview.log`, `.preview.pid`,
`.preview.port` dentro de `app_dir`; comprueba
`last_preview_exception(app_dir)`.
**Solución:** llama a `stop_app_preview(app_dir)` para limpiar un
proceso obsoleto, confirma que `app_dir` realmente contiene
`streamlit_app.py`, y luego **Run** de nuevo.
**Si eso falla:** libera el rango de puertos `8511`–`8520` en el host
(otra vista previa o un proceso no relacionado puede estar reteniéndolo),
y confirma que solo un `app_viewer()` apunta a este `app_dir` (ver
[limits](sections/limits.html)).

### "Fix with CoCo" no está conectado {#fix-with-coco-not-wired}

**Ves:** hacer clic en **Fix with CoCo** no hace nada, o muestra un
toast pidiendo "wire `on_fix=`".
**Causa probable:** la app anfitriona llamó a `app_viewer()` sin un
callback `on_fix=`. `app_viewer()` no encola un trabajo por sí solo —
solo construye el prompt vía `default_fix_prompt()`.
**Diagnostica:** revisa la llamada a `app_viewer(...)` en busca de
`on_fix=`.
**Solución:** pasa `on_fix=<callback>` que encole
`default_fix_prompt(traceback, app_dir)` como un trabajo en la propia
sesión de Copilot del anfitrión y abra el rail de Copilot — ver
`doc/features/app-viewer/app-viewer.md` para el patrón de referencia.
**Si eso falla:** confirma que el anfitrión realmente compone
`copilot_rail()` junto a `app_viewer()` — `app_viewer()` deliberadamente
no importa ni conoce `copilot_rail()` (ver
[architecture](sections/architecture.html)).

### Fallo de parseo del log de vista previa {#preview-log-parse-miss}

**Ves:** la app hija está visiblemente rota, pero el expander **Preview
exception** no muestra ningún traceback.
**Causa probable:** deriva del formato de log. El parser busca los
marcadores literales `Uncaught app exception` y
`Traceback (most recent call last):` en `.preview.log`, y trata
cualquier línea posterior con marca de tiempo como "error cleared" — un
log que no coincide con esos marcadores, o que registra una línea
posterior no relacionada, se lee como despejado aunque la app siga
rota.
**Diagnostica:** lee `.preview.log` directamente (o
`preview_log_tail(app_dir)`) en lugar de confiar en el expander.
**Solución:** haz clic en **Fix with CoCo** de todos modos — sigue
enviando el tail del log como parte del prompt incluso cuando el parser
no detectó una excepción en vivo.
**Si eso falla:** copia las líneas de log relevantes en un prompt manual
a CoCo, ya que los marcadores automáticos no cubren esta forma de log.

## Salida estructurada

### Salida estructurada que no se renderiza {#structured-output-not-rendering}

**Ves:** la respuesta del agente tiene forma de JSON, pero no aparece
ningún panel estructurado ni widget impulsado por callback.
**Causa probable:** una de dos cosas — o bien se definió
`on_structured_output` / `structured_output_container`, lo que omite
intencionalmente el panel estructurado en línea por defecto
(exclusión mutua), o `CocoOptions.output_schema` nunca se definió, así
que el agente no estaba realmente limitado a producir un payload
`structured_output` conforme al esquema aunque el texto de respuesta
parezca JSON.
**Diagnostica:** comprueba `session.chat_result().structured_output`
tras el turno; comprueba si se pasó `on_structured_output=` o
`structured_output_container=` a `panel()` / `copilot_rail()`.
**Solución:** define `CocoOptions.output_schema={...}` para que el SDK
imponga `output_format`, y confía en el panel en línea por defecto (sin
callback/contenedor definido) o lee `structured_output` desde el
callback.
**Si eso falla:** confirma que la respuesta viene de un turno que
realmente se ejecutó con el `CocoOptions` que lleva el esquema — una
sesión creada antes de añadir el esquema mantiene su worker original
hasta que cambie `options_hash()` (ver
[architecture](sections/architecture.html)).

### `$schema` / `$id` rechazado {#schema-dollar-schema-rejected}

**Ves:** `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`.
**Causa probable:** un archivo de contrato JSON Schema (como los que hay
bajo `examples/bi_to_semantic/contracts/`) incluye una clave `$schema`
(o `$id`), y esto se pasó directamente al SDK sin eliminarla — el
resolutor de esquema del SDK intenta obtener esa URI y falla.
**Diagnostica:** comprueba la versión de `streamlit-coco` en uso;
comprueba si `output_schema` se construye fusionando a mano un archivo
de contrato después de la construcción (lo que podría reintroducir
`$schema`).
**Solución:** actualiza a `>=0.1.6` — `CocoOptions.to_sdk_options()`
ahora elimina `$schema`/`$id` automáticamente (`_schema_for_sdk()` en
`streamlit_coco/options.py`) antes de reenviar el esquema al SDK.
**Si eso falla:** si ya estás en `>=0.1.6` y el error persiste, confirma
que nada aguas abajo reinserta `$schema` en el diccionario pasado como
`output_schema` después de construir `CocoOptions`.

## Release y CI

### Falso positivo de `pip-audit` sobre el paquete editable {#pip-audit-editable-false-positive}

**Ves:** `pip-audit` reporta `streamlit-coco … Dependency not found on PyPI and could not be audited (<version>)`.
**Causa probable:** ejecutar `pip-audit` simple contra una instalación
editable o previa al tag de `streamlit-coco` mismo, que aún no está
publicada en esa versión.
**Diagnostica:** comprueba qué comando se ejecutó — `pip-audit` solo
mostrará esto; `make audit` / `pip-audit --skip-editable` no lo hará.
**Solución:** usa `make audit` (o `pip-audit --skip-editable`
directamente) — esto se corrigió en `0.1.7` tanto para el objetivo del
Makefile como para CI, para que un bump de versión previo al tag no se
reporte como un fallo de audit falso-positivo.
**Si eso falla:** si el mismo mensaje aparece con `--skip-editable` ya
definido, trátalo como un gap de audit real y regístralo en lugar de
asumir que es este falso positivo conocido.

## Modo debug

### El modo debug no muestra los payloads {#debug-mode-not-showing-payloads}

**Ves:** `STREAMLIT_COCO_DEBUG` (o `COCO_DEBUG`) estaba definido, pero
no aparece ninguna sección "Raw tool payload" en la transcripción.
**Causa probable:** el valor no es una de las cadenas verdaderas
reconocidas (`"1"`, `"true"`, `"yes"`, `"on"`, sin distinguir
mayúsculas), o la variable se exportó en una shell/proceso diferente al
que ejecuta Streamlit.
**Diagnostica:** `echo $STREAMLIT_COCO_DEBUG` en la shell exacta que
lanza `streamlit run`; confirma que el conjunto de valores verdaderos de
`is_debug_mode()` coincide con el valor usado.
**Solución:** `export STREAMLIT_COCO_DEBUG=1` (o `COCO_DEBUG=1`) antes
de iniciar Streamlit en esa misma shell, o define
`st.session_state["coco_debug"] = True` dentro de la app para un
interruptor impulsado por la interfaz.
**Si eso falla:** confirma que el proceso de Streamlit realmente se
reinició después de definir la variable — las variables de entorno se
leen en el momento de la llamada por `is_debug_mode()`, pero un proceso
iniciado antes de que se hiciera el export en su propia shell no lo
verá.

## App Builder

### Condición de carrera de sobrescritura del brief de App Builder {#app-builder-brief-overwrite-race}

**Ves:** las ediciones hechas en el expander **App brief** de Studio
parecen perderse, o una ejecución de **Save & regenerate** usa un brief
obsoleto.
**Causa probable:** antes de `0.1.8`, **Save & regenerate** podía encolar
a CoCo antes de que `BRIEF.md` se escribiera a partir de los valores de
campo actuales del expander, y la página Brief podía sobrescribir
`BRIEF.md` de nuevo en el mismo turno — una condición de carrera entre
las dos escrituras.
**Diagnostica:** comprueba la versión instalada
(`streamlit_coco.__version__`).
**Solución:** actualiza a `>=0.1.8` — **Save & regenerate** ahora
escribe `BRIEF.md` a partir de los widgets del expander antes de encolar
a CoCo, y la página Brief ya no sobrescribe ese archivo en el mismo
turno.
**Si eso falla:** si esto sigue viéndose en `>=0.1.8`, captura la
secuencia exacta de clics (qué página, qué botón, en qué orden) y
regístralo — la corrección de orden apuntó a la ruta específica de Save
& regenerate, no a cualquier posible secuencia de edición concurrente.
