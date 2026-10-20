# Quiero configurar aprobaciones de herramientas

**Para** un desarrollador que decide qué herramientas del agente necesitan
un humano en el bucle · **15 min** · **una app mínima funcional**

Terminas con una sesión donde herramientas específicas se ejecutan
automáticamente y otras se pausan para aprobación, resueltas ya sea
mediante la interfaz incluida o de forma programática.

## Antes de empezar

- Una app mínima funcional
  ([Quiero construir una app CoCo mínima](task-build-a-minimal-app.html)).
- Saber qué herramientas puede llamar el agente en tu app (`Read`, `Glob`,
  `Grep`, `Edit`, `Write`, `Bash`, la herramienta SQL, `AskUserQuestion`,
  `ExitPlanMode`, herramientas provistas por MCP, …) y cuáles de ellas son
  destructivas en tu contexto.

## Pasos

1. Define `allowed_tools` en `CocoOptions` para las herramientas que nunca
   deberían necesitar un prompt, y `require_approval_for` para las que
   siempre deberían pausarse:

   ```python
   options = st_coco.CocoOptions(
       connection="my_connection",
       allowed_tools=["Read", "Glob", "Grep"],
       require_approval_for=["Edit", "Write", "Bash"],
   )
   ```

   `AskUserQuestion` y `ExitPlanMode` siempre se pausan para una decisión,
   sin importar lo que se liste en ninguna de las dos opciones.

2. Monta el panel con las aprobaciones visibles (el valor por defecto):

   ```python
   st_coco.panel(session, show_approvals=True)
   ```

   Cuando el agente llama a una herramienta coincidente con
   `require_approval_for`, el estado de la sesión pasa a `awaiting_user` y
   `render_approvals()` muestra tres controles: **Approve once**, **Always
   allow**, **Deny**. Ni `AskUserQuestion` ni las solicitudes de
   `ExitPlanMode` muestran **Always allow**.

3. Para resolver las aprobaciones desde tu propia interfaz en lugar de los
   controles incluidos, llama directamente a los resolvers de bajo nivel
   con el id de la solicitud pendiente (de
   `session.chat_result().pending_approval`):

   ```python
   result = session.chat_result()
   if result.pending_approval:
       request_id = result.pending_approval["request_id"]
       st_coco.approve_pending(session, request_id, always=False)
       # o: st_coco.deny_pending(session, request_id, reason="not now")
   ```

4. Opcionalmente, estrecha o amplía la puerta en tiempo de ejecución
   pasando un callable a `require_approval_for` en lugar de una lista
   fija, y luego llama a `session.sync_options(options)` después de
   cambiarlo para que la sesión adopte el nuevo hash.

## Resultado

Las herramientas en `allowed_tools` se ejecutan sin ningún prompt. Las
herramientas coincidentes con `require_approval_for` pausan la ejecución y
muestran el control de aprobación de tres botones (o esperan a
`approve_pending`/`deny_pending` en una interfaz personalizada) antes de
ejecutarse. Una denegación no ejecuta la llamada a la herramienta; el
turno del agente continúa desde ahí, opcionalmente con el motivo que
pasaste.

## Variaciones

- **Always allow** aplica solo para la sesión actual — se borra en
  `session.reset()` o al reiniciar el proceso, nunca se escribe en una
  política persistida.
- `permission_mode="plan"` enruta las llamadas a herramientas a través de
  un flujo `ExitPlanMode` en lugar de aprobación por herramienta;
  `render_plan_banner()` muestra el banner de modo plan y la llamada a la
  acción **Execute plan**.
- `approval_timeout_seconds` (por defecto `600.0`, diez minutos) controla
  cuánto tiempo espera una aprobación pendiente antes de que la ejecución
  falle con `ApprovalTimeoutError`.

## Si falla

- [Timeout de aprobación](../../technical-guide/help.html#approval-timeout)
- ["Always allow" tiene alcance de sesión únicamente](../../technical-guide/help.html#always-allow-scope)
