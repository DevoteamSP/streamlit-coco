# Architecture

## Composants

| Composant | Fichier | Rôle |
|---|---|---|
| `CocoOptions` | `streamlit_coco/options.py` | Enveloppe de configuration typée. Se convertit vers le `CortexCodeAgentOptions` du SDK via `to_sdk_options()` ; calcule `options_hash()` afin que le worker en arrière-plan redémarre quand les permissions d'outils changent. |
| `CocoSession` | `streamlit_coco/session.py` | Session multi-tours. Possède un thread en arrière-plan (`threading.Thread`, nommé `coco-session`) qui fait tourner une boucle asyncio enveloppant `CortexCodeSDKClient`. Expose `send`, `run`, `stream`, `cancel`, `reset`, `close`, `execute_plan`, `set_permission_mode`. |
| `PermissionManager` | `streamlit_coco/permissions.py` | Coordonne les callbacks `can_use_tool` du SDK avec les approbations de l'UI. Suit les requêtes en attente, l'ensemble `always_allowed_tools` par session, et résout via `approve_pending` / `deny_pending`. |
| `panel()` / `copilot_rail()` | `streamlit_coco/ui.py`, `streamlit_coco/rail.py` | UI Streamlit native. `panel()` est le primitif transcription/champ/approbations/Stop ; `copilot_rail()` le compose en un Copilot en rail latéral (sélecteur de connexion, jobs en file d'attente, configuration d'affichage de la transcription, questions d'exemple). |
| `app_viewer()` | `streamlit_coco/viewer.py`, `streamlit_coco/app_preview.py` | Colonne d'aperçu pour une application Streamlit générée par CoCo : fait naître un processus enfant `streamlit run`, l'intègre dans une iframe, et propose **Fix with CoCo** en analysant `.preview.log`. |
| `bootstrap` | `streamlit_coco/bootstrap.py` | Start gate piloté par `check_environment` (`render_start_gate`), `get_or_create_session`, `chat_input_bar`, `reset_session`, `stop_session`, `cwd_uploader`. |
| `diagnostics` | `streamlit_coco/diagnostics.py` | `check_environment()` / `require_environment()` — sonde l'installation du SDK, l'accessibilité du CLI, et la configuration Snowflake sans démarrer d'agent. |

Les autres modules sont des détails d'implémentation (pas une API publique
stable), mais comptent pour le travail d'extension : `tool_names.py`
(dispatch outil → `ToolFamily`), `tool_cards.py` / `tool_extract.py` (rendu
par famille et extraction diff/SQL), `text_renderer.py` (rendu de texte
enfichable), `messages.py` (normalisation `CocoEvent` depuis le NDJSON du
SDK), `upload.py` (téléversements navigateur → `cwd`), `ask_user.py` /
`sql_tool.py` (aides UI par outil).

## Plan du dépôt

```text
streamlit_coco/          la bibliothèque (package importable)
  options.py              CocoOptions
  session.py              CocoSession, CocoChatResult, CocoRunStatus
  permissions.py          PermissionManager, approve_pending/deny_pending
  query.py                query() headless
  messages.py             CocoEvent, normalisation NDJSON -> événement
  diagnostics.py          check_environment / require_environment
  bootstrap.py            start gate, chat_input_bar, aides de session
  ui.py                   panel(), render_approvals(), render_plan_banner()
  rail.py                 copilot_rail(), transcript_display_config()
  viewer.py, app_preview.py   app_viewer() et ses aides de processus
  display.py              render_transcript, render_output_field, statut
  upload.py               upload_to_cwd, cwd_uploader
  tool_names.py, tool_cards.py, tool_extract.py   dispatch par famille d'outil
  text_renderer.py        rendu de texte enfichable
  errors.py                hiérarchie typée CocoError
  component.py, frontend/  composant chat() CCv2 historique
examples/                 applications de démonstration de première partie (voir ci-dessous)
tests/                    unitaires + smoke ; tests/e2e/ Playwright
doc/                      documentation produit, sécurité, déploiement, tests
doc/training/             ce pack de formation
.github/workflows/        ci.yml, security.yml, release.yml
Makefile                  cibles install/test/lint/run/build/publish
```

## Flux de données

```text
Application Streamlit
  -> streamlit-coco  (CocoOptions, CocoSession, panel()/copilot_rail())
  -> cortex-code-agent-sdk  (CortexCodeSDKClient, CortexCodeAgentOptions)
  -> CLI CoCo ("cortex")  -- lancé comme sous-processus local
  -> Snowflake Cortex  (LLM + outils, en utilisant le rôle Snowflake connecté)
```

Le thread en arrière-plan de la session pilote le client SDK et reçoit en
retour un flux d'événements NDJSON du sous-processus CLI via un transport
local (pas de saut réseau dans la cible de déploiement locale).
`message_to_events()` / `_blocks_to_events()` dans `messages.py` normalisent
chaque message SDK (`AssistantMessage`, `ResultMessage`, `StreamEvent`, blocs
tool-use/tool-result) en enregistrements `CocoEvent` que l'UI et les
appelants headless consomment tous les deux. Quand un appel d'outil a besoin
d'une approbation, le SDK invoque `can_use_tool` (construit par
`build_can_use_tool()` dans `permissions.py`) ; cet appel **bloque le thread
worker** sur `PermissionManager.wait_for_decision()` jusqu'à ce que l'UI le
résolve (ou que `approval_timeout_seconds` s'écoule, levant
`ApprovalTimeoutError`) — aucun autre outil ne s'exécute sur ce tour tant
que la décision n'est pas prise.

## Invariants à ne pas rompre

- **Les imports headless du cœur ne chargent jamais Streamlit.**
  `CocoSession`, `query`, `CocoOptions`, les fonctions de permission, et la
  hiérarchie d'erreurs s'importent proprement sans qu'aucun import
  `streamlit` ne se trouve sur le chemin — c'est ce qui permet à
  `examples/headless_pipeline.py` de s'exécuter depuis un simple terminal.
  Les exports UI (`panel`, `copilot_rail`, `chat_input_bar`, …) sont résolus
  paresseusement via `streamlit_coco.__getattr__` (`_LAZY_ATTRS` dans
  `streamlit_coco/__init__.py`), pas importés avidement au moment de
  l'import du package.
- **Les points d'approbation interceptent avant l'exécution de l'outil, pas
  après.** `can_use_tool` est le hook pré-exécution du SDK ;
  `PermissionManager` crée la requête en attente et bloque le worker à cet
  endroit. Un outil qui nécessite une approbation ne s'exécute jamais de
  façon spéculative pour être annulé ensuite — il ne s'exécute simplement
  pas tant qu'il n'est pas approuvé.
- **« Always allow » est par session, en mémoire uniquement.** Il vit dans
  `PermissionManager.always_allowed_tools`, un simple `set` sur l'objet
  session. Il n'est jamais écrit sur disque et ne survit jamais à
  `reset()`, `close()`, ou à un redémarrage de processus.
- **`AskUserQuestion` et `ExitPlanMode` n'utilisent jamais « Always
  allow ».** `permissions.py` traite ces deux familles d'outils comme des
  cas particuliers, créant toujours une nouvelle requête d'approbation,
  même si un « always allow » antérieur s'appliquerait autrement.
- **Le worker redémarre quand les permissions d'outils changent, pas à
  chaque modification d'option.** `CocoOptions.options_hash()` ne hache que
  les champs qui affectent ce qu'un outil est autorisé à faire
  (`allowed_tools`, `disallowed_tools`, `permission_mode`,
  `require_approval_for`, `add_dirs`, …) ; `CocoSession` compare ce hash et
  ne redémarre le worker en arrière-plan que lorsqu'il change.
- **`app_viewer()` n'importe jamais `copilot_rail()`, et vice versa.** Le
  composant d'aperçu est agnostique de l'hôte : il ne connaît pas les files
  de jobs. Une application hôte compose les deux et câble `on_fix`
  elle-même.

## Pipeline derrière les commandes de démo du Makefile

| Cible | Exemple | Primitifs câblés |
|---|---|---|
| `make chat` | `examples/chat_app.py` | `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`. Le patron préféré. |
| `make approval` | `examples/approval_gate.py` | `chat()` CCv2 historique — composant tout-en-un avec sa propre saisie intégrée. |
| `make structured` | `examples/structured_output.py` | `CocoOptions.output_schema` + `on_structured_output` acheminant le JSON de l'agent vers un widget d'application plutôt que vers le texte du chat. |
| `make headless` | `examples/headless_pipeline.py` | `query()` et `CocoSession` pilotés depuis du Python `async` pur — aucun import Streamlit nulle part dans l'exécution. |
| `make cwd-upload` | `examples/cwd_upload_chat.py` | `chat_input_bar(accept_file=...)` / `cwd_uploader()` → `upload_to_cwd()` vers le `cwd` de l'agent. |
| `make backlog` | `examples/backlog_desk/` | Application multipage (Board / Epic / Ticket / Release) sur du JSON local, Copilot en rail latéral ouvert depuis un bouton d'en-tête, aucun outil SQL. |
| `make bi-semantic` (alias `make tableau-semantic`) | `examples/bi_to_semantic/` | Analyse déterministe (carte de l'estate, inventaire de KPI) → arbitrage `request_input(schema=...)` → écriture protégée par approbation d'une vue sémantique + politique d'accès en ligne + consommateur généré, prévisualisée via `app_viewer()`. |
| `make app-builder` | `examples/app_builder/` | Un catalogue de types (`types/<id>/type.json`) pilote un brief ; `add_dirs` monte le `SKILL.md` du type (+ `types/shared/SKILL.md`) afin que CoCo écrive `streamlit_app.py` sous approbation ; `copilot_rail()` + `app_viewer()` pour Build/Preview. |

## Orchestration des applications d'exemple

Les trois applications d'exemple qui comptent comme surfaces produit distinctes :

- **`examples/chat_app.py`** — l'implémentation de référence du patron
  préféré (`panel()` + `chat_input_bar`). Le lanceur de prompts de test de
  la barre latérale lit `examples/testdata/prompts.json`.
- **`examples/backlog_desk/`** — premier exemple basé sur un rail, sans
  SQL. Le Copilot n'est pas une page de navigation ; il s'ouvre depuis un
  bouton **Copilot** d'en-tête ou un lien d'action et se ferme avec
  **Close**. Ses « skills » sont des gabarits d'invite (Summarize sprint,
  Draft release notes, Propose ticket update, Check definition of done),
  pas des fichiers `.cortex/skills/`.
- **`examples/bi_to_semantic/`** et **`examples/app_builder/`** — les deux
  exemples qui composent `copilot_rail()` avec `app_viewer()` : une
  écriture CoCo est suivie d'un aperçu en direct de l'application Streamlit
  générée, avec **Fix with CoCo** câblé à `default_fix_prompt()` et un job
  en file d'attente.

Voir [extending](extending.html) pour savoir comment ajouter une quatrième
application d'exemple à cette liste, et
[data-and-contracts](data-and-contracts.html) pour les contrats de fichiers
que chacune lit et écrit.
