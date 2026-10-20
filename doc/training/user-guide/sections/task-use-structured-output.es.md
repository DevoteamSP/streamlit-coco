# Quiero usar salida estructurada

**Para** un desarrollador que renderiza la salida del agente en un widget
en lugar de texto de chat · **15 min** · **una app mínima funcional**

Terminas con una sesión que devuelve JSON conforme a un esquema que tú
defines, dirigido a tu propio widget en lugar de a la transcripción.

## Antes de empezar

- Una app mínima funcional
  ([Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)).
- Un JSON Schema que describa la forma que quieres recibir. No incluyas
  las claves `$schema` ni `$id` — la librería las elimina antes de pasar
  el esquema al SDK, pero un esquema redactado en otro lugar (por ejemplo
  un archivo de contrato compartido) puede seguir llevándolas.

## Pasos

1. Define `output_schema` en `CocoOptions`:

   ```python
   options = st_coco.CocoOptions(
       connection="my_connection",
       output_schema={
           "type": "object",
           "properties": {
               "status": {"type": "string"},
               "count": {"type": "integer"},
           },
           "required": ["status", "count"],
       },
   )
   ```

2. Gestiona el payload estructurado a medida que llega, ya sea con un
   callback o leyéndolo de vuelta después del turno:

   ```python
   def on_structured(payload: dict, result: st_coco.CocoChatResult) -> None:
       st.metric("Count", payload["count"])

   st_coco.panel(session, on_structured_output=on_structured)
   ```

   O lee `session.structured_output` /
   `session.chat_result().structured_output` después de que un turno se
   complete, sin un callback.

3. Opcionalmente, dale al renderizado estructurado su propio contenedor en
   lugar de dejar que aparezca en línea en la transcripción:

   ```python
   box = st.container()
   st_coco.panel(session, structured_output_container=box)
   ```

4. Para una llamada headless puntual, pasa `output_schema` directamente a
   `query()` en lugar de a través de `CocoOptions` — ver
   [Quiero ejecutar CoCo en modo headless](task-run-headless.html).

## Resultado

Cuando el resultado final del agente lleva un payload estructurado,
`panel()` (o tu callback `on_structured_output`) lo recibe como un `dict`
de Python conforme a tu esquema, y
`session.chat_result().structured_output` contiene el mismo valor. Si el
turno no produce ningún payload estructurado, ambos permanecen `None` — la
transcripción sigue mostrando la respuesta en texto plano.

## Variaciones

- `structured_output.py` demuestra el flujo completo — ejecútalo con
  `make structured` (ver
  [Referencia de apps de ejemplo](reference-examples.html)).
- `request_input(question, schema=...)` es un mecanismo diferente:
  recoge una respuesta estructurada del *usuario* entre turnos, no del
  agente — ver [Referencia de la API](reference-api.html).

## Si falla

- [`no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`](../../technical-guide/help.html#schema-dollar-schema-rejected)
- [Salida estructurada que no se renderiza](../../technical-guide/help.html#structured-output-not-rendering)
