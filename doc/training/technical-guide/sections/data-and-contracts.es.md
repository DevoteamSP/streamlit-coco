# Datos y contratos

## `CocoEvent`

`streamlit_coco/messages.py` define `CocoEvent`, el evento normalizado y
serializable a JSON que la librería produce a partir de mensajes
SDK/NDJSON. Cada evento lleva `to_dict()` / `CocoEvent.from_dict()` para
ida y vuelta.

Campos:

| Campo | Tipo | Notas |
|---|---|---|
| `type` | `str` | `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error` |
| `id` | `str` | UUID, generado por evento |
| `text` | `str \| None` | Texto de asistente/thinking |
| `delta` | `str \| None` | Delta de texto en streaming |
| `name` | `str \| None` | Nombre de herramienta (en eventos tool-use) |
| `tool_use_id` | `str \| None` | Correlaciona un resultado de herramienta con su evento tool-use |
| `input` | `dict \| None` | Entrada de la herramienta |
| `content` | `Any` | Payload de contenido en bruto |
| `is_error` | `bool \| None` | Flag de error del resultado de la herramienta |
| `request_id` | `str \| None` | Id de solicitud de permiso |
| `tool_name` | `str \| None` | Nombre de herramienta en eventos permission-request |
| `tool_input` | `dict \| None` | Entrada de la herramienta en eventos permission-request |
| `subtype` | `str \| None` | Subtipo del evento |
| `duration_ms` | `int \| None` | Duración del turno/herramienta, cuando el SDK la proporciona |
| `structured_output` | `Any` | Payload de salida estructurada, cuando está presente |
| `cost_usd` | `float \| None` | Coste, cuando el SDK lo proporciona |
| `message` | `str \| None` | Mensaje en texto libre (eventos system/error) |
| `code` | `str \| None` | Código de error |
| `metadata` | `dict` | Campos extra libres |

`events_to_dataframe(events)` (necesita `pandas`) aplana una lista de
`CocoEvent` en un `DataFrame` para inspección o registro.

## Contratos JSON Schema — `examples/bi_to_semantic/contracts/`

Tres archivos JSON Schema limitan las salidas estructuradas que el
ejemplo BI → Semantic pide a CoCo (y a sus propios parsers
deterministas) que produzca. Cada uno es un esquema draft 2020-12 con
`additionalProperties: false`:

| Archivo | Propósito |
|---|---|
| `estate_map.schema.json` | Forma de `estate_map.json` — tablas, columnas, joins, y uso por workbook descubierto en el estate de Tableau/Power BI |
| `kpi_inventory.schema.json` | Forma de `kpi_inventory.json` — nombres de métrica, los workbooks que los definen, sus definiciones, un flag de conflicto, y una descripción en inglés sencillo |
| `access_rules.schema.json` | Forma de `access_rules.json` — ramas y divergencias de reglas de acceso por workbook, en inglés sencillo |

Estos archivos no se reproducen aquí; léelos directamente bajo
`examples/bi_to_semantic/contracts/` al construir contra la forma que
imponen. Como llevan una URI de draft `$schema`, son exactamente el tipo
de archivo de contrato que dispara
[help.html#schema-dollar-schema-rejected](../help.html#schema-dollar-schema-rejected)
si se pasa a `CocoOptions.output_schema` sin modificar — la librería
elimina `$schema` / `$id` antes de reenviar al SDK, así que pasar estos
archivos tal cual a través de `CocoOptions.output_schema` es seguro; solo
quien llame y reimplemente esa eliminación necesita tener cuidado.

## `brief.json` / `BRIEF.md` de App Builder

Cada proyecto de App Builder bajo `examples/app_builder/out/<slug>/`
lleva:

- `brief.json` — el brief legible por máquina: id del type, contexto
  introducido por el propietario, las preguntas declaradas del type y
  sus respuestas.
- `BRIEF.md` — el mismo brief renderizado como Markdown, la forma que
  lee CoCo (montada vía `add_dirs`) al escribir o regenerar la app. Las
  acciones **Save** y **Save & regenerate** de la página Studio escriben
  `BRIEF.md` a partir del estado actual del formulario antes de encolar
  a CoCo — ver
  [help.html#app-builder-brief-overwrite-race](../help.html#app-builder-brief-overwrite-race)
  para el bug de orden que esto corrigió en `0.1.8`.
- `sketches/` — imágenes de boceto adjuntas opcionales para el brief.
- `streamlit_app.py` — la app consumidora generada (o el scaffold de
  demo), una vez construida.

No hay ningún archivo JSON Schema para `brief.json` en el repositorio; su
forma la define implícitamente la lista `brief.questions` de
`types/<id>/type.json` más los campos fijos de nivel superior que
escribe el motor de App Builder
(`examples/app_builder/engine/paths.py` localiza estos archivos bajo
`OUT_DIR = examples/app_builder/out/`).

## Contrato del subdirectorio de subida (`_uploads/`)

`upload_to_cwd()` (`streamlit_coco/upload.py`) escribe las subidas del
navegador bajo `<CocoOptions.cwd>/_uploads/` por defecto
(`DEFAULT_UPLOAD_SUBDIR = "_uploads"`). El contrato que aplica en cada
escritura:

- Los nombres de archivo se sanean a un basename únicamente
  (`sanitize_upload_name`) — los separadores de ruta y caracteres
  inseguros se eliminan; `.`/`..` y nombres vacíos se rechazan.
- El directorio de destino se resuelve y se comprueba que esté dentro de
  `cwd` (`subdir` debe ser relativo y no debe contener `..`).
- Lista de extensiones permitidas: `DEFAULT_ALLOWED_EXTENSIONS`, un
  frozenset fijo de extensiones de documento/dato seguras (ver la
  constante en `streamlit_coco/upload.py` para la lista exacta) —
  rechaza cualquier cosa fuera de ella a menos que quien llame pase su
  propio `allowed_extensions`.
- Límite de tamaño: `DEFAULT_MAX_BYTES = 10 * 1024 * 1024` (10 MiB) a
  menos que quien llame anule `max_bytes`.
- La política de sobrescritura es explícita por llamada: `"error"`
  (valor por defecto de `upload_to_cwd` — lanza `CwdUploadError` si el
  archivo existe), `"replace"` (valor por defecto del
  `upload_overwrite` de `chat_input_bar`), o `"skip"`.

Cada escritura exitosa devuelve un `UploadedPath` (`path`, `relative`,
`name`, `bytes_written`, `overwritten`, `skipped`).

## Versionado

No hay ningún esquema de versionado separado para `CocoEvent`, los JSON
Schemas de BI → Semantic, ni la forma del brief de App Builder. Todos
ellos versionan junto con el paquete: el campo `version` de
`pyproject.toml` y `CHANGELOG.md` son el único registro de cuándo cambió
la forma de un contrato (ver las entradas `Fixed` de `0.1.6` y `0.1.8`
en [help](../help.html) como ejemplos de correcciones adyacentes a
contratos). Un cambio incompatible en cualquiera de estas formas es un
evento de versión del paquete, no un esquema versionado de forma
independiente.
