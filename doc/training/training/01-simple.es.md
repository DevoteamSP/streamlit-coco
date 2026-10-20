# Caso 1 — Simple: el patrón preferido, guiado

**Nivel:** Simple — totalmente guiado, datos de muestra. **Tiempo:** 20–30
min.

## Contexto

Toda integración de `streamlit-coco` parte de la misma forma: tú posees la
página Streamlit, CoCo posee la sesión. `examples/chat_app.py` es la
referencia funcional incluida para esa forma — las mismas cuatro llamadas
que muestra el [quickstart del README](../../../README.md#quickstart) de
forma aislada: `check_environment()`, `render_start_gate()`,
`get_or_create_session()`, y `panel()` + `chat_input_bar()`.

## Objetivo

Ejecutar la app de referencia incluida, identificar cada una de las cuatro
llamadas en el código fuente y ejercitar tanto un turno de solo lectura
como uno protegido por aprobación — de modo que puedas señalar cualquier
línea de `chat_app.py` y decir qué hace.

## Datos

**Suministrados.** No es necesario crear ningún objeto de Snowflake:
`SNOWFLAKE_SAMPLE_DATA` (incluido en cualquier cuenta de Snowflake con
datos de muestra habilitados), en concreto el esquema `TPCH_SF1`, es de
solo lectura y está disponible por defecto. También se suministra un
conjunto curado de prompts en `examples/testdata/prompts.json`, navegable
desde el interruptor **Test prompts** de la barra lateral en `make chat`.

## Pasos

1. Confirma que tu entorno está listo — la
   [lista de verificación de configuración](../enablement/setup.html)
   debería estar completamente marcada antes de empezar.
2. Ejecuta `make chat`. Esto lanza `examples/chat_app.py`.
3. Abre `examples/chat_app.py` en un editor junto a la pestaña del
   navegador. Encuentra y lee, en orden:
   - `env = st_coco.check_environment(connection=connection)` — sondea SDK,
     CLI y configuración de Snowflake sin iniciar un agente.
   - `st_coco.render_start_gate(opts, session_key=SESSION_KEY,
     gate_key=GATE_KEY, env=env)` — la pantalla de aterrizaje; devuelve
     `False` hasta que haces clic en **Start CoCo Chat**.
   - `session = st_coco.get_or_create_session(opts, key=SESSION_KEY)` —
     obtiene o crea el worker en segundo plano, almacenado en
     `st.session_state`.
   - `st_coco.panel(session=session, ...)` seguido de
     `st_coco.chat_input_bar(session, ...)` — la interfaz de
     transcripción/salida y el cuadro de entrada.
4. En el navegador, haz clic en **Start CoCo Chat** si aún no lo has
   hecho.
5. Escribe: *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
   Observa cómo la transcripción se transmite de forma progresiva en lugar
   de aparecer toda de golpe, y fíjate en la tarjeta de herramienta que
   aparece.
6. Escribe: *"Create a summary table called TOP_CUSTOMERS in my schema."*
   Aparece un banner de aprobación con **Approve once**, **Always allow**,
   **Deny**. Haz clic en **Deny** con un motivo — confirma que el agente lo
   reconoce y no crea la tabla.

## Resultado esperado

- La transcripción del paso 5 se renderiza de forma progresiva, con al
  menos una tarjeta de herramienta visible (normalmente SQL o Glob).
- La transcripción del paso 6 se pausa en un banner de aprobación antes de
  crear ninguna tabla; denegarla no deja ningún objeto nuevo en tu
  esquema.
- Puedes nombrar, de memoria, cuál de las cuatro llamadas en
  `chat_app.py` produjo la puerta de inicio, la sesión y el panel.

## Dónde mirar si te atascas

- Si la app nunca sale de la puerta de inicio o la transcripción nunca
  empieza a transmitirse:
  [`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting)
  y
  [`help.html#coco-connection-error`](../technical-guide/help.html#coco-connection-error).
- Si no aparece ningún banner de aprobación para la solicitud
  `CREATE TABLE`, revisa de nuevo `require_approval_for` en las píldoras
  **Requires approval** de la barra lateral de `chat_app.py`, o el paso de
  comprobación del entorno de la lista de verificación de configuración.
