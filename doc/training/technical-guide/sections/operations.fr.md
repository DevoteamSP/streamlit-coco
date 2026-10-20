# Opérations

## Exécution

Il n'y a pas de processus serveur autonome pour la bibliothèque elle-même —
elle s'exécute au sein de l'application Streamlit qui l'embarque. Les
applications d'exemple s'exécutent via des cibles Makefile :

| Cible | Exécute |
|---|---|
| `make run` | `examples/chat_app.py` (`EXAMPLE` par défaut) |
| `make chat` | `examples/chat_app.py` |
| `make approval` | `examples/approval_gate.py` (CCv2 historique) |
| `make structured` | `examples/structured_output.py` |
| `make headless` | `examples/headless_pipeline.py` (sans Streamlit) |
| `make backlog` | `examples/backlog_desk/` |
| `make cwd-upload` | `examples/cwd_upload_chat.py` |
| `make bi-semantic` (alias `make tableau-semantic`) | `examples/bi_to_semantic/` |
| `make app-builder` | `examples/app_builder/` |

Ou lancez n'importe quel exemple Streamlit directement :
`uv run streamlit run examples/chat_app.py`.

## Planification

Non applicable. streamlit-coco n'a ni planificateur, ni exécuteur de jobs
en arrière-plan, ni composant piloté par cron. Chaque exécution est
interactive, démarrée en ouvrant une application Streamlit.

## Surveillance

- La transcription de l'agent n'existe que dans l'état de session
  Streamlit, en mémoire, pour la durée de vie de la session du navigateur.
  Rien n'est persisté par défaut.
- `app_viewer()` écrit `.preview.log`, `.preview.pid`, et `.preview.port`
  dans le `app_dir` prévisualisé pendant qu'un processus d'aperçu enfant
  tourne — c'est le seul journal sur disque que produit la bibliothèque, et
  il est limité au sous-processus d'aperçu, pas à la session de l'agent.
- Il n'existe pas de journal d'audit d'approbation persistant (qui a
  approuvé quel appel d'outil, quand) — c'est l'élément ouvert **SEC-01** ;
  voir [security](security.html) et [limits](limits.html).
- La visibilité de debug sur les charges utiles brutes des outils est
  contrôlée par `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` (voir
  [configuration](configuration.html)) ; cela change ce qui est *affiché
  dans l'UI*, pas ce qui est écrit sur disque.

## Coût et latence

Les appels LLM passent par Snowflake Cortex via le CLI/SDK CoCo. Le coût et
la latence de ces appels relèvent de Snowflake Cortex — streamlit-coco ne
suit, ne rapporte, ni ne budgète les tokens, les crédits d'entrepôt, ou la
latence des appels. `CocoEvent` porte un champ `cost_usd` et un champ
`duration_ms` quand le message SDK sous-jacent les fournit, mais la
bibliothèque n'agrège, ne persiste, ni n'alerte sur ces valeurs ; une
application qui veut un suivi coût/latence doit lire ces champs elle-même,
événement par événement.

## Nettoyage

Entre deux exécutions de démo ou lors du démontage d'une session :

- `stop_session(session_key="coco", gate_key="coco_started")` — démonte la
  `CocoSession` (ferme le worker en arrière-plan) et efface le drapeau de
  start-gate, de sorte que l'application retourne à l'écran de start-gate.
- `session.close()` — ferme une session spécifique sans toucher au drapeau
  de start-gate.
- Tuez tout processus d'aperçu en cours avant de changer de `app_dir` sur
  `app_viewer()` : utilisez `stop_app_preview()` (ou le bouton **Stop**
  dans l'UI). Un seul processus d'aperçu tourne par `app_dir` à la fois
  (voir [limits](limits.html)).
- Nettoyez les artefacts générés entre les passages de démo au besoin :
  `_uploads/` sous le `cwd` de l'agent (téléversements navigateur),
  `examples/bi_to_semantic/out/` et
  `examples/bi_to_semantic/../workspaces/bi_to_semantic/` (dans
  `.gitignore`), `examples/app_builder/out/<slug>/` (projets d'application
  nommés — supprimez via l'action **Delete app** de la Library/du Brief ou
  en retirant le dossier). Aucun de ces répertoires n'est nettoyé
  automatiquement.
