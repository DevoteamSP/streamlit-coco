# Caso 3 — Avanzado: una sesión que nunca conecta

**Nivel:** Avanzado — algo se rompe, diagnosticas solo. **Tiempo:** 30–45
min.

## Contexto

Este caso se basa en un síntoma documentado en las propias referencias de
resolución de problemas de la librería (no es hipotético): una sesión que
arranca correctamente la interfaz pero nunca sale del estado de conexión.
No se te dirá la causa raíz de antemano — el mismo síntoma puede venir de
más de una capa de la pila, y parte del ejercicio consiste en averiguar
cuál.

## Objetivo

Diagnosticar, sin que te digan la causa, por qué una sesión de CoCo no
llega a estar lista — y arreglarlo — usando las mismas herramientas que
`check_environment()` usa internamente, no conjeturas.

## Datos

**Tu propio entorno local.** No se necesitan objetos especiales de
Snowflake; este es un diagnóstico puramente de entorno/conectividad. Usa
la app de ejemplo que ya tengas funcionando de ejercicios anteriores
(`examples/chat_app.py` vía `make chat`, o tu propia app del
[Caso 1](01-simple.html) / [Caso 2](02-intermediate.html)).

## Síntomas

Esto es todo lo que se te da. No asumas la causa solo a partir de esta
lista — confírmala.

- Ejecutas `make chat` (o tu propia app construida sobre el patrón
  quickstart).
- La puerta de inicio se renderiza con normalidad y muestra su sonda
  SDK/CLI/Snowflake.
- Haces clic en **Start CoCo Chat**.
- La línea de estado del panel se queda en un estado de conexión; el área
  de transcripción muestra un persistente "Starting CoCo…" y nunca
  avanza.
- El campo de entrada del chat permanece deshabilitado.
- No aparece ningún banner de error en la propia interfaz.

## Pasos

1. **Reprodúcelo.** Si tu propio entorno no muestra actualmente este
   síntoma, aun así puedes seguir el método de diagnóstico de abajo — el
   objetivo es el método, no necesariamente forzar una reproducción en
   vivo.

2. **Activa la salida de depuración.** Define `STREAMLIT_COCO_DEBUG=1` (o
   `COCO_DEBUG=1`) y vuelve a ejecutar. Lee la terminal, no solo el
   navegador — busca cualquier cosa impresa después de "Starting CoCo…".

3. **Saltate la interfaz.** En una shell de Python, llama a
   `check_environment()` directamente con el mismo valor `connection=` que
   usa tu app, e imprime cada campo: `sdk_installed`, `sdk_version`,
   `cli_path`, `cli_version`, `snowflake_config_file`, `connection_hint`.
   No te detengas en el primer campo que parezca incorrecto — léelos
   todos; puede haber más de uno mal a la vez.

4. **Relaciona lo que encontraste con un error tipado.**
   `streamlit_coco.errors` define una clase de excepción por cada capa de
   fallo (SDK ausente, CLI no encontrado, CLI presente pero sin responder,
   sin configuración de Snowflake, conexión/autenticación incorrecta,
   sesión que nunca llega a estar lista). Para cada campo que pareciera
   incorrecto en el paso 3, averigua cuál de esas clases habría lanzado
   `require_environment()` en lugar de la sonda silenciosa de
   `check_environment()` — ese es tu diagnóstico.

5. **Arregla la capa específica que encontraste**, luego repite la ruta
   de reproducción (puerta de inicio → **Start CoCo Chat**) y confirma
   que la sesión ahora llega a un estado listo y responde a un prompt.

## Resultado esperado

- Puedes nombrar la capa específica que estaba rota (SDK, CLI en `PATH`,
  CLI respondiendo a `--version`, configuración de Snowflake presente, o
  conexión/autenticación) usando los propios campos de
  `check_environment()`, no por ensayo y error en la interfaz.
- Después de la corrección, la misma ruta de reproducción abandona el
  estado de conexión, el campo de entrada del chat se habilita y un
  prompt devuelve una respuesta normal en streaming con una tarjeta de
  herramienta.

## Dónde mirar si te atascas

Empieza aquí, luego ramifícate según lo que te haya dicho
`check_environment()`:

- [`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting)
  — el síntoma general y cómo leer la salida de depuración.
- [`help.html#coco-connection-error`](../technical-guide/help.html#coco-connection-error)
  — si `check_environment()` alcanzó el CLI pero la conexión/autenticación
  es incorrecta.
- [`help.html#cli-not-found`](../technical-guide/help.html#cli-not-found) /
  [`help.html#cli-probe-failed`](../technical-guide/help.html#cli-probe-failed)
  — si `cli_path` o `cli_version` parecían incorrectos.
- [`help.html#snowflake-config-not-found`](../technical-guide/help.html#snowflake-config-not-found)
  — si `snowflake_config_file` estaba vacío.
- [`help.html#session-not-ready`](../technical-guide/help.html#session-not-ready)
  — si todos los campos de `check_environment()` parecían correctos pero
  la sesión sigue sin llegar a estar lista.
