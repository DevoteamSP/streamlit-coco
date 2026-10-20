# Referencia de comandos

Cada objetivo `make` del `Makefile` del repositorio que ejecuta
directamente quien usa la librería. No hay entrada `[project.scripts]` —
todos los comandos pasan por `make`.

## `make install`

Sinopsis: `make install`

Instala el paquete con sus extras `dev`, en modo editable, vía `uv`
(`uv sync --extra dev`). `make sync` es un alias del mismo objetivo.

Salida: una instalación editable en el entorno virtual activo.

## `make run`

Sinopsis: `make run [EXAMPLE=<ruta>]`

| Variable | Por defecto | Efecto |
|---|---|---|
| `EXAMPLE` | `examples/chat_app.py` | El script de ejemplo a ejecutar |

Ejecuta el ejemplo dado con `streamlit run`. Salida: la app se abre en el
navegador por defecto en el siguiente puerto libre de Streamlit.

## `make chat`

Sinopsis: `make chat`

Ejecuta `examples/chat_app.py` — la demo del patrón preferido. Ver
[Quiero ejecutar las apps de ejemplo](task-run-the-example-apps.html) y
[Referencia de apps de ejemplo](reference-examples.html).

## `make approval`

Sinopsis: `make approval`

Ejecuta `examples/approval_gate.py` — la demo heredada CCv2 `chat()`.

## `make structured`

Sinopsis: `make structured`

Ejecuta `examples/structured_output.py` — la demo de `output_schema` /
`on_structured_output`.

## `make headless`

Sinopsis: `make headless`

Ejecuta `examples/headless_pipeline.py` desde una terminal, sin Streamlit
involucrado. Salida: texto de eventos en streaming en la terminal.

## `make cwd-upload`

Sinopsis: `make cwd-upload`

Ejecuta `examples/cwd_upload_chat.py` — la demo de subida de archivos.

## `make backlog`

Sinopsis: `make backlog`

Ejecuta el Product Backlog Desk (`examples/backlog_desk/`) — una demo
multipágina respaldada por archivos/JSON con un Copilot en rail lateral
derecho. Los archivos de salida aterrizan bajo
`examples/backlog_desk/data/`; ver [Salidas](outputs.html).

## `make bi-semantic`

Sinopsis: `make bi-semantic`

Ejecuta BI → Semantic (`examples/bi_to_semantic/`). `make
tableau-semantic` es un alias obsoleto del mismo objetivo. Los archivos de
salida aterrizan bajo `examples/bi_to_semantic/out/`; ver
[Salidas](outputs.html).

## `make app-builder`

Sinopsis: `make app-builder`

Ejecuta App Builder (`examples/app_builder/`). Los archivos de salida
aterrizan bajo `examples/app_builder/out/<slug>/`; ver
[Salidas](outputs.html).

## `make e2e-harness`

Sinopsis: `make e2e-harness`

Ejecuta el harness UX sin CoCo (`examples/e2e_ux_harness.py`) usado por la
suite end-to-end de Playwright — sin agente en vivo involucrado.

## `make test`

Sinopsis: `make test`

Ejecuta la suite de tests de unidad/smoke: `pytest tests/
--ignore=tests/e2e -v`.

## `make lint`

Sinopsis: `make lint`

Ejecuta `ruff check .`.

## `make format`

Sinopsis: `make format`

Ejecuta `ruff format . && ruff check --fix .`.

## `make check`

Sinopsis: `make check`

Ejecuta `make lint` y luego `make test`.

## `make e2e-install`

Sinopsis: `make e2e-install`

Instala el extra `e2e` y el navegador Chromium para Playwright. Ejecutar
una vez antes del primer `make e2e`.

## `make e2e`

Sinopsis: `make e2e`

Ejecuta la suite end-to-end UX de Playwright (`tests/e2e`, marcador `e2e`)
contra `make e2e-harness`.

## `make audit`

Sinopsis: `make audit`

Ejecuta `pip-audit --skip-editable` — un escaneo de vulnerabilidades de
dependencias.

## `make test-all`

Sinopsis: `make test-all`

Ejecuta `make check` + `make e2e` + `make audit` — la puerta automatizada
completa.

## Otros objetivos (orientados a mantenedores)

Estos objetivos existen para cortar y publicar un release en lugar de
para usar la librería día a día; se cubren en la Guía Técnica
`upgrade-and-release.html`, no se repiten aquí:

| Objetivo | Efecto |
|---|---|
| `make build` | Construye sdist + wheel en `dist/` (`uv build`) |
| `make publish` | Sube `dist/` a PyPI (`uv publish`) |
| `make sync-release` | Sincroniza el árbol de release con `../streamlit-coco` (`DRY_RUN=1` / `COMMIT=1` / `PUSH=1`) |
| `make clean` | Elimina cachés y artefactos de build |
| `make adoption-stats` / `make adoption-chart` | Recolecta/reconstruye métricas de tráfico de PyPI y GitHub bajo `doc-dev/metrics/` — fuera del alcance de esta guía |
