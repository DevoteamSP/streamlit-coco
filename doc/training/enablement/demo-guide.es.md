# Guía de demo

Una demo guionizada de 10 minutos: gancho de apertura, recorrido en vivo,
cierre. Audiencia: responsables técnicos de decisión, ingenieros de datos,
profesionales de Snowflake.

## Lista de requisitos técnicos (antes de la demo)

- [ ] Cuenta de Snowflake con acceso a Cortex Code, conexión configurada
- [ ] `cortex --version` funciona correctamente
- [ ] `make install` ejecutado, `make check` pasa
- [ ] Una base de datos de Snowflake con tablas de muestra disponibles (por
      ejemplo `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
- [ ] Ventanas de terminal y navegador dispuestas una al lado de la otra
- [ ] Ensayo cronometrado una vez, dentro de las últimas 24 horas

## Gancho de apertura (30 seg — el problema)

> "Conectar un agente CoCo a una app Streamlit tú mismo implica construir
> gestión de sesión a través de reruns, renderizado en streaming,
> visualización de tarjetas de herramienta y puertas de seguridad desde
> cero. `streamlit-coco` te da eso en unas pocas líneas de Python. Déjame
> mostrártelo."

## Recorrido en vivo (7 min — paso a paso con puntos de conversación)

### Paso 1 — Primera impresión (2 min)

1. Muestra `examples/chat_app.py` — señala que es un archivo corto y
   legible construido a partir de cuatro llamadas: `check_environment()`,
   `render_start_gate()`, `get_or_create_session()`, `panel()` +
   `chat_input_bar()`.
2. Ejecuta `make chat`.
3. Se abre el navegador → muestra la interfaz del panel (puerta de inicio,
   luego la transcripción vacía y la línea de estado una vez iniciado).
4. Escribe: *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
5. Observa la transcripción en streaming renderizándose en tiempo real;
   señala la tarjeta de herramienta que aparece (Glob/SQL).

> Punto de conversación: "Un archivo Python corto. Interfaz de agente
> completa con streaming, visibilidad de herramientas y gestión de sesión
> resueltas por ti."

### Paso 2 — Puertas de aprobación (3 min)

1. Escribe: *"Show me the top 5 customers by total order amount. Write the
   SQL and run it."*
2. El agente propone SQL → se dispara el banner de aprobación. Recorre el
   SQL completo mostrado, haz clic en **Approve once** → aparecen los
   resultados.
3. Escribe: *"Now create a summary table called TOP_CUSTOMERS in my
   schema."*
4. La puerta de aprobación se dispara de nuevo — esta vez haz clic en
   **Deny** con un motivo ("let's not create tables in the demo"). El
   agente lo reconoce y sugiere una alternativa.

> Punto de conversación: "Cada acción destructiva — SQL, escritura de
> archivos, comandos bash — requiere aprobación humana explícita,
> configurada por herramienta en `CocoOptions.require_approval_for`."

### Paso 3 — Salida estructurada (1.5 min)

1. Cambia a `make structured` (`examples/structured_output.py`).
2. Muestra el `output_schema` en el código.
3. Escribe: *"Give me a breakdown of orders by status."*
4. El agente devuelve JSON estructurado → la app lo renderiza como un
   gráfico, no como texto en bruto.

> Punto de conversación: "La salida del agente puede fluir directamente
> hacia tus propios widgets mediante un callback `on_structured_output` —
> sin parseo manual de JSON."

### Margen (0.5 min)

Aterriza en el cierre desde donde estés en el Paso 3. Si queda tiempo en
la sala tras el cierre guionizado, hay dos cosas que vale la pena mostrar
pero que **no** forman parte del guion cronometrado de 10 minutos:

- `make headless` (`examples/headless_pipeline.py`) — la misma API
  `query()` sin import de Streamlit, para CI y trabajos por lotes.
- `make bi-semantic` o `make backlog` — `copilot_rail()`, mostrando CoCo
  como una columna derecha en una app de producto en lugar de un chat de
  página completa.

## Cierre (2.5 min — recapitulación de valor + CTA)

Puntos resumen para dejar en pantalla o decir en voz alta:

- `pip install "streamlit-coco[sdk]"` — una app funcional en un puñado de
  líneas
- Puertas de aprobación activadas por defecto para herramientas
  destructivas
- Una sola librería cubre panel interactivo, salida estructurada y uso
  headless
- Código abierto (Apache-2.0), construido para Snowflake

**Llamada a la acción**: "Pruébalo contra tu propia cuenta de Snowflake
esta semana — el quickstart del README te lleva rápidamente a una app
funcional. Contacta con el asset owner si te encuentras problemas de
configuración."

## Si preguntan… (FAQ)

| Pregunta | Respuesta |
| --- | --- |
| ¿Funciona con Streamlit in Snowflake (SiS)? | No está lanzado hoy. El despliegue local (CLI + Streamlit + configuración de Snowflake en el mismo host) es la única topología lanzada; SiS/SPCS son solo alcance del modelo de amenazas. |
| ¿Qué LLM usa? | El que use Cortex Code por debajo — no hay configuración de modelo en esta librería más allá de `CocoOptions.model`. |
| ¿Puedo personalizar qué herramientas necesitan aprobación? | Sí — `allowed_tools` / `require_approval_for` en `CocoOptions`, por herramienta. |
| ¿Está lista para producción? | Alpha (`0.1.9`) — la API todavía puede cambiar. |
| ¿En qué se diferencia de usar el CLI de CoCo directamente? | Esta librería se encarga de la plomería específica de Streamlit: estado de sesión seguro frente a reruns, renderizado en streaming, tarjetas de herramienta e interfaz de aprobación — el CLI por sí solo no tiene nada de eso. |
| ¿Qué hay de la subida de archivos? | `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)` suben archivos al directorio de trabajo del agente; ver `make cwd-upload`. |
| ¿Qué es `copilot_rail()`? | Un Copilot en rail lateral derecho alrededor de `panel()` — conexión, trabajos encolados y un popover Display config (límites de mensajes/caracteres) para una transcripción compacta. Ver `make bi-semantic` / `make backlog`. |
| ¿Hay un registro de auditoría de aprobaciones? | No persistido hoy — "Always allow" tiene alcance de sesión únicamente y se borra al reiniciar. |

## Limpieza

```bash
# Detén la app en ejecución (Ctrl+C)
# No se crearon tablas/artefactos si la aprobación de CREATE TABLE se denegó según el guion
```
