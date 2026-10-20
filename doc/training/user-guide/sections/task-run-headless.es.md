# Quiero ejecutar CoCo en modo headless

**Para** un desarrollador que orquesta CoCo desde un trabajo de CI o una
terminal · **15 min** · **una terminal, sin interfaz de Streamlit
necesaria**

Terminas con un script que impulsa al agente sin importar Streamlit, ya
sea para un solo turno o una sesión de varios turnos, resolviendo
cualquier aprobación en código.

## Antes de empezar

- `streamlit-coco[sdk]` instalado; `check_environment().ready` es `True`
  para la conexión que vas a usar (ver [Primeros pasos](getting-started.html)).
- Los símbolos headless principales (`CocoSession`, `query`,
  `CocoOptions`, los tipos de permisos y errores) se importan sin cargar
  Streamlit — los exports de la interfaz se resuelven de forma perezosa,
  así que un simple `import streamlit_coco` es seguro en un script que
  nunca toca Streamlit.

## Pasos

1. Para un solo turno, usa `query()`:

   ```python
   import asyncio
   import streamlit_coco as st_coco

   async def main() -> None:
       options = st_coco.CocoOptions(connection="my_connection")
       async for event in st_coco.query("Summarize sales by region.", options=options):
           if event.type == "assistant_text":
               print(event.text)

   asyncio.run(main())
   ```

2. Para una sesión de varios turnos sin ninguna interfaz, impulsa
   `CocoSession` directamente:

   ```python
   session = st_coco.CocoSession(options=options, key="headless")
   session.start()
   await session.ensure_ready(timeout=120)
   result = await session.run("List the tables in my schema.")
   async for event in session.stream():
       ...
   session.close()
   ```

3. Resuelve las aprobaciones en código en lugar de en una interfaz —
   comprueba `session.chat_result().pending_approval` tras una ejecución
   y llama a `approve_pending()` / `deny_pending()` como se muestra en
   [Quiero configurar aprobaciones de herramientas](task-configure-tool-approvals.html),
   o pre-aprueba todo lo que esperas vía `allowed_tools` para que el
   script nunca se bloquee.

4. Convierte los eventos acumulados en una tabla cuando necesites
   inspeccionarlos o registrarlos en bloque:

   ```python
   df = st_coco.events_to_dataframe(session.events)  # necesita pandas
   ```

## Resultado

`query()` produce objetos `CocoEvent` para un solo turno y no devuelve
nada más — no queda ningún objeto de sesión que conservar después.
`CocoSession` ejecutada fuera de Streamlit se comporta exactamente igual
que dentro de un `panel()`: la misma transcripción, las mismas
transiciones de `CocoRunStatus`, las mismas pausas de aprobación — solo
falta el renderizado.

## Variaciones

- `examples/headless_pipeline.py` (`make headless`) muestra tanto
  `query()` como `CocoSession` desde un script de terminal simple, cada
  uno en su propio bucle de eventos.
- `query()` lanza `SDKNotInstalledError` o `QueryError` (u otra subclase
  de `CocoError`) en lugar de devolver un resultado parcial en caso de
  fallo — envuelve la llamada en consecuencia para un trabajo de CI.

## Si falla

- [`SDKNotInstalledError`](../../technical-guide/help.html#sdk-not-installed)
- [Sesión no lista](../../technical-guide/help.html#session-not-ready)
