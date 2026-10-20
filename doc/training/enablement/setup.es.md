# Configuración

Pon en marcha localmente el repositorio de desarrollo y confirma que estás
listo para el [recorrido guiado](guided-tour.html) y los
[ejercicios prácticos](hands-on.html). Referencia completa:
[`doc/deployment/local.md`](../../deployment/local.md) — esta página es el
recorrido condensado y específico de entrenamiento a través de ella.

## Cuentas y permisos necesarios

- Una cuenta de Snowflake con **acceso a Cortex Code**. Pregunta a tu asset
  owner si no dispones de una para el entrenamiento — puede haber una
  conexión compartida/sandbox disponible.
- Acceso Git a `DevoteamSP/streamlit-coco-dev` (el repositorio de
  desarrollo). Si solo necesitas el paquete publicado, con
  `pip install "streamlit-coco[sdk]"` desde PyPI es suficiente y puedes
  saltarte el paso 1 de abajo.

## 1. Clonar e instalar

```bash
git clone https://github.com/DevoteamSP/streamlit-coco-dev.git
cd streamlit-coco-dev
make install     # uv sync --extra dev
```

Verifica que el paquete se importa y comprueba la versión:

```bash
uv run python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.9
```

## 2. Instalar y verificar el CLI de CoCo

```bash
cortex --version
```

Si no está en `PATH`, instálalo o apunta al binario:

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

`CocoOptions(cli_path=...)` también funciona, en código, como alternativa a
la variable de entorno.

## 3. Configurar una conexión de Snowflake

Crea o confirma `~/.snowflake/connections.toml`:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema según se necesiten
```

El `~/.snowflake/config.toml` heredado también se detecta. Cuando se omite
`connection` en `CocoOptions`, el SDK usa la conexión por defecto del
Snowflake CLI.

## 4. Comprobación del entorno (todavía sin agente iniciado)

```bash
uv run python -c "
import streamlit_coco as st_coco
env = st_coco.check_environment(connection='analytics')
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
"
```

`env.ready` debería imprimir `True`. Si no, revisa la tabla de resolución
de problemas en
[`doc/deployment/local.md` §7](../../deployment/local.md#7-troubleshooting)
antes de continuar.

## 5. Ejecutar la suite de tests

```bash
make check    # ruff + pytest de unidad/smoke (excluye tests/e2e)
```

Todos los tests deberían pasar. Esto confirma que tu entorno Python
coincide con CI.

## 6. Ejecutar tu primera demo

```bash
make chat
```

Se abre una pestaña del navegador con la demo `panel()` +
`chat_input_bar()` (`examples/chat_app.py`). Escribe un prompt — por
ejemplo *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
(¿qué tablas hay disponibles en SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?) — y
confirma que ves una respuesta en streaming con al menos una tarjeta de
herramienta.

## Lista de verificación — estás listo cuando...

- [ ] `uv run python -c "import streamlit_coco as c; print(c.__version__)"` imprime `0.1.9`
- [ ] `cortex --version` funciona correctamente
- [ ] `check_environment(...).ready` es `True`
- [ ] `make check` pasa sin fallos
- [ ] `make chat` abre una app funcional y obtienes una respuesta en
      streaming con al menos una tarjeta de herramienta

Si todas las casillas están marcadas, continúa con
[`guided-tour.md`](guided-tour.html).

## Referencia rápida de resolución de problemas

| Síntoma | Solución |
| --- | --- |
| `SDKNotInstalledError` | `make install` de nuevo, o `pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | Instala el CLI; define `CORTEX_CODE_CLI_PATH` |
| `CocoConnectionError` | Corrige `connections.toml`; prueba con `cortex --version` y el Snowflake CLI directamente |
| Sesión atascada en "Starting CoCo…" | Revisa los logs de la terminal; define `STREAMLIT_COCO_DEBUG=1` |

Tabla completa:
[`doc/deployment/local.md` §7](../../deployment/local.md#7-troubleshooting).
La Guía Técnica tiene la referencia completa:
[`help.html`](../technical-guide/help.html).
