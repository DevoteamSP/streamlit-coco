# Tests et CI

## Arborescence de tests

```text
tests/            unitaires + smoke (`make test` par défaut ; 17 fichiers)
tests/e2e/         e2e UX Playwright (conftest.py + 3 specs UX)
examples/e2e_ux_harness.py   harnais sans CoCo que la suite e2e pilote
```

Fichiers de tests unitaires notables : `test_core.py`, `test_errors.py`,
`test_upload.py`, `test_copilot_rail.py`, `test_app_viewer.py`,
`test_snowflake_toml.py`, `test_ndjson_fixtures.py`, `test_backlog_desk.py`,
`test_bi_to_semantic_parse.py`, `test_app_builder_catalog.py`,
`test_app_builder_profile.py`, `test_rich_text.py`, `test_smoke.py`.

## Comment lancer chaque porte

| Porte | Commande | Couvre |
|---|---|---|
| Rapide | `make check` | `ruff check .` + `pytest tests/ --ignore=tests/e2e -v` |
| Navigateur UX | `make e2e` | Playwright contre `examples/e2e_ux_harness.py` — pas d'agent CoCo en direct. Première fois : `make e2e-install` (installe l'extra `[e2e]` + Chromium). |
| Sécurité | `make audit` | `pip-audit --skip-editable` |
| Automatisé complet | `make test-all` | `check` + `e2e` + `audit` |

La suite navigateur couvre : la coloration syntaxique SQL/Python en bloc
délimité, le **Copy** presse-papiers sur les messages assistant, le
`cwd_uploader` de la barre latérale → `_uploads/`, et la troncature
`max_messages` + **Load earlier**.

Les checklists manuelles/en direct (nécessitent un vrai CLI CoCo + une
connexion Snowflake) vivent sous
`doc/features/<feature>/test-checklist.md`, indexées depuis
`doc/features/README.md`. Ordre d'exécution suggéré :
file-upload → panel → tools-display / approvals → optionnellement
structured / headless / approval (CCv2) / bi-semantic.

## Ce que la CI vérifie réellement

`.github/workflows/ci.yml` — à chaque push vers `main` et chaque pull
request ciblant `main` :

- job `test` : `ruff check .`, puis `pytest tests/ --ignore=tests/e2e -v`,
  puis `pip-audit --skip-editable` (cette dernière étape est en
  `continue-on-error: true` — non bloquante tant qu'une base saine n'est
  pas établie).
- job `e2e` : installe l'extra `[e2e]` et Chromium, puis
  `pytest tests/e2e -m e2e -v`. Aucun agent CoCo en direct n'est appelé.

`.github/workflows/security.yml` — sur les pull requests vers `main`, les
push vers `main`, et chaque semaine (lundi 06:00 UTC) :

- job `gitleaks` : installe le binaire CLI Gitleaks (pas
  `gitleaks-action@v2`, qui nécessite une `GITLEAKS_LICENSE` pour les
  dépôts d'organisation GitHub) et lance
  `gitleaks git --verbose --redact --exit-code 1 .`.
- job `pip-audit` : `pip-audit --skip-editable` (aussi en
  `continue-on-error: true`).

**CodeQL ne tourne pas dans la CI de ce dépôt.** Voir
[security](security.html#ci-security-posture-current) pour comprendre
pourquoi, et ne faites pas d'hypothèse d'un job CodeQL en raisonnant sur
les portes de ce dépôt.

`.github/workflows/release.yml` ne s'exécute que sur les push de tags
`v*` : construit sdist+wheel, génère le SBOM, et publie sur PyPI (sauté
pour les suffixes de tag pré-release). Voir
[upgrade-and-release](upgrade-and-release.html).

## Ce qu'il faut ajouter avec un changement

- Un test pour le nouveau comportement : un test unitaire sous `tests/`
  pour le code de la bibliothèque, ou une spec Playwright sous
  `tests/e2e/` pour un comportement UX que la suite navigateur devrait
  détecter (le code délimité, le presse-papiers, le téléversement, et le
  fenêtrage de la transcription sont les précédents existants).
- Une entrée de checklist manuelle sous
  `doc/features/<feature>/test-checklist.md` quand le changement touche
  une fonctionnalité UI qui a besoin d'un CLI CoCo en direct + une
  connexion Snowflake pour être vérifiée (chaque fonctionnalité existante
  a son propre fichier de checklist — ajoutez des lignes au fichier
  pertinent, ou créez un nouveau dossier `doc/features/<feature>/` pour
  une fonctionnalité vraiment nouvelle, en suivant la forme
  `## Preconditions` / `## Golden path` / `## Sign-off` des fichiers
  existants).
- Une entrée `CHANGELOG.md` sous `[Unreleased]` — `Added` / `Changed` /
  `Fixed` / `Security` selon le cas. Les correctifs de sécurité vont
  toujours sous `Security`, jamais `Fixed`.
