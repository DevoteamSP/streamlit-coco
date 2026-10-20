# Référence API

L'API Python publique de `streamlit-coco`, telle qu'exportée depuis
`streamlit_coco` (voir l'[index](../index.html) pour la version exacte que
décrit ce guide). Les modules privés (`bridge`, `tool_cards`,
`tool_extract`, et d'autres non listés ici) sont des détails
d'implémentation, pas une API stable — ils ne sont pas documentés comme
entrées de référence.

## `CocoOptions`

Le dataclass de configuration pour une session ou un appel `query()`
(`streamlit_coco/options.py`).

| Champ | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `connection` | `str \| None` | `None` | Nom de la connexion CLI Snowflake à utiliser |
| `cwd` | `str` | `"."` | Répertoire de travail dans lequel opèrent les outils de l'agent |
| `model` | `str \| None` | `None` | Sélection du modèle ; préférez `"auto"` si défini |
| `allowed_tools` | `list[str]` | `[]` | Outils pouvant s'exécuter sans approbation |
| `disallowed_tools` | `list[str]` | `[]` | Outils entièrement bloqués |
| `permission_mode` | `str` | `"default"` | Mode de permission global, ex. `"plan"` pour les flux `ExitPlanMode` |
| `profile` | `str \| None` | `None` | Nom du profil SDK |
| `cli_path` | `str \| None` | `None` | Surcharge le chemin de la CLI `cortex` (la variable d'environnement `CORTEX_CODE_CLI_PATH` fonctionne aussi) |
| `mcp_servers` | `dict` | `{}` | Configuration des serveurs MCP transmise au SDK |
| `hooks` | `dict` | `{}` | Passthrough des hooks SDK |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Outils qui se mettent en pause pour approbation humaine ; `AskUserQuestion`/`ExitPlanMode` se mettent toujours en pause |
| `output_schema` | `dict \| None` | `None` | JSON Schema transmis au SDK sous forme de `output_format` (`$schema`/`$id` retirés avant transmission) |
| `max_turns` | `int \| None` | `None` | Plafonne le nombre de tours de l'agent |
| `approval_timeout_seconds` | `float` | `600.0` | Secondes d'attente d'une approbation en attente avant `ApprovalTimeoutError` |
| `extra_sdk_options` | `dict` | `{}` | Kwargs de passthrough transmis à l'objet options natif du SDK |

### Méthodes

- `options_hash() -> str` — un hash stable des options qui ne change que
  lorsqu'une valeur affectant la session en cours change (utilisé pour
  décider si le worker en arrière-plan doit redémarrer).
- `to_sdk_options(*, can_use_tool=None)` — construit l'objet options natif
  du SDK ; lève `SDKNotInstalledError` si le SDK n'est pas installé.
- `auto_allow_tools() -> list[str]` — l'ensemble effectif des outils qui
  s'exécutent sans approbation.
- `tools_requiring_approval() -> list[str]` — l'ensemble effectif des
  outils qui se mettent en pause pour approbation.

```python
options = st_coco.CocoOptions(
    connection="my_connection",
    cwd=".",
    allowed_tools=["Read", "Glob", "Grep"],
    require_approval_for=["Edit", "Write", "Bash"],
    approval_timeout_seconds=300.0,
)
```

Utilisé par : [Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)

## `CocoRunStatus`

Une énumération `str` (`streamlit_coco/session.py`) donnant l'état courant
d'une session.

| Valeur | Signification |
|---|---|
| `idle` | Aucune activité de session démarrée pour l'instant |
| `connecting` | Le worker en arrière-plan démarre |
| `ready` | Connecté, en attente d'un prompt |
| `running` | Un tour est en cours |
| `awaiting_user` | Un appel d'outil est en pause en attente d'approbation |
| `completed` | Le tour s'est terminé normalement |
| `error` | Le tour ou la session a échoué |
| `cancelled` | Le tour a été annulé |

```python
if session.chat_result().status == st_coco.CocoRunStatus.awaiting_user:
    st.warning("Waiting on an approval.")
```

Utilisé par : [Concepts](concepts.html#cocorunstatus)

## `CocoChatResult`

Un instantané dataclass du résultat d'un tour, retourné par `panel()`,
`chat()` et `session.chat_result()`.

| Champ | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `last_prompt` | `str \| None` | — | Le dernier prompt envoyé |
| `last_result` | `CocoEvent \| None` | — | Le dernier événement terminal |
| `pending_approval` | `dict \| None` | — | La requête d'approbation en attente, le cas échéant |
| `structured_output` | `Any` | — | La dernière charge utile structurée, si `output_schema` était défini |
| `events` | `list[CocoEvent]` | — | Tous les événements de la session jusqu'à présent |
| `status` | `CocoRunStatus` | — | L'état d'exécution courant |

```python
result = session.chat_result()
if result.pending_approval:
    st.info(f"Waiting on: {result.pending_approval['tool_name']}")
```

Utilisé par : [Je veux configurer les approbations d'outils](task-configure-tool-approvals.html)

## `CocoSession`

Une session multi-tours adossée à un `CortexCodeSDKClient` sur un thread en
arrière-plan (`streamlit_coco/session.py`).

| Membre | Effet |
|---|---|
| `send(prompt)` | Met un prompt en file d'attente ; lève `SessionStartError`/`SessionNotReadyError` si non prête |
| `start()` | Démarre le worker en arrière-plan |
| `ensure_ready(timeout=120)` | Attend que la session soit prête ; lève `SessionNotReadyError` en cas de délai dépassé ou d'échec de démarrage |
| `run(prompt, *, timeout=None)` | Envoie un prompt et attend son résultat |
| `stream()` | Itère de façon asynchrone les événements du tour courant/suivant |
| `set_permission_mode(mode)` | Change le mode de permission |
| `execute_plan(...)` | Exécute un plan produit sous `permission_mode="plan"` |
| `cancel()` | Annule le tour en cours |
| `close()` | Arrête le worker en arrière-plan |
| `reset()` | Efface l'historique de conversation et redémarre le worker |
| `chat_result()` | Retourne le `CocoChatResult` courant |
| `is_running` / `is_ready` / `is_connecting` / `needs_polling` | Propriétés d'état booléennes |
| `transcript` / `messages` / `events` | L'historique accumulé des tours/événements |
| `last_error` / `init_info` / `structured_output` | Diagnostics et la dernière charge utile structurée |
| `permission_manager` | Le gestionnaire d'état d'approbation de la session |
| `add_event_listener(cb)` | Enregistre un callback invoqué pour chaque nouvel événement |
| `sync_options(options)` | Applique un nouveau `CocoOptions` ; redémarre le worker si `options_hash()` a changé |
| `set_show_structured_inline(bool)` | Bascule le rendu en ligne de la sortie structurée |

```python
session = st_coco.CocoSession(options=options, key="copilot")
session.start()
result = await session.run("List the tables in my schema.")
```

Utilisé par : [Je veux exécuter CoCo en headless](task-run-headless.html)

### Helpers du registre de sessions

| Fonction | Effet |
|---|---|
| `get_session(key) -> CocoSession \| None` | Recherche une session existante par clé dans le registre du processus |
| `get_or_create_session(options, *, key="coco", sync_options=True) -> CocoSession` | Helper Streamlit : récupère ou crée une session dans `st.session_state[key]` |
| `reset_session(options, session_key="coco", warm_up=False) -> CocoSession` | Réinitialise (ou crée) la session à `session_key` |
| `stop_session(session_key="coco", gate_key="coco_started") -> None` | Arrête la session et efface l'indicateur de la porte d'accès |

```python
session = st_coco.get_or_create_session(options, key="coco")
```

Utilisé par : [Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)

## Interface — pattern préféré

### `panel(session, **kwargs) -> CocoChatResult`

Affiche l'historique de conversation natif ou la sortie de champ, les
contrôles d'approbation, et un bouton Stop pour une session.

| Paramètre | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `output_mode` | `str` | `"transcript"` | `"transcript"` ou `"field"` |
| `output_label` | `str \| None` | `"CoCo output"` | `None` masque le conteneur de sortie bordé |
| `show_tool_details` | `bool` | `True` | Affiche le détail des cartes d'outils |
| `show_thinking` | `bool` | `False` | Affiche les blocs de réflexion |
| `show_approvals` | `bool` | `True` | Affiche les contrôles d'approbation |
| `show_stop` | `bool` | `True` | Affiche le bouton Stop pendant le polling |
| `show_status` | `bool` | `True` | Affiche l'habillage de statut de connexion/tour |
| `show_plan_banner` | `bool` | `True` | Affiche la bannière du mode plan et l'appel à l'action Execute plan |
| `warm_up` | `bool` | `False` | Appelle `session.start()` au montage si inactive |
| `status_expanded` | `str` | `"auto"` | `"auto"` / `"always"` / `"never"` |
| `approval_key_prefix` | `str` | `"coco"` | Espace de noms des clés de widget |
| `use_fragment` | `bool` | `True` | Sonde à l'intérieur d'un `@st.fragment` |
| `run_every` | `float` | `0.25` | Intervalle de sondage en secondes ; en pause tant qu'une approbation est en attente |
| `text_renderer` | `str \| Callable \| None` | `None` | `"markdown"` (défaut) / `"write"` / `"text"` / `"caption"` / `"code"` ou un callable |
| `show_copy` | `bool` | `True` | Affiche les contrôles de presse-papiers |
| `max_messages` | `int \| None` | `None` | Fenêtre de l'historique de conversation ; **Load earlier** révèle des éléments plus anciens |
| `preview_chars` | `int \| None` | `None` | Plafonne le texte utilisateur/assistant aux N premiers caractères |
| `on_structured_output` | `Callable[[dict, CocoChatResult], None] \| None` | `None` | Appelé quand une charge utile structurée arrive |
| `structured_output_container` | conteneur \| `None` | `None` | Conteneur dans lequel rendre la sortie structurée |

```python
st_coco.panel(session, output_mode="transcript", show_thinking=False)
```

Utilisé par : [Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)

### `copilot_rail(session, *, title="Copilot", …) -> None`

Un Copilot en rail à droite autour de `panel()`, pour les apps multipages.

| Paramètre | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `session` | `CocoSession` | — | La session à afficher |
| `connected` | `bool` | `True` | Si le rail s'affiche comme connecté |
| `connections` | `list \| None` | `None` | Choix de connexion, si le changement est proposé |
| `toml_file` | `str \| None` | `None` | Fichier de configuration Snowflake d'où lire les connexions |
| `on_connect` / `on_disconnect` | `Callable \| None` | `None` | Callbacks de cycle de vie de la connexion |
| `job` | `dict \| None` | `None` | Un job en file d'attente : `{prompt, label, status, expect_structured}` |
| `on_job_sent` / `on_job_finished` | `Callable \| None` | `None` | Callbacks de cycle de vie du job |
| `show_copy` | `bool` | `False` | Affiche les contrôles de presse-papiers |
| `show_transcript_filters` | `bool` | `True` | Affiche le popover de configuration d'affichage de l'historique |
| `example_questions` | `list \| None` | `None` | Dicts `{title, question}` ou tuples `(title, question)` |
| `deferred` | `bool` | `False` | Diffère le rendu (aussi réglable par question exemple) |

```python
st_coco.copilot_rail(session, title="Copilot", example_questions=[
    ("Summarize", "Summarize this sprint."),
])
```

Utilisé par : [Référence des exemples d'apps](reference-examples.html)

### `transcript_display_config` / `transcript_view_pills`

`transcript_display_config(*, key=…, last_n=8, preview_chars=200) -> tuple[int | None, int | None]`
— le popover de l'icône de paramètres d'affichage (`:material/display_settings:`)
avec les pills et curseurs Last messages / First n characters.

`transcript_view_pills(*, key=…, last_n=8, preview_chars=200)` — les mêmes
pills en tant que widget autonome, sans l'habillage du popover.

```python
last_n, preview_chars = st_coco.transcript_display_config(key="rail")
```

Utilisé par : [Concepts](concepts.html#the-transcript)

### `app_viewer(app_dir, *, key="coco_app_viewer", …) -> None`

Intègre un aperçu en direct d'une app que l'agent vient d'écrire.

| Paramètre | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `app_dir` | `str` | — (requis) | Dossier contenant `streamlit_app.py` |
| `key` | `str` | `"coco_app_viewer"` | Espace de noms des clés de widget |
| `port` | `int \| None` | `None` | Premier port libre entre 8511 et 8520 si non défini |
| `address` | `str` | `"127.0.0.1"` | Adresse de liaison pour le processus d'aperçu |
| `env` | `dict \| None` | `None` | Variables d'environnement supplémentaires pour le processus enfant |
| `iframe_height` | `int` | `520` | Hauteur de l'iframe d'aperçu en pixels |
| `show_fix` | `bool` | `True` | Affiche l'action « Fix with CoCo » |
| `on_fix` | `Callable[[str], None] \| None` | `None` | Callback recevant le prompt de correction |
| `on_close` | `Callable \| None` | `None` | Callback à la fermeture de l'aperçu |
| `title_extra` | `str \| None` | `None` | Texte supplémentaire ajouté au titre |
| `title` | `str` | `"Preview"` | Titre du panneau |
| `script_name` | `str` | `"streamlit_app.py"` | Nom du fichier du point d'entrée à l'intérieur de `app_dir` |

Fonctions helpers sans Streamlit : `start_app_preview`, `stop_app_preview`,
`preview_running`, `preview_url`, `last_preview_exception`,
`preview_log_tail`, `default_fix_prompt(traceback, app_dir) -> str`.

```python
st_coco.app_viewer("examples/app_builder/out/my-app", title="Preview")
```

Utilisé par : [Je veux exécuter les exemples d'apps](task-run-the-example-apps.html)

### `chat_input_bar(session, *, placeholder=…, connecting_placeholder=…, key=None, accept_file=False, …) -> str | None`

La barre de saisie du chat, avec pièce jointe optionnelle.

| Paramètre | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `accept_file` | `bool \| str` | `False` | `True` ou `"multiple"` pour accepter des téléversements |
| `file_type` | `list[str] \| None` | `None` | Restreint les extensions acceptées |
| `max_upload_size` | `int \| None` | `None` | Surcharge la taille de téléversement maximale par défaut |
| `upload_subdir` | `str` | `"_uploads"` | Sous-répertoire de `cwd` où sont écrits les téléversements |
| `upload_overwrite` | `str` | `"replace"` | `"error"` / `"replace"` / `"skip"` |
| `inject_upload_paths` | `bool` | `True` | Ajoute les chemins des fichiers téléversés au texte du prompt |

```python
prompt = st_coco.chat_input_bar(session, accept_file=True, upload_overwrite="replace")
```

Utilisé par : [Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html)

## Helpers de téléversement

### `upload_to_cwd(target, files, *, subdir="_uploads", overwrite="error", max_bytes=DEFAULT_MAX_BYTES, allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS) -> list[UploadedPath]`

Écrit les fichiers téléversés dans le répertoire de travail d'une session,
d'options, ou d'un chemin. `target` peut être un chemin, un `CocoOptions`,
ou un `CocoSession`. Lève `CwdUploadError` en cas de nom de fichier
invalide (garde-fou contre le path-traversal), d'extension interdite, de
charge utile trop volumineuse, ou de conflit d'écrasement.

```python
paths = st_coco.upload_to_cwd(session, files, overwrite="error")
```

Utilisé par : [Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html)

### `cwd_uploader(target, *, label=…, overwrite="error", …) -> list[UploadedPath]`

Un `st.file_uploader` de barre latérale/habillage câblé à `upload_to_cwd()`,
avec une légende d'inventaire des fichiers déjà téléversés.

```python
uploaded = st_coco.cwd_uploader(session, label="Upload a reference file")
```

Utilisé par : [Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html)

### Constantes de téléversement (`streamlit_coco/upload.py`)

| Nom | Type | Valeur par défaut | Effet |
|---|---|---|---|
| `DEFAULT_UPLOAD_SUBDIR` | `str` | `"_uploads"` | Nom du sous-répertoire de téléversement par défaut |
| `DEFAULT_MAX_BYTES` | `int` | `10 * 1024 * 1024` (10 Mio) | Limite de taille par fichier par défaut |
| `DEFAULT_ALLOWED_EXTENSIONS` | `frozenset[str]` | une liste blanche fixe | Extensions de fichiers autorisées par défaut ; lisez la constante source pour la liste exacte plutôt que d'en supposer une |

Utilisé par : [Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html)

## Approbations et envoi de prompts

### `send_prompt(session, prompt) -> None`

Nettoie et met en file d'attente un prompt sur une session ; affiche toute
`CocoError` via `st.error` au lieu de la laisser remonter dans la page.

```python
st_coco.send_prompt(session, "Summarize this sprint.")
```

Utilisé par : [Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)

### `render_approvals(session, *, key_prefix="coco") -> bool`

Affiche l'interface d'approbation HITL pour une requête en attente. Ordre
des boutons : **Approve once** · **Always allow** · **Deny**. Les requêtes
`AskUserQuestion` et `ExitPlanMode` n'affichent jamais **Always allow**.

```python
st_coco.render_approvals(session, key_prefix="coco")
```

Utilisé par : [Je veux configurer les approbations d'outils](task-configure-tool-approvals.html)

### `render_plan_banner(session, …) -> bool`

Affiche la bannière du mode plan avec un appel à l'action **Execute plan**.

```python
st_coco.render_plan_banner(session)
```

Utilisé par : [Je veux configurer les approbations d'outils](task-configure-tool-approvals.html)

### `approve_pending(session, request_id, *, always=False, updated_input=None)` / `deny_pending(session, request_id, *, reason=None)`

Résolveurs bas niveau pour une approbation en attente, pour des interfaces
d'approbation personnalisées.

```python
st_coco.approve_pending(session, request_id, always=False)
st_coco.deny_pending(session, request_id, reason="not now")
```

Utilisé par : [Je veux configurer les approbations d'outils](task-configure-tool-approvals.html)

## Helpers d'affichage

| Fonction | Effet |
|---|---|
| `render_transcript(session, …, text_renderer=None)` | Affiche l'historique de conversation de façon autonome (ce qu'utilise `panel()` en interne) |
| `render_output_field(session, …, text_renderer=None)` | Affiche uniquement le dernier champ de sortie |
| `render_session_status(session, …)` | Affiche l'habillage de statut/connexion de façon autonome |
| `get_latest_assistant_text(session) -> str` | Retourne le dernier texte de l'assistant sous forme de simple chaîne |

```python
latest = st_coco.get_latest_assistant_text(session)
```

Utilisé par : [Concepts](concepts.html#the-transcript)

## Amorçage et porte d'accès

### `render_environment_status(env=None, *, connection=None, toml_file=None, stacked=False, show_title=True)`

Affiche le bloc de statut SDK/CLI/config Snowflake, à partir d'un
`CocoEnvironment` donné (ou en en vérifiant un lui-même si `env` est omis).

```python
st_coco.render_environment_status(connection="my_connection")
```

Utilisé par : [Prise en main](getting-started.html)

### `render_start_gate(options, *, session_key=…, gate_key=…, warm_up=True, env=None) -> bool`

Affiche l'écran d'accueil (statut de l'environnement plus une action
**Start**) et retourne `False` tant que l'environnement n'est pas prêt ou
que l'utilisateur n'a pas confirmé. L'appelant doit appeler `st.stop()` sur
`False` — la porte d'accès n'arrête pas le script elle-même.

```python
if not st_coco.render_start_gate(options):
    st.stop()
```

Utilisé par : [Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)

## CCv2 legacy

### `chat(**kwargs) -> CocoChatResult`

Un widget Custom Component v2 tout-en-un avec une saisie intégrée,
antérieur à `panel()`. Préférez `panel()` pour les nouvelles apps.
Paramètres notables : `session` / `options`, `key`, `height`, `placeholder`,
`use_fragment`, `run_every`, `output_mode`, `on_structured_output`, et des
callbacks optionnels `on_event` / submit / approval / cancel.

```python
result = st_coco.chat(options=options, key="legacy")
```

Utilisé par : [Je veux exécuter les exemples d'apps](task-run-the-example-apps.html)

### `request_input(question, *, key="coco_input", default="", schema=None, …) -> str | dict | None`

Un formulaire de clarification possédé par l'app, affiché entre deux tours
— pas un canal CCv2. Retourne un `dict` quand `schema=` est fourni, sinon
une `str` (ou `None` si sans réponse).

```python
answer = st_coco.request_input("Which environment?", schema={"type": "string"})
```

Utilisé par : [Référence des exemples d'apps](reference-examples.html)

## Headless

### `async query(prompt, *, options=None, output_schema=None) -> AsyncIterator[CocoEvent]`

Un wrapper à tour unique qui s'exécute sans aucun objet session ni import
Streamlit. Lève `SDKNotInstalledError`, `QueryError`, ou une autre
sous-classe `CocoError` en cas d'échec.

```python
async for event in st_coco.query("List the tables in my schema.", options=options):
    ...
```

Utilisé par : [Je veux exécuter CoCo en headless](task-run-headless.html)

### `events_to_dataframe(events) -> DataFrame`

Aplatit une liste de `CocoEvent` en `DataFrame` pandas (nécessite pandas
installé).

```python
df = st_coco.events_to_dataframe(session.events)
```

Utilisé par : [Je veux exécuter CoCo en headless](task-run-headless.html)

## `CocoEvent`

Une unité normalisée et sérialisable en JSON d'activité de l'agent
(`streamlit_coco/messages.py`), avec `to_dict()` / `from_dict()` pour le
stockage ou le transport.

| Champ | Effet |
|---|---|
| `type` | L'une de `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error` |
| `text` / `delta` | Contenu texte ou delta en streaming |
| `name` / `tool_use_id` / `tool_name` / `tool_input` / `input` | Identification et arguments de l'appel d'outil |
| `content` / `is_error` | Contenu du résultat d'outil et indicateur d'erreur |
| `request_id` | Identifie une requête d'approbation en attente |
| `subtype` / `duration_ms` / `cost_usd` | Métadonnées de résultat |
| `structured_output` | La charge utile structurée, quand présente |
| `message` / `code` / `metadata` | Détail d'erreur/système |

```python
event = st_coco.CocoEvent.from_dict(raw)
event.to_dict()
```

Utilisé par : [Concepts](concepts.html#cocoevent)

## Environnement et erreurs

### `check_environment(*, connection=None, cli_path=None, toml_file=None) -> CocoEnvironment`

Vérifie le SDK, la CLI et la configuration Snowflake. Ne lève jamais
d'exception.

| Champ / propriété | Effet |
|---|---|
| `sdk_installed` / `sdk_version` | Si le SDK est importable, et sa version |
| `cli_path` / `cli_version` | Le chemin de la CLI résolu et sa version rapportée |
| `snowflake_config_file` / `connection_hint` / `toml_file` | Détail de résolution de la configuration Snowflake |
| `ready` | `True` quand tout ce qu'il faut pour démarrer une session est présent |
| `cli_ok` | `True` quand la CLI a été vérifiée avec succès |
| `snowflake_config_found` / `snowflake_config_display` / `snowflake_config_missing_label` | Présence de la configuration Snowflake et texte d'affichage |

```python
env = st_coco.check_environment(connection="my_connection")
```

Utilisé par : [Prise en main](getting-started.html)

### `require_environment(*, connection=None, cli_path=None, toml_file=None, require_snowflake_config=False) -> CocoEnvironment`

Comme `check_environment()`, mais lève une erreur typée au lieu de
retourner un résultat non prêt.

```python
env = st_coco.require_environment(connection="my_connection", require_snowflake_config=True)
```

Utilisé par : [Prise en main](getting-started.html)

### Helpers de configuration Snowflake

| Fonction | Effet |
|---|---|
| `list_snowflake_toml_files() -> list[Path]` | Fichiers `*.toml` sous `~/.snowflake/`, `connections.toml`/`config.toml` en premier |
| `list_snowflake_connections(toml_file=None) -> list[str]` | Noms de profils ; l'ancien `config.toml` lit `[connections]`, les autres fichiers lisent les tables de premier niveau |
| `resolve_snowflake_config_path(toml_file=None, *, must_exist=True)` | Résout un nom de fichier nu ou un chemin vers un fichier de configuration sous `~/.snowflake/` |
| `default_snowflake_connection_name(toml_file=None)` | Le nom de connexion utilisé quand aucun n'est donné |

```python
files = st_coco.list_snowflake_toml_files()
```

Utilisé par : [Prise en main](getting-started.html)

### Hiérarchie des exceptions (`streamlit_coco/errors.py`)

| Classe | Levée quand | Message |
|---|---|---|
| `CocoError` | Classe de base pour toutes les exceptions ci-dessous | — |
| `SDKNotInstalledError` (aussi `ImportError`) | Le SDK n'est pas installé | `cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | La CLI `cortex` n'est pas sur `PATH` | `CoCo CLI not found on PATH... or set CORTEX_CODE_CLI_PATH.` (ou `not found at {cli_path!r}`) |
| `CLIProbeError` | Le binaire de la CLI existe mais ne répond pas à `--version` | `CoCo CLI at {cli_path!r} did not respond to --version` |
| `SnowflakeConfigNotFoundError` | Aucun fichier de configuration Snowflake trouvé | `No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml)...` |
| `CocoConnectionError` | Nom de connexion invalide ou échec d'authentification | — |
| `SessionStartError` | Le worker en arrière-plan n'a pas réussi à démarrer | — |
| `SessionNotReadyError` | La session n'est pas prête (délai de connexion dépassé / échec de démarrage) | — |
| `ApprovalTimeoutError` (aussi `TimeoutError`) | Aucune réponse d'approbation dans le délai `approval_timeout_seconds` | `Approval timed out for tool {tool_name}` |
| `QueryError` | Un appel `query()` headless a échoué | — |
| `CwdUploadError` | Un téléversement a échoué (taille / extension / chemin / écrasement) | — |

`wrap_exception()` fait correspondre les exceptions brutes SDK/runtime à
celles-ci par message et par un kwarg `context=` (`"session_start"`,
`"session_ready"`/`"session"`, `"query"`, `"approval"`).

```python
try:
    env = st_coco.require_environment(connection="my_connection")
except st_coco.SDKNotInstalledError:
    st.error("Install the SDK: pip install streamlit-coco[sdk]")
```

Utilisé par : [FAQ](faq.html)

## Helpers d'outils

| Fonction | Effet |
|---|---|
| `tool_family(name)` | Associe un nom d'outil à son énumération de famille, pour l'affichage des cartes d'outils |
| `is_sql_tool(name)` | `True` pour l'outil SQL |
| `is_ask_user_question(name)` | `True` pour `AskUserQuestion` |
| `is_exit_plan_mode(name)` | `True` pour `ExitPlanMode` |
| `is_debug_mode(*, session_state=None)` | `True` quand `STREAMLIT_COCO_DEBUG` ou `COCO_DEBUG` est vrai (`1`/`true`/`yes`/`on`, insensible à la casse), ou que `st.session_state["coco_debug"]` est vrai |

```python
if st_coco.is_debug_mode():
    st.caption("Debug mode is on.")
```

Utilisé par : [FAQ](faq.html)

## Métadonnées du package

`st_coco.__version__` — la version du package installé, par exemple
`"0.1.9"`.

```python
import streamlit_coco as st_coco
print(st_coco.__version__)
```

Utilisé par : [Prise en main](getting-started.html)
