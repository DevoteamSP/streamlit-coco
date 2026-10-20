# Concepts

Les objets qu'un utilisateur de `streamlit-coco` manipule directement, ce
qu'ils représentent, leurs états, et où chacun vit dans le code.

## `CocoOptions`

Configuration d'une session CoCo : connexion, répertoire de travail, modèle,
outils autorisés/interdits, mode de permission, règles d'approbation, schéma
de sortie, limite de tours, et passthrough SDK. C'est un dataclass simple
(`streamlit_coco/options.py`) — on en crée un, on le passe à
`get_or_create_session` ou `query()`, et on le modifie (une nouvelle
instance, pas en place) quand les réglages changent.

`CocoOptions` n'a pas de cycle de vie propre : c'est un objet-valeur. Son
`options_hash()` est ce qu'une session compare pour décider si elle doit
redémarrer son worker en arrière-plan — changer `permission_mode` ou
`allowed_tools` entre deux reruns et appeler `sync_options()` déclenche un
redémarrage si le hash diffère.

Touché par chaque page de tâche de ce guide ; le tableau complet des champs
se trouve dans la [Référence API](reference-api.html).

## `CocoSession`

Une conversation multi-tours avec l'agent, adossée à un `CortexCodeSDKClient`
tournant sur un thread en arrière-plan (`streamlit_coco/session.py`). Une
session survit d'un rerun Streamlit à l'autre lorsqu'elle est stockée dans
`st.session_state` via `get_or_create_session()`.

Cycle de vie : créée inactive → `start()` connecte le worker en arrière-plan
→ `send()`/`run()`/`stream()` pilotent les tours → `reset()` efface
l'historique de conversation et redémarre le worker → `close()` arrête le
worker. Une session est retrouvée par sa `key` via `get_session(key)`, et
arrêtée explicitement avec `stop_session()`.

## `CocoRunStatus`

L'état dans lequel se trouve une session (et l'interface construite dessus),
sous forme d'énumération de chaînes : `idle` → `connecting` → `ready` →
`running` → `awaiting_user` → `completed` / `error` / `cancelled`.
`awaiting_user` signifie qu'un appel d'outil est en pause en attente d'une
approbation ; l'interface affiche les contrôles d'approbation et arrête de
sonder pour une nouvelle sortie de l'agent jusqu'à ce que cela soit résolu.
`panel()` et les autres helpers d'affichage lisent cet état pour décider
quel habillage afficher (squelette de statut, bouton Stop, état désactivé
de l'entrée).

## `CocoEvent`

Une unité normalisée et sérialisable en JSON d'activité de l'agent
(`streamlit_coco/messages.py`), avec `to_dict()`/`from_dict()` pour le
stockage ou le transport. Valeurs de `type` courantes : `assistant_text`,
`stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`,
`result`, `system`, `error`. Une session accumule les événements dans
`session.events` ; l'interface d'historique de conversation et
`events_to_dataframe()` consomment tous deux le même flux d'événements. Les
événements n'ont pas de cycle de vie au-delà d'être ajoutés — chacun est un
fait sur quelque chose qui s'est déjà produit.

## `CocoChatResult`

La valeur de retour de `panel()` et `chat()` (CCv2 legacy) : un instantané du
résultat d'un tour — `last_prompt`, `last_result`, `pending_approval`,
`structured_output`, `events`, et `status`. Il est recalculé à chaque rerun
via `session.chat_result()` ; rien n'y est modifié directement.

## `CocoEnvironment`

Le résultat de `check_environment()` : si le SDK est installé, le chemin et
la version de la CLI, et si une configuration Snowflake a été trouvée, plus
les champs nécessaires pour afficher cet état (`connection_hint`,
`toml_file`, `snowflake_config_display`). `check_environment()` ne lève
jamais d'exception — elle retourne toujours un `CocoEnvironment`, pour
qu'un appelant puisse afficher un écran de diagnostic dans tous les cas.
`require_environment()` effectue la même vérification mais lève une erreur
typée (voir [Référence API](reference-api.html)) au lieu de retourner un
résultat non prêt, pour les chemins de code qui doivent s'arrêter net.

## Le modèle d'approbation / permission

Chaque appel d'outil que l'agent veut faire est soit auto-autorisé (dans
`CocoOptions.allowed_tools`, ou reconnu par `permission_mode`), soit mis en
pause pour une décision humaine, selon `require_approval_for` (une liste de
noms d'outils, ou un callable). `AskUserQuestion` et `ExitPlanMode` se
mettent toujours en pause, quelle que soit cette configuration. Un appel mis
en pause devient une approbation en attente sur la session ; elle est
résolue avec l'une de trois issues — **Approve once**, **Always allow**, ou
**Deny** — soit via l'interface `render_approvals()` intégrée à `panel()`,
soit programmatiquement avec `approve_pending()` / `deny_pending()`.
« Always allow » est limité à la session en cours uniquement : c'est effacé
au `reset()` ou au redémarrage du processus, jamais écrit dans une politique
persistée. Voir
[Je veux configurer les approbations d'outils](task-configure-tool-approvals.html).

## L'historique de conversation

La séquence ordonnée des tours et événements qu'une session a produits,
telle que rendue par `render_transcript()` (utilisé dans `panel()` en
`output_mode="transcript"`) ou lue via `session.transcript` /
`session.messages`. Les paramètres d'affichage uniquement (`max_messages`,
`preview_chars`, `text_renderer`) contrôlent combien en est montré et
comment, sans changer ce qui est stocké — « Load earlier » révèle davantage
du même historique sous-jacent, cela n'en récupère pas de nouveau.

## Glossaire

| Terme | Définition |
|------|------------|
| `CocoOptions` | Objet-valeur de configuration pour une session ou un appel `query()` |
| `CocoSession` | Une conversation multi-tours, adossée à un thread worker SDK en arrière-plan |
| `CocoRunStatus` | L'état courant de la session (`idle` … `completed`/`error`/`cancelled`) |
| `CocoEvent` | Une unité normalisée d'activité de l'agent (texte assistant, usage d'outil, résultat, …) |
| `CocoChatResult` | Instantané du résultat d'un tour, retourné par `panel()`/`chat()` |
| `CocoEnvironment` | Résultat d'une vérification d'environnement (disponibilité SDK/CLI/config Snowflake) |
| Approval gate (verrou d'approbation) | Le flux de pause-et-résolution pour un appel d'outil reconnu par `require_approval_for` |
| « Always allow » | Une approbation limitée à la session (non persistée) qui saute les futures invites pour cet outil |
| Historique de conversation (transcript) | L'historique ordonné des tours/événements d'une session |
| `cwd` | Le répertoire de travail dans lequel opèrent les outils de l'agent (`CocoOptions.cwd`) |
| Headless | Exécuter `query()` ou `CocoSession` sans aucune interface Streamlit |
