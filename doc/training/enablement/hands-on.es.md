# Ejercicios prácticos

6 ejercicios progresivos usando las apps reales de `examples/`. Completa
primero la [lista de verificación de configuración](setup.html) y el
[recorrido guiado](guided-tour.html). Presupuesto: ~120–150 minutos en
total.

---

## Ejercicio 1 — Ejecutar el patrón preferido (`panel()` + `chat_input_bar()`)

**Objetivo**: Ver el patrón de integración recomendado de principio a fin y
entender la división de responsabilidades ("tú posees la página, CoCo
posee la sesión").

**Pasos**:

1. `make chat` (ejecuta `examples/chat_app.py`).
2. Abre `examples/chat_app.py` en un editor. Identifica las cuatro
   llamadas que componen el patrón: `check_environment()`,
   `render_start_gate()`, `get_or_create_session()`, `panel()` +
   `chat_input_bar()`.
3. En el navegador, escribe: *"What tables are available in
   SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
4. Observa cómo se transmite la transcripción y fíjate en la tarjeta de
   herramienta que aparece (probablemente una tarjeta SQL o Glob).

**Resultado esperado**: Una respuesta en streaming se renderiza de forma
progresiva (no toda de golpe), con al menos una tarjeta de herramienta que
muestra lo que hizo el agente.

**Resolución de problemas**: Si nada se transmite, confirma que
`check_environment(...).ready` era `True` en la lista de verificación de
configuración — una sesión atascada suele significar que el CLI o la
conexión no están bien. Ver
[`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting).

---

## Ejercicio 2 — Disparar y resolver una puerta de aprobación

**Objetivo**: Entender el modelo de seguridad human-in-the-loop — el
diferenciador clave de esta librería frente a una integración de agente
desnuda.

**Pasos**:

1. Todavía en `make chat`, escribe: *"Show me the top 5 customers by total
   order amount. Write the SQL and run it."*
2. Cuando aparezca el banner de aprobación, lee la sentencia SQL completa
   que se muestra.
3. Haz clic en **Approve once** — confirma que la consulta se ejecuta y los
   resultados aparecen en la transcripción.
4. Escribe: *"Now create a summary table called TOP_CUSTOMERS in my
   schema."*
5. Cuando la puerta de aprobación se dispare de nuevo, haz clic en **Deny**
   con un motivo (por ejemplo "not for this exercise") — confirma que el
   agente reconoce la denegación.

**Resultado esperado**: La ejecución SQL se pausa a la espera de
aprobación en ambas ocasiones; aprobar permite que se ejecute, denegar la
detiene y el agente adapta su siguiente respuesta.

**Resolución de problemas**: Si no aparece ninguna puerta de aprobación
para un `CREATE TABLE`, comprueba que `require_approval_for=["Edit",
"Write", "Bash"]` (o similar) está definido en `CocoOptions` — abre
`examples/chat_app.py` y confirma las píldoras **Requires approval** de la
barra lateral.

---

## Ejercicio 3 — Salida estructurada hacia un widget

**Objetivo**: Ver cómo la salida del agente puede impulsar tus propios
widgets de Streamlit en lugar de renderizarse solo como texto de chat.

**Pasos**:

1. Detén la demo anterior (Ctrl+C) y ejecuta `make structured`
   (`examples/structured_output.py`).
2. Abre el archivo y localiza la definición de `output_schema` y el
   callback `on_structured_output` pasado a `panel()`.
3. En el navegador, escribe: *"Give me a breakdown of orders by status."*
4. Confirma que la respuesta se renderiza como un gráfico/dataframe de
   Streamlit, no como texto JSON en bruto.

**Resultado esperado**: La respuesta estructurada del agente se dirige a
un widget que definiste, sin ningún parseo manual de JSON en el código de
tu app.

**Resolución de problemas**: Si se renderiza como texto plano en lugar de
un widget, es posible que la respuesta no coincida con `output_schema` —
prueba a reformular el prompt siendo más explícito sobre los campos que
quieres. Ver
[`help.html#structured-output-not-rendering`](../technical-guide/help.html#structured-output-not-rendering).

---

## Ejercicio 4 — Modo headless (sin interfaz Streamlit)

**Objetivo**: Confirmar que la misma librería funciona fuera de Streamlit —
para CI, scripts y trabajos por lotes.

**Pasos**:

1. Ejecuta `make headless` (`examples/headless_pipeline.py`).
2. Abre el archivo y observa: ningún import de `streamlit` en ningún
   sitio, la misma función `query()` usada para el flujo de eventos
   asíncrono.
3. Observa la salida de la terminal — los eventos se transmiten a medida
   que el agente trabaja, con los mismos tipos de evento
   (`assistant_text`, `tool_use`, `result`) que el modo con interfaz.

**Resultado esperado**: El script se ejecuta hasta completarse, imprimiendo
los eventos transmitidos enteramente desde la terminal — sin navegador
involucrado.

**Resolución de problemas**: Si se queda colgado, comprueba los mismos
prerrequisitos de entorno que el Ejercicio 1 (`check_environment`) — el
modo headless tiene la misma dependencia de CLI/conexión.

---

## Ejercicio 5 — Construir una app mínima desde cero

**Objetivo**: Demostrar que puedes reproducir el patrón sin copiar un
ejemplo existente — la verdadera prueba de estar "entrenado". Esta es una
situación real, no un ejercicio mecánico: te toparás con al menos uno de
los dos errores de permisos de herramienta que la gente realmente comete
con `CocoOptions`.

**Pasos**:

1. Crea un nuevo archivo `my_first_app.py` en la raíz del repositorio.
2. Usando el [quickstart del README](../../../README.md#quickstart) como
   única referencia (no copies `examples/chat_app.py` directamente),
   escribe una app que:
   - Use `connection="analytics"` (o el nombre de tu conexión configurada)
   - Defina `allowed_tools=["Read", "Glob", "Grep"]`
   - Defina `require_approval_for=["Edit", "Write", "Bash"]`
   - Renderice la puerta de inicio, luego `panel()` + `chat_input_bar()`
3. Ejecútala: `uv run streamlit run my_first_app.py`
4. Pídele que lea un archivo del repositorio (por ejemplo *"Read the
   README and summarize it in 3 bullets"*) y confirma que se ejecuta sin
   requerir aprobación (`Read` está en `allowed_tools`).
5. Pídele que escriba un archivo nuevo — confirma que la puerta de
   aprobación se dispara esta vez.

**Resultado esperado**: Una app funcional construida solo a partir del
README, distinguiendo correctamente las herramientas de ejecución
automática de las que requieren aprobación.

**Resolución de problemas**: Si `Read` sigue pidiendo aprobación, comprueba
que no lo has listado también en `require_approval_for` — `allowed_tools`
y `require_approval_for` no deberían solaparse para la misma herramienta.

**Elimina `my_first_app.py` cuando termines** — es un artefacto de
entrenamiento desechable, no forma parte del repositorio.

---

## Ejercicio 6 — Copilot rail en una app de producto

**Objetivo**: Ver `copilot_rail()` como un Copilot en rail lateral derecho,
no como un chat de página completa, y usar sus controles de Display config
para mantener una transcripción en vivo legible.

**Pasos**:

1. `make bi-semantic` (`examples/bi_to_semantic/`).
2. Carga el MIT Tableau Server pack en la pantalla 1 (no se requiere
   warehouse).
3. Conecta Copilot a la derecha. Observa el popover **Connection** y, junto
   a él, el popover de solo icono **Display config**
   (`:material/display_settings:`). Ábrelo: dos sliders, **Last messages**
   (por defecto 8) y **First n characters** (por defecto 200), cada uno
   activado por una píldora. Mueve cada slider y confirma que la
   transcripción se actualiza en vivo mientras el popover permanece
   abierto.
4. Encola un trabajo de reglas de acceso o de generación y observa la
   insignia compacta **Working · thinking…** en la fila de título — no una
   tarjeta de estado alta. **Cancel job** se sitúa en esa misma fila, junto
   a **Close**.

**Resultado esperado**: CoCo vive en el rail; la app posee la columna
izquierda. La transcripción se mantiene compacta sin importar cuánto dure
la conversación, gracias a los sliders de Display config, no por un
truncamiento fijo. Mismo primitivo subyacente (`panel()`) que `make
backlog`.

**Resolución de problemas**: Si falta el popover Display config, confirma
que tu checkout es al menos `0.1.8` (`uv run python -c "import
streamlit_coco as c; print(c.__version__)"`) — el popover se lanzó en
`0.1.8`; el selector **Config file** de la conexión se lanzó en `0.1.9`. El
`pyproject.toml` del ejemplo fija por ruta la librería a este checkout del
repositorio.

---

## Cierre

Ya has ejecutado todos los modos de interacción principales: panel
interactivo, puertas de aprobación, salida estructurada, headless, una
construcción desde cero y un Copilot rail incrustado en una app de
producto. Siguiente: lee [`demo-guide.md`](demo-guide.html) y haz un
ensayo cronometrado.
