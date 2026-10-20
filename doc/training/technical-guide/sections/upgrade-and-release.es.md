# Actualización y release

## Versiones

streamlit-coco sigue semver. La versión actual es **0.1.9** (alpha —
`Development Status :: 3 - Alpha` en `pyproject.toml`). No hay ningún
archivo de notas de migración separado de `CHANGELOG.md`; el impacto de
actualización de una versión dada es lo que indique la entrada de
`CHANGELOG.md` de esa versión bajo Added / Changed / Fixed / Security.

## Proceso de publicación

Hay dos repositorios de GitHub involucrados:

| Repositorio | Rol |
|---|---|
| `DevoteamSP/streamlit-coco-dev` | Desarrollo (privado, WIP, agentes, experimentos) |
| `lletourmy/streamlit-coco` | Superficie de release pública **temporal** — los tags subidos aquí disparan la publicación en PyPI |

El nombre del proyecto en PyPI es siempre `streamlit-coco`, sin importar
qué repositorio de GitHub lo publique actualmente.

**Advertencia sobre el publicador temporal:** `DevoteamSP` aún no está
validado como Trusted Publisher de PyPI, así que `RELEASE_REMOTE`, la
puerta de subida a PyPI de `release.yml`
(`github.repository == 'lletourmy/streamlit-coco'`), y las URLs
publicadas del paquete apuntan actualmente a
`lletourmy/streamlit-coco`. Cuando `DevoteamSP` esté validado, todo esto
se trasladará a `DevoteamSP/streamlit-coco` — esto es una transición
única, no un paso por cada release.

### Pasos del release, en orden

1. **Preparar en `-dev`.** Crea el kit de release para la versión
   (`doc/releases/X.Y.Z/`, `doc-dev/releases/X.Y.Z/` a partir de las
   carpetas `_template/`), luego ejecuta `make test-all` y las listas de
   verificación manuales de interfaz bajo `doc/features/`.
2. **Sube `version` en `pyproject.toml`.**
3. **Limpia y actualiza `CHANGELOG.md`** — mueve `[Unreleased]` a
   `## [X.Y.Z] — YYYY-MM-DD`, elimina subsecciones vacías, mantén un
   bloque Added/Changed/Fixed/Security claro.
4. **Limpia y actualiza `doc/roadmap.md`** — línea de estado, Now / Next,
   elimina del plan activo los elementos ya lanzados.
5. **Actualiza `doc/prd.md`** (y `doc/api.md` si cambió la API pública).
6. **Añade capturas de pantalla** bajo
   `doc/releases/X.Y.Z/screenshots/`; escribe borradores de difusión bajo
   `doc-dev/releases/X.Y.Z/` (nunca sincronizados públicamente).
7. **Fusiona a `main`** en `streamlit-coco-dev`.
8. **Sincroniza el árbol público:**
   ```bash
   DRY_RUN=1 make sync-release                       # vista previa
   COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release   # escribe + push
   ```
   Clon de destino por defecto: `../streamlit-coco`. Remoto por defecto:
   `https://github.com/lletourmy/streamlit-coco.git`. Ambos pueden
   sobrescribirse con `RELEASE_REPO=` / `RELEASE_REMOTE=`. Excluido del
   árbol de sincronización público: `.cursor/`, `.agents/`, `.claude/`,
   `doc-dev/`, `apps/`, cachés locales, `dist/`, y el propio script de
   sincronización (también excluido de la build del sdist vía el
   `[tool.hatch.build.targets.sdist].exclude` de `pyproject.toml`).
9. **Etiqueta en `lletourmy/streamlit-coco`, no en `-dev`:**
   ```bash
   cd ../streamlit-coco
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```
10. El flujo de GitHub Release (`release.yml`) entonces:
    - crea un GitHub Release con notas extraídas de `CHANGELOG.md`;
    - construye sdist + wheel (`uv build`);
    - genera un SBOM CycloneDX (`sbom-vX.Y.Z.cdx.json`) y lo adjunta al
      Release;
    - publica en PyPI — **omitido para tags `-rc` / `-beta` /
      `-alpha`.**
11. **Verifica:**
    ```bash
    pip install "streamlit-coco[sdk]==X.Y.Z"
    ```

### Fallback de publicación manual/local

Desde un árbol limpio ya sincronizado (o `-dev` si es inevitable):

```bash
make build      # uv build -> dist/
make publish    # uv publish — necesita credenciales si el Trusted Publisher no está disponible
```

Prefiere la ruta de CI etiquetada en `lletourmy/streamlit-coco` sobre
este fallback.

## Desinstalación

streamlit-coco es una librería, no un servicio — no hay ningún
procedimiento de desmontaje separado más allá de eliminar el paquete:

```bash
pip uninstall streamlit-coco
# o
uv remove streamlit-coco
```

Eliminar el paquete no toca nada que haya escrito en tiempo de ejecución
(ver [operations](operations.html) Limpieza) — esos artefactos se
limpian por separado si es necesario.

## Procedimiento de release

Este es el mismo flujo que **Proceso de publicación** arriba; no hay
ningún runbook de release separado que mantener sincronizado. Cortar un
release significa completar los pasos numerados de esa sección en orden.
