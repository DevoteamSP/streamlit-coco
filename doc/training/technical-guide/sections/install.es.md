# Instalación

Un objetivo de despliegue se lanza hoy: **local** — Streamlit, el CLI de
CoCo, y la configuración de conexión de Snowflake todos en el mismo host.
Las rutas de instalación de Streamlit in Snowflake (SiS) y SPCS no están
implementadas en este repositorio hoy. Aparecen solo como alcance en
[security](security.html#threat-model-summary) (contexto del modelo de
amenazas) y en la hoja de ruta del proyecto, no como algo que se pueda
instalar.

## Matriz de prerrequisitos

| Requisito | Versión | Por qué |
|---|---|---|
| Python | 3.10+ | `requires-python = ">=3.10"` en `pyproject.toml` |
| Streamlit | >=1.55 | `streamlit-coco` declara `streamlit>=1.55` como su única dependencia obligatoria |
| CLI de CoCo (`cortex`) | accesible en `PATH`, o `CORTEX_CODE_CLI_PATH` definido | El SDK lo lanza como subproceso; la librería no lo empaqueta |
| `cortex-code-agent-sdk` | >=1.0.7 | Instalado vía el extra `[sdk]`; la librería habla con CoCo a través de este SDK |
| Conexión de Snowflake | un perfil en `~/.snowflake/connections.toml` (o el `config.toml` heredado) | El CLI/SDK se autentican a través de este archivo; la librería nunca almacena credenciales |

## Instalación local — pasos ordenados

### 1. Instalar el paquete

```bash
pip install "streamlit-coco[sdk]"
```

o, desde un clon (contribuidores en `streamlit-coco-dev`):

```bash
git clone https://github.com/DevoteamSP/streamlit-coco.git
cd streamlit-coco
make install   # uv sync --extra dev
```

Verifica:

```bash
python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.9
```

### 2. Instalar el CLI de CoCo

El Cortex Code Agent SDK lanza el CLI de CoCo (`cortex`) como subproceso.
Debe estar instalado y accesible en la misma máquina que la app
Streamlit.

Verifica:

```bash
cortex --version
```

Si no está en `PATH`:

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

(o pasa `cli_path=` en `CocoOptions` — ver
[configuration](configuration.html)).

### 3. Configurar una conexión de Snowflake

Crea o actualiza `~/.snowflake/connections.toml`:

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
```

El `~/.snowflake/config.toml` heredado también se detecta. Ver
[security](security.html#roles-and-grants) para el rol que debería usar
esta conexión.

Verifica (sondea SDK, CLI, y configuración sin iniciar un agente):

```python
import streamlit_coco as st_coco

env = st_coco.check_environment(connection="analytics")
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
```

Para un script que debería fallar rápido en lugar de devolver un objeto de
estado:

```python
st_coco.require_environment(connection="analytics")
```

### 4. Ejecutar una app de ejemplo

```bash
make chat
```

Verifica: el navegador se abre en la demo de chat y la puerta de inicio
("Start CoCo Chat") muestra el estado SDK / CLI / Snowflake en verde antes
de hacer clic en ella. Ver [operations](operations.html) para la lista
completa de objetivos `make` que ejecutan apps de ejemplo.

## Qué no es instalable hoy

- **Streamlit in Snowflake (SiS)** — no existe ninguna ruta de
  instalación en este repositorio. SiS aparece solo como contexto de
  despliegue en el modelo de amenazas, no como un objetivo soportado.
- **SPCS** — igual: solo alcance del modelo de amenazas, no un objetivo
  de instalación.
- **Native App** — no hay `manifest.yml` / `snowflake.yml` en el
  repositorio; no hay nada que instalar como Native App.
