# streamlit-coco — Certificación Expert

**Umbral de aprobación: 24/30.** Prerrequisito: ≥ 12 meses de uso.

### Q1. ¿Qué usa `CocoSession` internamente para impulsar el cliente del SDK?

a) Una llamada bloqueante síncrona desde el hilo principal de Streamlit
b) Un hilo en segundo plano (`threading.Thread`, llamado `coco-session`) ejecutando un bucle asyncio que envuelve `CortexCodeSDKClient`
c) Un proceso Streamlit separado por sesión
d) Una cola de tareas respaldada por un broker externo

### Q2. ¿Qué invariante permite que `examples/headless_pipeline.py` se ejecute desde una terminal simple sin Streamlit instalado?

a) Los exports de la interfaz (`panel`, `copilot_rail`, `chat_input_bar`, …) se resuelven de forma perezosa vía `streamlit_coco.__getattr__`; los imports headless principales (`CocoSession`, `query`, `CocoOptions`, las funciones de permisos, la jerarquía de errores) nunca importan `streamlit`
b) `streamlit` se incluye como dependencia vendorizada dentro de `streamlit_coco`
c) El ejemplo headless hace monkey-patch de `sys.modules["streamlit"]`
d) `CocoSession` detecta la ausencia de Streamlit y recurre automáticamente a un modo solo-CLI

### Q3. Cuando una llamada a herramienta necesita aprobación, ¿qué se bloquea exactamente, y hasta cuándo?

a) El hilo principal de Streamlit se bloquea hasta que se actualiza la página
b) El callback `can_use_tool` (construido por `build_can_use_tool()`) bloquea el hilo worker de la sesión en `PermissionManager.wait_for_decision()`, hasta que la interfaz lo resuelve o transcurre `approval_timeout_seconds`
c) Nada se bloquea; la herramienta se ejecuta y se revierte si se deniega
d) El subproceso del CLI termina y debe reiniciarse manualmente

### Q4. ¿Qué campos aplica en hash `CocoOptions.options_hash()`, y para qué se usa?

a) Todos los campos de `CocoOptions`; siempre reinicia el worker ante cualquier cambio
b) Solo los campos que afectan a lo que una herramienta puede hacer (por ejemplo `allowed_tools`, `disallowed_tools`, `permission_mode`, `require_approval_for`, `add_dirs`); `CocoSession` reinicia su worker solo cuando este hash cambia
c) Solo `connection` y `cwd`, usados puramente para logging
d) Un hash de toda la transcripción, usado para cachear respuestas

### Q5. ¿Por qué `app_viewer()` nunca importa `copilot_rail()` (y viceversa)?

a) Son mutuamente incompatibles y no pueden usarse en la misma app
b) El componente de vista previa se mantiene agnóstico del anfitrión — no conoce las colas de trabajos; una app anfitriona compone ambos y conecta `on_fix` ella misma
c) `copilot_rail()` quedó obsoleto en favor de `app_viewer()`
d) Un bug de importación circular aún no se ha corregido

### Q6. ¿Qué familias de herramientas están tratadas como caso especial en `permissions.py` para crear siempre una solicitud de aprobación nueva, ignorando cualquier "always allow" previo?

a) La herramienta SQL y Write
b) `AskUserQuestion` y `ExitPlanMode`
c) Grep y Glob
d) Edit y Read

### Q7. ¿Qué mensaje transporta `SnowflakeConfigNotFoundError`?

a) "CoCo CLI not found on PATH"
b) "No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml)..."
c) "Approval timed out for tool {tool_name}"
d) "cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]"

### Q8. ¿Qué excepción se lanza cuando se encuentra un binario `cortex` en una ruta configurada pero no responde correctamente a `--version`?

a) `CLINotFoundError`
b) `CLIProbeError`
c) `CocoConnectionError`
d) `SessionStartError`

### Q9. ¿En qué se diferencia `SessionStartError` de `SessionNotReadyError`?

a) Son la misma excepción bajo dos nombres
b) `SessionStartError` cubre un worker que falla al arrancar; `SessionNotReadyError` cubre un timeout de conexión o un fallo de arranque una vez que el worker ya está en marcha
c) `SessionStartError` se usa solo para `query()` headless
d) `CocoConnectionError` reemplaza a ambas

### Q10. ¿Qué hace el kwarg `context=` de `wrap_exception()`?

a) Es puramente cosmético y no afecta a qué tipo de error se lanza
b) Guía el mapeo por detección de mensaje (por ejemplo `"session_start"`, `"session_ready"`/`"session"`, `"query"`, `"approval"`) hacia la subclase `CocoError` correcta según dónde ocurrió la excepción en bruto
c) Define la clave de sesión de Streamlit
d) Registra la excepción en un servidor remoto

### Q11. ¿Qué cubre `CwdUploadError`?

a) Solo subidas de tamaño excesivo
b) Nombres de archivo incorrectos (protección contra path-traversal), extensiones no permitidas, payloads de tamaño excesivo, y conflictos de sobrescritura
c) Solo fallos de conexión de Snowflake durante la subida
d) Solo discordancias de extensión, nunca de tamaño

### Q12. ¿Qué excepción es también un `TimeoutError`, además de un `CocoError`?

a) `SessionNotReadyError`
b) `ApprovalTimeoutError`
c) `CLIProbeError`
d) `QueryError`

### Q13. En el modelo de amenazas STRIDE, ¿qué severidad se asigna a la inyección de prompt que dispara herramientas peligrosas, y qué la mitiga?

a) Severidad baja; mitigado por saneamiento de entrada
b) Severidad alta; mitigado por puertas de aprobación (`PermissionManager` intercepta antes de la ejecución), recomendándose además un rol de mínimo privilegio
c) Severidad crítica; mitigado deshabilitando todas las herramientas por defecto
d) Severidad media; mitigado por limitación de tasa

### Q14. ¿Qué severidad y mitigación aplican al riesgo de escalada de "Always allow"?

a) Severidad alta; mitigado exigiendo reintroducir una contraseña
b) Severidad media; mitigado por el alcance — solo por herramienta, por sesión, borrado al reiniciar o al hacer reset
c) Severidad baja; sin mitigación aplicada
d) Severidad alta; mitigado por un registro de auditoría persistente (ya lanzado)

### Q15. ¿Cuál es el estado del riesgo de repudio (sin registro persistido de acciones destructivas aprobadas)?

a) Resuelto en `0.1.8`
b) Abierto, severidad media, rastreado como SEC-01 — la transcripción solo existe en el estado de sesión de Streamlit, no se escribe nada duradero
c) No es un riesgo reconocido en el modelo de amenazas
d) Mitigado por el escaneo de CodeQL

### Q16. ¿Cómo se mitiga el riesgo de divulgación de información de secretos que aparecen en la transcripción/logs?

a) La librería cifra la transcripción en reposo
b) La librería no registra credenciales, y el SDK las redacta de su salida
c) No se mitiga; es un elemento abierto
d) Deshabilitando la transcripción por completo

### Q17. ¿Qué riesgo de cadena de suministro señala el modelo de amenazas, y cómo se mitiga?

a) Elevación de privilegios mediante una dependencia comprometida; mitigado por `pip-audit` en CI y el escaneo de Gitleaks, con `uv.lock` confirmado para builds reproducibles
b) Inyección SQL en las llamadas a herramientas del agente; mitigado por consultas parametrizadas
c) Secuestro de sesión; mitigado rotando claves de API
d) Suplantación de DNS del registro de PyPI; mitigado por certificate pinning

### Q18. Según la orientación de "Roles and grants", ¿por qué se desaconseja conectar con `ACCOUNTADMIN` (o un grant como `MANAGE WAREHOUSES`), incluso con puertas de aprobación en su lugar?

a) Las puertas de aprobación controlan si una sentencia se ejecuta, no qué puede tocar una vez aprobada — los permisos SQL efectivos son exactamente los grants del rol conectado
b) Las sesiones `ACCOUNTADMIN` son técnicamente incompatibles con el CLI de CoCo
c) La librería bloquea activamente las conexiones `ACCOUNTADMIN`
d) `MANAGE WAREHOUSES` deshabilita por completo el flujo de aprobación

### Q19. ¿Cuáles de estos quedan explícitamente fuera de alcance para el pack de guías de este producto, según la decisión de alcance de los módulos de forma? (Opción múltiple — selecciona todas las que apliquen)

a) Un capítulo de referencia de Skills para `.cortex/skills/*/SKILL.md` en la raíz del repositorio
b) Un capítulo `reference-procedures` para objetos de Snowflake
c) Un capítulo de despliegue de Native App
d) Un capítulo `reference-commands` para los objetivos del Makefile
e) Un capítulo `reference-api` para la API de Python
f) Un capítulo de catálogo de controles (archivos de reglas / rúbrica de puntuación)

### Q20. ¿Qué objetivos de despliegue considera el modelo de amenazas, y cuáles se lanzan realmente hoy?

a) Local, SiS y SPCS se lanzan todos hoy
b) Solo SiS se lanza hoy; local y SPCS son solo alcance del modelo de amenazas
c) Local, SiS y SPCS se consideran todos en el modelo de amenazas, pero solo local se lanza realmente hoy
d) Solo SPCS se lanza hoy

### Q21. ¿Por qué omite el pack de guías un capítulo de "Infrastructure as code"?

a) Existen archivos Terraform pero se dejaron sin documentar
b) No hay ningún archivo `*.tf` en este repositorio
c) IaC queda fuera de alcance solo por motivos de seguridad
d) Está planeado para una versión futura y diferido intencionalmente

### Q22. ¿Por qué trata `reference-examples` cada una de las tres apps de ejemplo como una sola sección, en lugar de documentar cada página interna de Streamlit de cada app?

a) Ir página por página para tres apps de ejemplo repetiría los README de los ejemplos ya enlazados, así que cada app recibe un H2 en lugar de varios
b) Las páginas de Streamlit no pueden documentarse en Markdown
c) Solo `chat_app.py` tiene más de una página
d) La documentación a nivel de página se genera automáticamente y no requiere redacción

### Q23. ¿Qué es `text_renderer` como punto de extensión?

a) Un parámetro obligatorio sin valor por defecto, usado para seleccionar el warehouse de Snowflake
b) Una opción de renderizado de texto conectable en `panel()` (y helpers de visualización relacionados) — un nombre preestablecido (`"markdown"`, `"write"`, `"text"`, `"caption"`, `"code"`) o un callable
c) Un flag de CLI para `make chat`
d) Un archivo YAML que define los colores de la transcripción

### Q24. ¿Cómo decide la librería cómo renderizar la tarjeta de una herramienta desconocida o provista por MCP?

a) Se niega a renderizar nada para herramientas que no reconoce
b) Mediante despacho por nombre de herramienta (`tool_family(name)` en `tool_names.py`) que mapea un nombre de herramienta a un `ToolFamily`, con `tool_cards.py`/`tool_extract.py` gestionando el renderizado por familia
c) Siempre renderiza JSON en bruto para herramientas no reconocidas, sin lógica de despacho
d) Cada herramienta debe registrarse primero en `CocoOptions.allowed_tools` antes de poder renderizarse

### Q25. ¿Cómo permite App Builder que un "type" aporte su propia guía de CoCo a un trabajo de generación?

a) Codificando los prompts directamente dentro de `streamlit_coco`
b) Cada carpeta `types/<id>/` puede incluir un `SKILL.md` (+ `reference/`, `CHECKLIST.md`) montado vía `add_dirs`, junto con `types/shared/SKILL.md` para las reglas que aplican a todo type
c) Llamando a una API REST alojada fuera del repositorio
d) Escribiendo directamente en `streamlit_coco/tool_names.py`

### Q26. ¿Qué decide si el paso de perfilado de un type de App Builder es un parser determinista o un trabajo de CoCo?

a) La versión de Streamlit instalada
b) El `grounding_kind` del type (`tabular`, `semantic_view`, `documents`, o `urls`) — el grounding `tabular` usa un parser pandas determinista (`engine/profile.py`); los demás tipos pasan por CoCo
c) Si el usuario está en la página Admin
d) El `permission_mode` global definido para la app

### Q27. ¿Quién obtiene las fuentes de grounding de "documents" o "urls" de App Builder — la sesión de CoCo o la app anfitriona?

a) La sesión de CoCo, mediante una herramienta de red concedida
b) La aplicación anfitriona — los documentos/URLs los obtiene el anfitrión, nunca la sesión de CoCo, ya que no se le concede ninguna herramienta de red
c) Ninguno; las fuentes de grounding deben descargarse manualmente antes de cada ejecución
d) Una función externa separada

### Q28. Un colega pregunta por qué el repositorio no necesita un capítulo `reference-commands` de flags de CLI como lo tendría una herramienta CLI típica. ¿Cuál es la explicación correcta?

a) La librería no expone ningún comando en absoluto
b) La superficie principal del producto es una librería Python (la API), no un CLI — los objetivos del Makefile se documentan como `reference-commands` para ejecutar las demos, mientras que la referencia propia de la librería es la superficie de la API, tratada como el análogo de "Commands"
c) La documentación de CLI se oculta intencionalmente a los clientes
d) La documentación propia del CLI de CoCo reemplaza por completo la necesidad de cualquier referencia local

### Q29. Dos repositorios están involucrados en el lanzamiento a PyPI hoy. ¿Cuál es el arreglo actual (temporal), y por qué?

a) Los releases se etiquetan y publican directamente desde `DevoteamSP/streamlit-coco-dev`
b) Los tags en `lletourmy/streamlit-coco` (una superficie de release pública temporal) disparan la publicación en PyPI, hasta que `DevoteamSP/streamlit-coco` esté validado para PyPI y la configuración de Trusted Publisher se traslade allí
c) Los releases de PyPI son subidas manuales sin etiquetado de repositorio involucrado
d) `DevoteamSP/streamlit-coco` ya es el repositorio de publicación; `-dev` es solo para seguimiento de issues

### Q30. Enseñando a un nuevo miembro del equipo el flujo de release: ¿qué paso viene inmediatamente después de que `DRY_RUN=1 make sync-release` se vea correcto?

a) `git push --tags` directamente en el repositorio `-dev`
b) `COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release`, luego etiquetar `vX.Y.Z` en `lletourmy/streamlit-coco` (no en `-dev`)
c) Ejecutar `make publish` inmediatamente desde el checkout `-dev`
d) Saltar directamente a `pip install streamlit-coco==X.Y.Z` para verificar

## Answer Key

| P | Respuesta | Explicación |
|---|--------|-------------|
| 1 | **b** | `CocoSession` posee un `threading.Thread` llamado `coco-session` que ejecuta un bucle asyncio envolviendo `CortexCodeSDKClient`. |
| 2 | **a** | Los símbolos headless principales se importan sin cargar Streamlit; los exports de la interfaz se resuelven de forma perezosa mediante `__getattr__`/`_LAZY_ATTRS`, que es lo que permite que `headless_pipeline.py` funcione sin Streamlit instalado. |
| 3 | **b** | `can_use_tool` bloquea el hilo worker en `PermissionManager.wait_for_decision()` hasta que se resuelve o transcurre `approval_timeout_seconds`. |
| 4 | **b** | `options_hash()` aplica hash solo a los campos que afectan a los permisos de herramienta; el worker se reinicia solo cuando ese hash cambia, no en cada edición de opciones. |
| 5 | **b** | Este es un invariante documentado: el componente de vista previa se mantiene agnóstico del anfitrión y no conoce las colas de trabajos. |
| 6 | **b** | `permissions.py` trata como caso especial a `AskUserQuestion` y `ExitPlanMode` para crear siempre una solicitud nueva, sin importar un "always allow" previo. |
| 7 | **b** | Este es el texto exacto del mensaje de `SnowflakeConfigNotFoundError`. |
| 8 | **b** | `CLIProbeError` significa específicamente que el binario existe pero no respondió a `--version`; `CLINotFoundError` cubre el caso de no estar en PATH. |
| 9 | **b** | `SessionStartError` es un error de worker que falla al arrancar; `SessionNotReadyError` cubre el timeout/fallo de arranque una vez iniciado. |
| 10 | **b** | `context=` (`"session_start"`, `"session_ready"`/`"session"`, `"query"`, `"approval"`) guía hacia qué subclase `CocoError` mapea la detección de mensaje. |
| 11 | **b** | `CwdUploadError` se lanza igualmente por nombres incorrectos, extensiones no permitidas, payloads de tamaño excesivo y conflictos de sobrescritura. |
| 12 | **b** | `ApprovalTimeoutError` está documentado como también `TimeoutError`. |
| 13 | **b** | La inyección de prompt se califica de severidad alta; las puertas de aprobación que interceptan antes de la ejecución son la mitigación principal, junto con la recomendación de un rol de mínimo privilegio. |
| 14 | **b** | La escalada de "Always allow" es de severidad media, mitigada puramente por su alcance por herramienta/por sesión. |
| 15 | **b** | El repudio es de severidad media, abierto como SEC-01 — no se escribe nada duradero fuera del estado de sesión en memoria. |
| 16 | **b** | La mitigación es que la librería nunca registra credenciales y el SDK las redacta de su propia salida. |
| 17 | **a** | El riesgo señalado es la elevación de privilegios mediante una dependencia comprometida; la mitigación es `pip-audit`, Gitleaks, y un `uv.lock` confirmado. |
| 18 | **a** | Las puertas de aprobación solo deciden si una sentencia se ejecuta; una vez aprobada, su alcance está limitado únicamente por los grants reales del rol conectado. |
| 19 | **A, B, C, F** | Skills, procedimientos de Snowflake, Native App y un catálogo de controles figuran todos como "no activados" / fuera de alcance; commands y la referencia de la API sí se activaron y están documentados. |
| 20 | **c** | El modelo de amenazas considera local/SiS/SPCS, pero solo local se lanza realmente; SiS/SPCS son solo alcance del modelo de amenazas y de la hoja de ruta. |
| 21 | **b** | El motivo de alcance dado es simplemente que no existe ningún archivo `*.tf` en ningún lugar del repositorio. |
| 22 | **a** | La decisión de alcance explícita es un H2 por app de ejemplo, para evitar repetir los README de los ejemplos página por página. |
| 23 | **b** | `text_renderer` acepta un nombre preestablecido o un callable en `panel()` y los helpers de visualización relacionados. |
| 24 | **b** | El despacho `tool_family(name)` en `tool_names.py` mapea nombres de herramienta a un `ToolFamily`, consumido por `tool_cards.py`/`tool_extract.py` para el renderizado. |
| 25 | **b** | Cada carpeta de type puede llevar su propio `SKILL.md` (+ reference/checklist), montado vía `add_dirs`, más un `types/shared/SKILL.md` compartido. |
| 26 | **b** | `grounding_kind` decide: `tabular` usa el parser determinista `engine/profile.py`, los demás tipos pasan por CoCo. |
| 27 | **b** | Los documentos/URLs los obtiene la app anfitriona; a la sesión de CoCo no se le concede ninguna herramienta de red. |
| 28 | **b** | La superficie principal de la librería es la API de Python, no un CLI; los objetivos del Makefile reciben `reference-commands` para las demos, mientras que la API es el propio análogo de "Commands" de la librería. |
| 29 | **b** | `lletourmy/streamlit-coco` es la superficie de release pública temporal etiquetada para la publicación en PyPI, hasta que `DevoteamSP/streamlit-coco` esté validado para PyPI. |
| 30 | **b** | Tras un dry run limpio, el siguiente paso documentado es la sincronización confirmada/enviada, y luego etiquetar `vX.Y.Z` en `lletourmy/streamlit-coco`, nunca en `-dev`. |
