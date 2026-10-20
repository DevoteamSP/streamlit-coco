# Quiero añadir subida de archivos

**Para** un desarrollador que permite a los usuarios entregar archivos al
agente · **10 min** · **una app mínima funcional**

Terminas con una forma de que el usuario de la app suba archivos al
directorio de trabajo del agente, ya sea desde la barra de entrada del
chat o un uploader dedicado en la barra lateral.

## Antes de empezar

- Una app mínima funcional
  ([Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)).
- Decide el directorio de destino: las subidas aterrizan bajo
  `CocoOptions.cwd` en un subdirectorio (`_uploads` por defecto).

## Pasos

1. Para aceptar archivos directamente desde la barra de entrada del chat,
   define `accept_file` en `chat_input_bar()`:

   ```python
   prompt = st_coco.chat_input_bar(
       session,
       accept_file=True,           # o "multiple"
       upload_subdir="_uploads",
       upload_overwrite="replace",  # "error" / "replace" / "skip"
   )
   ```

   Con `inject_upload_paths=True` (el valor por defecto), las rutas de
   los archivos subidos se añaden al texto del prompt enviado al agente.

2. Para ofrecer un uploader independiente (por ejemplo en una barra
   lateral), usa `cwd_uploader()` en su lugar:

   ```python
   with st.sidebar:
       uploaded = st_coco.cwd_uploader(
           session,
           label="Upload a reference file",
           overwrite="error",
       )
   ```

   `cwd_uploader()` envuelve `st.file_uploader` y llama a
   `upload_to_cwd()` por ti, y muestra una leyenda listando lo que ya hay
   en el directorio de subidas.

3. Para subir archivos completamente fuera de un widget de Streamlit (por
   ejemplo archivos ya leídos en memoria), llama directamente a
   `upload_to_cwd()`:

   ```python
   from streamlit_coco import upload_to_cwd

   paths = upload_to_cwd(
       session,                 # o un CocoOptions, o una ruta en bruto
       files,
       subdir="_uploads",
       overwrite="error",
   )
   ```

## Resultado

Los archivos subidos se escriben bajo `<CocoOptions.cwd>/_uploads/` (o el
`subdir`/`upload_subdir` que definas), y quedan disponibles para
cualquier herramienta del agente que lea desde `cwd`. `cwd_uploader()` y
`upload_to_cwd()` devuelven ambos la lista de resultados `UploadedPath`
para los archivos que se acaban de escribir.

## Variaciones

- `upload_to_cwd()` tiene por defecto `overwrite="error"` (rechaza un
  choque de nombres); `chat_input_bar()` fija por defecto
  `upload_overwrite="replace"` — define cualquiera de los dos
  explícitamente si el valor por defecto de tu punto de entrada no es el
  que quieres.
- El tamaño y la extensión del archivo se comprueban contra
  `DEFAULT_MAX_BYTES` (10 MiB) y una lista fija de extensiones
  permitidas de documentos/datos seguros
  (`streamlit_coco.upload.DEFAULT_ALLOWED_EXTENSIONS`) a menos que pases
  tu propio `max_bytes` / `allowed_extensions`.

## Si falla

- [Subida rechazada: extensión](../../technical-guide/help.html#upload-rejected-extension)
- [Subida rechazada: tamaño](../../technical-guide/help.html#upload-rejected-size)
- [Conflicto de nombre en la subida](../../technical-guide/help.html#upload-name-conflict)
