# Primeros pasos

## Acceso y prerrequisitos

- Python >=3.10, un entorno virtual, y Streamlit >=1.55.
- Una cuenta de Snowflake con acceso a Cortex Code, y una conexión
  configurada en `~/.snowflake/connections.toml` (o el
  `~/.snowflake/config.toml` heredado). Esta librería nunca almacena ni
  registra credenciales por sí misma — la autenticación se delega al CLI
  de CoCo, al SDK, y a la configuración de Snowflake a nivel de sistema
  operativo.
- El CLI `cortex` accesible en `PATH`, o `CORTEX_CODE_CLI_PATH` definido
  con su ubicación.

La instalación y la configuración del CLI se cubren paso a paso en
Enablement [`setup.html`](../../enablement/setup.html) — sigue esa página
primero si aún no has instalado `streamlit-coco`. Esta página asume que la
instalación ya está hecha y continúa desde un checkout funcional.

## Primera ejecución

1. Confirma que el entorno está listo antes de escribir código de app
   alguno:

   ```python
   import streamlit_coco as st_coco

   env = st_coco.check_environment()
   print(env.ready, env.sdk_installed, env.cli_ok, env.snowflake_config_found)
   ```

   `check_environment()` nunca lanza una excepción — siempre devuelve un
   `CocoEnvironment`, así que un `False` aquí significa algo que corregir,
   no un fallo. Ver [Conceptos](concepts.html#cocoenvironment) y
   [Referencia de la API](reference-api.html) para cada campo.

2. Ejecuta la demo de primera parte para ver una app funcionando antes de
   escribir la tuya:

   ```bash
   make chat
   ```

   Esto ejecuta `examples/chat_app.py` — el patrón de integración
   preferido (`check_environment` → `render_start_gate` →
   `get_or_create_session` → `panel()` + `chat_input_bar()`) en su forma
   más pequeña y funcional. Los detalles y las demás apps de ejemplo están
   en [Quiero ejecutar las apps de ejemplo](task-run-the-example-apps.html).

3. Construye tu propia app mínima a partir del mismo patrón:
   [Quiero construir una app CoCo mínima](task-build-a-minimal-app.html).

## Estás listo cuando…

- `check_environment().ready` es `True` para la conexión que piensas usar.
- `make chat` abre una pestaña del navegador mostrando el panel de CoCo, y
  un prompt que escribes recibe una respuesta en streaming.
- Puedes señalar las cuatro llamadas del patrón preferido
  (`check_environment` → `render_start_gate` → `get_or_create_session` →
  `panel()`) en `examples/chat_app.py` y explicar qué hace cada una.

Si `check_environment()` reporta un problema, o la app se queda atascada
antes de que aparezca una respuesta, ver
[Preguntas frecuentes](faq.html) o
[`help.html`](../../technical-guide/help.html) en la Guía Técnica.
