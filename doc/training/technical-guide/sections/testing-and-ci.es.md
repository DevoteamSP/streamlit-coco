# Testing y CI

## Árbol de tests

```text
tests/            unidad + smoke (make test por defecto; 17 archivos)
tests/e2e/         Playwright UX e2e (conftest.py + 3 specs UX)
examples/e2e_ux_harness.py   harness sin CoCo que impulsa la suite e2e
```

Archivos de test unitarios destacados: `test_core.py`, `test_errors.py`,
`test_upload.py`, `test_copilot_rail.py`, `test_app_viewer.py`,
`test_snowflake_toml.py`, `test_ndjson_fixtures.py`,
`test_backlog_desk.py`, `test_bi_to_semantic_parse.py`,
`test_app_builder_catalog.py`, `test_app_builder_profile.py`,
`test_rich_text.py`, `test_smoke.py`.

## Cómo ejecutar cada puerta

| Puerta | Comando | Cubre |
|---|---|---|
| Rápida | `make check` | `ruff check .` + `pytest tests/ --ignore=tests/e2e -v` |
| Navegador UX | `make e2e` | Playwright contra `examples/e2e_ux_harness.py` — sin agente CoCo en vivo. Primera vez: `make e2e-install` (instala el extra `[e2e]` + Chromium). |
| Seguridad | `make audit` | `pip-audit --skip-editable` |
| Automatizada completa | `make test-all` | `check` + `e2e` + `audit` |

La suite de navegador cubre: resaltado de código con fences SQL/Python,
**Copy** al portapapeles en los mensajes del asistente,
`cwd_uploader` de barra lateral → `_uploads/`, y truncamiento por
`max_messages` + **Load earlier**.

Las listas de verificación manuales/en vivo (necesitan un CLI de CoCo
real + conexión de Snowflake) viven bajo
`doc/features/<feature>/test-checklist.md`, indexadas desde
`doc/features/README.md`. Orden de ejecución sugerido: subida de
archivos → panel → visualización de herramientas / aprobaciones →
opcional structured / headless / approval (CCv2) / bi-semantic.

## Qué comprueba realmente CI

`.github/workflows/ci.yml` — en cada push a `main` y cada pull request
dirigido a `main`:

- trabajo `test`: `ruff check .`, luego `pytest tests/ --ignore=tests/e2e
  -v`, luego `pip-audit --skip-editable` (este último paso es
  `continue-on-error: true` — no bloqueante hasta que se establezca una
  línea base limpia).
- trabajo `e2e`: instala el extra `[e2e]` y Chromium, luego
  `pytest tests/e2e -m e2e -v`. No se llama a ningún agente CoCo en vivo.

`.github/workflows/security.yml` — en pull requests a `main`, pushes a
`main`, y semanalmente (lunes 06:00 UTC):

- trabajo `gitleaks`: instala el binario CLI de Gitleaks (no
  `gitleaks-action@v2`, que necesita un `GITLEAKS_LICENSE` para
  repositorios de organización de GitHub) y ejecuta `gitleaks git
  --verbose --redact --exit-code 1 .`.
- trabajo `pip-audit`: `pip-audit --skip-editable` (también
  `continue-on-error: true`).

**CodeQL no se ejecuta en el CI de este repositorio.** Ver
[security](security.html#ci-security-posture-current) para saber por
qué, y no asumas un trabajo de CodeQL al razonar sobre las puertas de
este repositorio.

`.github/workflows/release.yml` se ejecuta solo en pushes de tags `v*`:
construye sdist+wheel, genera el SBOM, y publica en PyPI (se omite para
sufijos de tag de pre-release). Ver
[upgrade-and-release](upgrade-and-release.html).

## Qué añadir con un cambio

- Un test para el nuevo comportamiento: un test unitario bajo `tests/`
  para código de la librería, o un spec de Playwright bajo `tests/e2e/`
  para comportamiento UX que la suite de navegador debería capturar
  (código con fences, portapapeles, subida, ventaneo de transcripción son
  el precedente existente).
- Una entrada de lista de verificación manual bajo
  `doc/features/<feature>/test-checklist.md` cuando el cambio toca una
  funcionalidad de interfaz que necesita un CLI de CoCo en vivo +
  conexión de Snowflake para verificarse (cada funcionalidad existente
  tiene su propio archivo de checklist — añade filas al relevante, o crea
  una nueva carpeta `doc/features/<feature>/` para una funcionalidad
  genuinamente nueva, siguiendo la forma `## Preconditions` /
  `## Golden path` / `## Sign-off` de los archivos existentes).
- Una entrada en `CHANGELOG.md` bajo `[Unreleased]` — `Added` /
  `Changed` / `Fixed` / `Security` según corresponda. Las correcciones de
  seguridad siempre van bajo `Security`, nunca bajo `Fixed`.
