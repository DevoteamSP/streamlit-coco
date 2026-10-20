# Référence des commandes

Chaque cible `make` du `Makefile` du dépôt qu'un utilisateur de la
bibliothèque exécute directement. Il n'y a pas d'entrée
`[project.scripts]` — toutes les commandes passent par `make`.

## `make install`

Synopsis : `make install`

Installe le package avec ses extras `dev`, en mode éditable, via `uv`
(`uv sync --extra dev`). `make sync` est un alias de la même cible.

Sortie : une installation éditable dans l'environnement virtuel actif.

## `make run`

Synopsis : `make run [EXAMPLE=<path>]`

| Variable | Valeur par défaut | Effet |
|---|---|---|
| `EXAMPLE` | `examples/chat_app.py` | Le script d'exemple à exécuter |

Exécute l'exemple donné avec `streamlit run`. Sortie : l'app s'ouvre dans le
navigateur par défaut sur le prochain port Streamlit libre.

## `make chat`

Synopsis : `make chat`

Exécute `examples/chat_app.py` — la démo au pattern préféré. Voir
[Je veux exécuter les exemples d'apps](task-run-the-example-apps.html) et
[Référence des exemples d'apps](reference-examples.html).

## `make approval`

Synopsis : `make approval`

Exécute `examples/approval_gate.py` — la démo `chat()` CCv2 legacy.

## `make structured`

Synopsis : `make structured`

Exécute `examples/structured_output.py` — la démo `output_schema` /
`on_structured_output`.

## `make headless`

Synopsis : `make headless`

Exécute `examples/headless_pipeline.py` depuis un terminal, sans aucun
Streamlit. Sortie : texte d'événements en streaming dans le terminal.

## `make cwd-upload`

Synopsis : `make cwd-upload`

Exécute `examples/cwd_upload_chat.py` — la démo de téléversement de
fichiers.

## `make backlog`

Synopsis : `make backlog`

Exécute le Product Backlog Desk (`examples/backlog_desk/`) — une démo
multipage adossée à des fichiers/JSON, avec un Copilot en rail à droite.
Les fichiers de sortie atterrissent sous `examples/backlog_desk/data/` ;
voir [Sorties](outputs.html).

## `make bi-semantic`

Synopsis : `make bi-semantic`

Exécute BI → Semantic (`examples/bi_to_semantic/`). `make tableau-semantic`
est un alias déprécié de la même cible. Les fichiers de sortie atterrissent
sous `examples/bi_to_semantic/out/` ; voir [Sorties](outputs.html).

## `make app-builder`

Synopsis : `make app-builder`

Exécute App Builder (`examples/app_builder/`). Les fichiers de sortie
atterrissent sous `examples/app_builder/out/<slug>/` ; voir
[Sorties](outputs.html).

## `make e2e-harness`

Synopsis : `make e2e-harness`

Exécute le harnais UX sans CoCo (`examples/e2e_ux_harness.py`) utilisé par
la suite end-to-end Playwright — aucun agent en direct impliqué.

## `make test`

Synopsis : `make test`

Exécute la suite de tests unitaires/smoke : `pytest tests/ --ignore=tests/e2e -v`.

## `make lint`

Synopsis : `make lint`

Exécute `ruff check .`.

## `make format`

Synopsis : `make format`

Exécute `ruff format . && ruff check --fix .`.

## `make check`

Synopsis : `make check`

Exécute `make lint` puis `make test`.

## `make e2e-install`

Synopsis : `make e2e-install`

Installe l'extra `e2e` et le navigateur Chromium pour Playwright. À exécuter
une fois avant le premier `make e2e`.

## `make e2e`

Synopsis : `make e2e`

Exécute la suite end-to-end UX Playwright (`tests/e2e`, marqueur `e2e`)
contre `make e2e-harness`.

## `make audit`

Synopsis : `make audit`

Exécute `pip-audit --skip-editable` — une analyse de vulnérabilités des
dépendances.

## `make test-all`

Synopsis : `make test-all`

Exécute `make check` + `make e2e` + `make audit` — le gate automatisé
complet.

## Autres cibles (destinées aux mainteneurs)

Ces cibles existent pour couper et publier une release plutôt que pour
utiliser la bibliothèque au quotidien ; elles sont couvertes dans le Guide
Technique `upgrade-and-release.html`, non répétées ici :

| Cible | Effet |
|---|---|
| `make build` | Construit le sdist + wheel dans `dist/` (`uv build`) |
| `make publish` | Envoie `dist/` vers PyPI (`uv publish`) |
| `make sync-release` | Synchronise l'arbre de release vers `../streamlit-coco` (`DRY_RUN=1` / `COMMIT=1` / `PUSH=1`) |
| `make clean` | Supprime les caches et artefacts de build |
| `make adoption-stats` / `make adoption-chart` | Collecte/reconstruit les métriques PyPI et de trafic GitHub sous `doc-dev/metrics/` — hors périmètre de ce guide |
