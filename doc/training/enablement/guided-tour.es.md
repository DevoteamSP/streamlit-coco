# Recorrido guiado

Un recorrido de 20–30 minutos por el producto en funcionamiento. Esto no es
un guion de demo (eso es [`demo-guide.md`](demo-guide.html)) ni son
ejercicios (eso es [`hands-on.md`](hands-on.html)) — solo lo que verás al
ejecutar cada comando, y a qué prestar atención.

Completa primero la [lista de verificación de configuración](setup.html).

## Parte 1 — `make chat`, el patrón preferido (~15 min)

```bash
make chat
```

Esto ejecuta `examples/chat_app.py`. Es la implementación de referencia del
patrón preferido de la librería: **tú posees la página, CoCo posee la
sesión.**

**Qué aparece primero:** un título ("CoCo for Streamlit"), una puerta de
estado del entorno ("Start CoCo Chat") y una barra lateral. Antes de hacer
clic en Start, la puerta muestra los resultados de la sonda SDK / CLI /
Snowflake — esto es `check_environment()` renderizado por
`render_start_gate()`. Fíjate en que nunca arranca un proceso de agente por
sí sola; solo lo hace una vez que haces clic en el botón.

**Haz clic en Start CoCo Chat.** El panel principal está vacío al
principio, con una línea de estado. En la barra lateral, abre el popover
**Settings** (icono `:material/tune:`). Observa:

- Un control segmentado **Output mode** (`transcript` / `field`) — se
  corresponde directamente con `panel(output_mode=...)`.
- Un interruptor **CoCo debug mode** — activa el comportamiento equivalente
  a `STREAMLIT_COCO_DEBUG` a través de `st.session_state["coco_debug"]`,
  mostrando los payloads en bruto de las herramientas una vez activado.
- Un interruptor **Plan mode** — establece `permission_mode="plan"` para
  poder ejercitar las aprobaciones de `ExitPlanMode`.
- Píldoras **Auto-allowed** y **Requires approval** — alimentan en vivo
  `CocoOptions.allowed_tools` y `require_approval_for`, y un botón **Reset
  session** reinicia el worker cuando las cambias (los permisos de
  herramienta forman parte del hash de opciones de la sesión).

**Escribe un prompt** — por ejemplo *"What tables are available in
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*. Observa cómo la transcripción se
renderiza de forma progresiva, no toda de golpe: esto es el bucle de
sondeo `@st.fragment` (`run_every=0.25`) leyendo del worker `CocoSession`
en segundo plano, así que el resto de la página no se vuelve a ejecutar
mientras CoCo está pensando. Aparece una tarjeta de herramienta
(probablemente Glob o SQL) — esta es la tarjeta legible que la librería
construye en lugar de un volcado JSON en bruto.

**Pide algo que escriba** — por ejemplo *"Create a summary table called
TOP_CUSTOMERS in my schema."* Aparece un banner de aprobación con
**Approve once**, **Always allow**, **Deny** (en ese orden). Esto es
`render_approvals()`, conectado automáticamente dentro de `panel()` porque
`show_approvals=True` es el valor por defecto. Esta es la puerta
human-in-the-loop: `Edit`, `Write` y `Bash` están en
`require_approval_for` por defecto en este ejemplo.

**Prompts de prueba en la barra lateral:** activa **Test prompts** para
explorar `examples/testdata/prompts.json` por categoría y enviar uno sin
escribir — útil más adelante para demos repetibles.

## Parte 2 — `make backlog`, un rail junto a una app real (~5 min)

```bash
make backlog
```

Esto ejecuta el Product Backlog Desk (`examples/backlog_desk/`), una app
multipágina respaldada por archivos (sin SQL): páginas **Board**, **Epic**,
**Ticket**, **Release**. Fíjate en que Copilot **no** es una página de
navegación — es un rail lateral derecho que se abre desde el botón
**Copilot** de la cabecera, o desde un enlace de acción como "Check DoD" en
un ticket. Se cierra con **Close**; las páginas Board/Epic/Ticket/Release
funcionan sin conectar Copilot en absoluto. Esta es la forma para la que
está construido `copilot_rail()`: la app posee la página, CoCo se sienta en
una columna al lado, no en su lugar.

## Parte 3 — `make bi-semantic`, el rail en su plenitud (~8 min)

```bash
make bi-semantic
```

Esto ejecuta BI → Semantic (`examples/bi_to_semantic/`), el uso más
completo de `copilot_rail()`. En la pantalla 1 (**Load**), carga el
**MIT Tableau Server pack** incluido — no se necesita warehouse. Pasa a la
pantalla 4 o 6 y abre Copilot a la derecha.

Fíjate, en la fila de título del rail: **Copilot**, un popover
**Connection**, y un popover de solo icono **Display config**
(`:material/display_settings:`, al pasar el ratón muestra "Display
config") junto a él. Abre Display config — tiene dos sliders: **Last
messages** (por defecto 8, rango 1–50) y **First n characters** (por
defecto 200, rango 40–1000), cada uno con una píldora de activar/desactivar.
Mover un slider vuelve a ejecutar solo el fragmento del rail; el popover
permanece abierto y la transcripción se actualiza en vivo. Esto sustituyó
un aspecto anterior de solo píldoras — a partir de esta versión, la
compacidad de la transcripción se controla enteramente desde este popover.

Mientras CoCo está ocupado, observa la fila de título: una insignia
compacta **Working · thinking…** se sitúa allí — no una tarjeta de estado
alta — y aparece un botón **Cancel job** junto a **Close**. Después de
Connect, en una transcripción vacía, puede que veas botones de **example
question**; al hacer clic en uno se envía inmediatamente o, si está
marcado como deferred, se copia al campo de entrada del chat para que lo
edites primero.

## Qué observar en las tres

- El agente siempre se ejecuta en el servidor; el navegador solo renderiza
  widgets de Streamlit — nada del proceso del agente se expone al cliente.
- Las puertas de aprobación son el mismo primitivo en todas partes
  (`render_approvals()` dentro de `panel()`), ya sea que la app sea un chat
  de página completa o un rail.
- `panel()` es el núcleo común; `copilot_rail()` es `panel()` más chrome de
  conexión, encolado de trabajos y controles de compacidad de la
  transcripción, construido para incrustarse junto a una app existente en
  lugar de reemplazarla.

Siguiente: [`hands-on.md`](hands-on.html) para construir y romper cosas por
tu cuenta.
