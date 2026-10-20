# Caso 2 — Intermedio: puertas de aprobación y un Copilot rail en una app real

**Nivel:** Intermedio — tus propios datos / un trabajo real, menos guiado.
**Tiempo:** 45–60 min.

## Contexto

Un rail junto a tus propias páginas es la forma para la que está
construido `copilot_rail()`: tanto `examples/backlog_desk/`
(respaldado por archivos/JSON, sin SQL) como `examples/bi_to_semantic/`
(Tableau/Power BI → vista semántica) lo conectan a una app multipágina
existente en lugar de reemplazar la app con una ventana de chat. Este
caso te pide hacer lo mismo con un flujo de trabajo real, con puntos de
control en lugar de instrucciones clic a clic.

## Objetivo

Configurar un `CocoOptions` con `require_approval_for` para un flujo de
trabajo que realmente muta algo, e incrustar `copilot_rail()` como una
columna derecha junto a una app multipágina existente (o la incluida).

## Datos

**Los tuyos, o un sustituto.** Si ya ejecutas una app Streamlit
multipágina, úsala. Si no, usa `examples/backlog_desk/` como sustituto de
"tus datos": tickets, epics y releases respaldados por archivos bajo
`examples/backlog_desk/data/{epics,tickets,releases,policies}` — archivos
reales que puedes inspeccionar con `git diff` después de que CoCo los
edite. `examples/bi_samples/` (paquetes de fixtures Tableau/Power BI con
licencia MIT) es el sustituto alternativo si prefieres seguir la forma de
BI → Semantic.

## Puntos de control

1. **Elige tu superficie.** Identifica una página de tu app (o la página
   Ticket de `examples/backlog_desk/`) donde una acción mutante carece
   actualmente de una salvaguarda human-in-the-loop, o donde quieras que
   un agente redacte algo que una persona revise antes de que se aplique.

2. **Define `CocoOptions` para ese flujo de trabajo.** Separa las
   herramientas que pueden ejecutarse sin supervisión (exploración de solo
   lectura: `Read`, `Glob`, `Grep`) de las que deben pausarse (`Edit`,
   `Write`, `Bash`, y `SQL` si tu flujo de trabajo toca Snowflake). Pon el
   primer conjunto en `allowed_tools` y el segundo en
   `require_approval_for` — no deberían solaparse para la misma
   herramienta. *Punto de control: puedes indicar, para cada herramienta
   que tu flujo de trabajo podría invocar, a qué lista pertenece y por
   qué.*

3. **Limita una sesión a la página.** Usa `get_or_create_session(opts,
   key=...)` con una clave específica para este flujo de trabajo, y decide
   cuándo debería reiniciarse — `copilot_rail()` no se reinicia por sí
   solo ante un cambio de `cwd` o de esquema; quien llama posee esa
   decisión de ciclo de vida. *Punto de control: sabes exactamente qué
   acción del usuario debería disparar `reset_session(...)`.*

4. **Conecta `copilot_rail()`.** Añádelo como la columna derecha de tu
   layout, siguiendo el patrón de `examples/backlog_desk/` (abierto desde
   un botón de cabecera, cerrado con **Close**) o el patrón de
   `examples/bi_to_semantic/` (un popover de conexión junto al rail).
   Consulta `doc/features/copilot-rail/copilot-rail.md` en el repositorio
   para la lista completa de parámetros (`job=`, `on_job_sent=`,
   `on_job_finished=`, `example_questions=`, `toml_file=`). *Punto de
   control: el rail se abre y se cierra sin volver a ejecutar el resto de
   tu página.*

5. **Encola un trabajo real y observa cómo se controla.** Dispara la
   acción mutante desde tu página (un trabajo `status="queued"`, o un
   prompt de chat directo) y confirma que `require_approval_for` la
   pausa con **Approve once** / **Always allow** / **Deny**, no con una
   escritura silenciosa. *Punto de control: puedes señalar la línea exacta
   de tu `CocoOptions` que provocó la pausa.*

6. **Mantén la transcripción utilizable.** Abre el popover Display config
   del rail (`:material/display_settings:`) y ajusta **Last messages** /
   **First n characters** para que una sesión larga se mantenga legible en
   el ancho del rail.

## Resultado esperado

- Copilot se sitúa en una columna derecha junto al contenido existente de
  tu página — la página en sí nunca se reemplaza por un chat de pantalla
  completa.
- La acción mutante que elegiste en el paso 1 ahora se pausa a la espera
  de una decisión explícita de Approve/Deny antes de ejecutarse.
- Puedes explicar, sin volver a leer el código, por qué cada herramienta
  de tu flujo de trabajo se ejecuta automáticamente o requiere aprobación.

## Dónde mirar si te atascas

- La puerta de aprobación no se dispara, o se dispara para la herramienta
  equivocada:
  [`help.html#always-allow-scope`](../technical-guide/help.html#always-allow-scope).
- El banner de aprobación queda sin respuesta hasta que expira:
  [`help.html#approval-timeout`](../technical-guide/help.html#approval-timeout).
- Algo en el flujo de trabajo se comporta de forma inesperada y las
  tarjetas de herramienta por sí solas no lo explican: activa
  `STREAMLIT_COCO_DEBUG=1` y vuelve a ejecutar — ver
  [`help.html#debug-mode-not-showing-payloads`](../technical-guide/help.html#debug-mode-not-showing-payloads)
  si el payload en bruto sigue sin aparecer.
