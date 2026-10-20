# Configuration

Chaque surface de configuration exposée par streamlit-coco : les champs
`CocoOptions`, les variables d'environnement, et le fichier de connexions
Snowflake qu'elle lit.

## Champs `CocoOptions`

`CocoOptions` (`streamlit_coco/options.py`) est une dataclass. Tous les
champs sont paramétrables par mot-clé ; il n'existe pas de fichier de
configuration pour la bibliothèque elle-même — une application construit une
instance `CocoOptions` en code.

| Nom | Type | Défaut | Effet | Exemple |
|---|---|---|---|---|
| `connection` | `str \| None` | `None` | Nom de connexion Snowflake CLI à utiliser. `None` utilise la connexion par défaut du CLI. | `CocoOptions(connection="analytics")` |
| `cwd` | `str` | `"."` | Répertoire de travail dans lequel opèrent les outils de l'agent (Read/Write/Bash/…). | `CocoOptions(cwd="./workspace")` |
| `model` | `str \| None` | `None` | Identifiant de modèle passé au SDK. Préférez `"auto"` quand il est défini explicitement. | `CocoOptions(model="auto")` |
| `allowed_tools` | `list[str]` | `[]` | Outils pouvant s'exécuter sans invite d'approbation lorsque l'approbation par liste est en vigueur. | `CocoOptions(allowed_tools=["Read", "Glob", "Grep"])` |
| `disallowed_tools` | `list[str]` | `[]` | Outils bloqués purement et simplement, indépendamment de l'approbation. | `CocoOptions(disallowed_tools=["Bash"])` |
| `permission_mode` | `str` | `"default"` | Mode de permission du SDK, par ex. `"plan"` pour les flux `ExitPlanMode`. | `CocoOptions(permission_mode="plan")` |
| `profile` | `str \| None` | `None` | Nom de profil SDK. | `CocoOptions(profile="ci")` |
| `cli_path` | `str \| None` | `None` | Surcharge le chemin vers le binaire CLI `cortex`. Même effet que `CORTEX_CODE_CLI_PATH` ; ce champ est prioritaire quand les deux sont définis. | `CocoOptions(cli_path="/opt/cortex/bin/cortex")` |
| `mcp_servers` | `dict` | `{}` | Configuration de serveur MCP transmise au SDK. | `CocoOptions(mcp_servers={"docs": {...}})` |
| `hooks` | `dict` | `{}` | Configuration de hook SDK. | `CocoOptions(hooks={})` |
| `require_approval_for` | `list[str] \| Callable` | `[]` | Outils qui font une pause pour une approbation human-in-the-loop. `AskUserQuestion` et `ExitPlanMode` invitent toujours à l'approbation, indépendamment de cette liste. Un callable reçoit `(tool_name, tool_input, context)` et renvoie `bool`. | `CocoOptions(require_approval_for=["Edit", "Write", "Bash"])` |
| `output_schema` | `dict \| None` | `None` | JSON Schema transmis au SDK comme `output_format`. La bibliothèque retire `$schema` / `$id` avant de le transmettre (voir [help.html#schema-dollar-schema-rejected](../help.html#schema-dollar-schema-rejected)). | `CocoOptions(output_schema={"type": "object", "properties": {...}})` |
| `max_turns` | `int \| None` | `None` | Plafonne le nombre de tours d'agent dans une exécution. | `CocoOptions(max_turns=10)` |
| `approval_timeout_seconds` | `float` | `600.0` | Secondes à attendre une décision human-in-the-loop avant de lever `ApprovalTimeoutError`. | `CocoOptions(approval_timeout_seconds=120.0)` |
| `extra_sdk_options` | `dict` | `{}` | Kwargs passthrough fusionnés dans les options du SDK, par ex. `add_dirs` pour monter des répertoires supplémentaires (utilisé par les packs de skills `types/` d'App Builder). | `CocoOptions(extra_sdk_options={"add_dirs": ["/path/to/types/shared"]})` |

Deux méthodes à connaître lors de la configuration d'une session :

- `options_hash()` — un hash stable sur les champs qui affectent les
  permissions d'outils. `CocoSession` ne redémarre son worker en
  arrière-plan que lorsque ce hash change entre deux appels (voir
  [architecture](architecture.html)).
- `to_sdk_options(*, can_use_tool=None)` — construit le
  `CortexCodeAgentOptions` du SDK ; lève `SDKNotInstalledError` si
  `cortex-code-agent-sdk` n'est pas installé.

## Variables d'environnement

| Nom | Type | Défaut | Effet | Exemple |
|---|---|---|---|---|
| `CORTEX_CODE_CLI_PATH` | chaîne de chemin | non défini (retombe sur la recherche `PATH`) | Surcharge le chemin du CLI `cortex` utilisé par les diagnostics et la résolution d'options quand il n'est pas sur le `PATH` et que `CocoOptions.cli_path` n'est pas défini. | `export CORTEX_CODE_CLI_PATH=/opt/cortex/bin/cortex` |
| `STREAMLIT_COCO_DEBUG` | `"1"` / `"true"` / `"yes"` / `"on"` (insensible à la casse) | non défini / faux | Affiche les charges utiles brutes de requête/réponse d'outil dans la transcription (« Raw tool payload »). Même effet que `COCO_DEBUG` ; l'une ou l'autre étant vraie active le mode debug. | `export STREAMLIT_COCO_DEBUG=1` |
| `COCO_DEBUG` | même ensemble de valeurs vraies que ci-dessus | non défini / faux | Alias de `STREAMLIT_COCO_DEBUG`. `is_debug_mode()` vérifie aussi `st.session_state["coco_debug"]` quand aucune variable d'environnement n'est définie. | `export COCO_DEBUG=1` |
| `TTS_DATA_MODE` | chaîne | `"disconnected"` quand défini par l'exemple | Lu uniquement par l'application consommatrice générée de `examples/bi_to_semantic` (transmis via `app_viewer(env=...)`), pas par la bibliothèque elle-même. Sélectionne le mode de données déconnecté ou connecté pour cette application générée. | `app_viewer(app_dir, env={"TTS_DATA_MODE": "disconnected"})` |

`is_debug_mode(*, session_state=None)` (réexport de
`streamlit_coco/tool_names.py`, défini dans `streamlit_coco/debug.py`) est
la seule source de vérité pour savoir si l'UI de debug est affichée ; il
vérifie d'abord les deux variables d'environnement, puis
`st.session_state["coco_debug"]`.

## Fichier de connexions Snowflake

CoCo s'authentifie via le propre fichier de connexions du Snowflake CLI,
jamais via la configuration de la bibliothèque :

- Emplacement par défaut : `~/.snowflake/connections.toml`.
- L'ancien `~/.snowflake/config.toml` est aussi détecté (ses profils vivent
  sous une table `[connections]` de premier niveau plutôt que des entrées
  `[connections.<name>]` à la racine).
- Résolution de `toml_file` (utilisée par `check_environment`, le
  sélecteur de fichier de configuration de `copilot_rail`, et
  `list_snowflake_connections`) :
  - un simple nom de fichier est résolu sous `~/.snowflake/` ; un chemin
    est utilisé tel quel.
  - s'il est omis : quand exactement un fichier `*.toml` existe sous
    `~/.snowflake/`, ce fichier est utilisé quel que soit son nom ; avec
    plusieurs fichiers présents, `connections.toml` l'emporte, puis
    `config.toml`, puis les fichiers restants par ordre alphabétique.

Exemple d'entrée de connexion :

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema selon les besoins — voir security.html
```

Aides associées : `list_snowflake_toml_files()`,
`list_snowflake_connections(toml_file=None)`,
`resolve_snowflake_config_path(toml_file=None, *, must_exist=True)`,
`default_snowflake_connection_name(toml_file=None)`. Toutes vivent dans
`streamlit_coco/diagnostics.py` et sont exercées par `check_environment()` /
`require_environment()` — voir [install](install.html) pour le flux de
vérification et
[help.html#snowflake-config-not-found](../help.html#snowflake-config-not-found)
quand la sonde échoue.
