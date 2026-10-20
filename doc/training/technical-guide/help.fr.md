# Aide

Par domaine et par symptôme. Chaque titre ci-dessous porte un `{#anchor}`
stable que d'autres pages référencent sous la forme `help.html#<anchor>`.

## Environnement et connexion

### SDK non installé {#sdk-not-installed}

**Symptôme :** `cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk]`
**Cause probable :** `streamlit-coco` a été installé sans l'extra `[sdk]`, donc `cortex_code_agent_sdk` n'est pas importable.
**Diagnostic :** `python -c "import cortex_code_agent_sdk"`
**Correction :** `pip install "streamlit-coco[sdk]"` (ou `make install`, qui lance `uv sync --extra dev`).
**Si cela échoue :** vérifiez que l'environnement Python actif est bien celui à partir duquel Streamlit est réellement lancé (`which python`, `which streamlit`) ; un second virtualenv avec le SDK installé ne sert à rien si l'application s'exécute dans un autre.

### CLI CoCo introuvable {#cli-not-found}

**Symptôme :** `CoCo CLI not found on PATH. Install the cortex CLI and ensure `cortex --version` works, or set CORTEX_CODE_CLI_PATH.` (ou, lorsque `cli_path` a été passé explicitement, `CoCo CLI not found at '<path>'`)
**Cause probable :** le binaire `cortex` n'est pas installé, ou il est installé à un endroit absent du `PATH`.
**Diagnostic :** `cortex --version` ; `echo $CORTEX_CODE_CLI_PATH`.
**Correction :** installez le CLI CoCo, ou définissez `export CORTEX_CODE_CLI_PATH=/path/to/cortex`, ou passez `cli_path=` sur `CocoOptions` (voir [configuration](sections/configuration.html)).
**Si cela échoue :** vérifiez que l'emplacement d'installation du CLI correspond à ce que le shell qui lance Streamlit voit réellement — un CLI installé sous un autre profil utilisateur ou un autre shell ne sera pas sur le `PATH` du processus Streamlit.

### Sonde CLI échouée {#cli-probe-failed}

**Symptôme :** `CoCo CLI at '<path>' did not respond to --version`
**Cause probable :** un binaire existe au chemin résolu mais ce n'est pas un CLI `cortex` fonctionnel (mauvais fichier, installation cassée, ou permissions).
**Diagnostic :** lancez `cortex --version` manuellement et vérifiez à la fois le code de sortie et la sortie ; `ls -l "$(which cortex)"` pour vérifier les permissions.
**Correction :** réinstallez le CLI ; corrigez les permissions d'exécution (`chmod +x`) si nécessaire.
**Si cela échoue :** demandez au mainteneur/propriétaire du CLI un binaire connu comme fonctionnel et comparez les sommes de contrôle.

### Configuration Snowflake introuvable {#snowflake-config-not-found}

**Symptôme :** `No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml) with an authenticated connection.`
**Cause probable :** aucun fichier `*.toml` n'existe sous `~/.snowflake/`.
**Diagnostic :** `ls ~/.snowflake/*.toml`, ou `st_coco.list_snowflake_toml_files()`.
**Correction :** créez `~/.snowflake/connections.toml` avec au moins une entrée `[connections.<name>]` — voir [configuration](sections/configuration.html) pour la forme attendue.
**Si cela échoue :** vérifiez que `HOME` se résout vers le répertoire attendu dans l'environnement qui exécute Streamlit (les conteneurs et les comptes de service ont parfois un `HOME` différent).

### Erreur de connexion CoCo {#coco-connection-error}

**Symptôme :** un message `CocoConnectionError` — le texte sous-jacent nomme la connexion ou un échec d'authentification (par exemple « connection not found », « unknown connection », ou un autre échec d'authentification/connexion).
**Cause probable :** le nom de connexion passé à `CocoOptions(connection=...)` ne correspond à aucun profil dans le fichier TOML résolu, ou les identifiants du profil sont périmés/invalides.
**Diagnostic :** `st_coco.list_snowflake_connections(toml_file=...)` pour lister les noms de profils connus ; testez la même connexion directement avec le Snowflake CLI.
**Correction :** corrigez le nom de connexion, ou corrigez les champs `account`/`user`/`authenticator` du profil dans `connections.toml`.
**Si cela échoue :** vérifiez que l'identifiant de compte et l'authenticator correspondent à ce que votre administrateur Snowflake a délivré ; relancez d'abord le flux d'authentification external-browser ou key-pair en dehors de streamlit-coco pour isoler si le problème vient du fichier de connexion ou de l'identifiant lui-même.

## Cycle de vie de la session

### Session bloquée sur « Starting CoCo… » {#session-stuck-connecting}

**Symptôme :** le statut du panneau/rail reste sur « Starting CoCo… » et n'atteint jamais l'état prêt.
**Cause probable :** un problème de CLI ou de réseau pendant la connexion (le sous-processus CLI ne renvoie jamais de signal prêt).
**Diagnostic :** vérifiez le terminal qui exécute Streamlit pour des erreurs CLI ; activez la sortie de debug avec `STREAMLIT_COCO_DEBUG=1` (voir [debug-mode-not-showing-payloads](#debug-mode-not-showing-payloads)).
**Correction :** corrigez le problème d'environnement sous-jacent (CLI/connexion — voir les entrées Environnement et connexion ci-dessus), puis réinitialisez la session.
**Si cela échoue :** capturez la sortie du terminal et signalez-la contre le CLI/SDK, car l'échec se produit en dessous du mappage d'erreurs propre à la bibliothèque.

### Session non prête {#session-not-ready}

**Symptôme :** une `SessionNotReadyError`, ou le statut de la session affiche `error`.
**Cause probable :** délai de connexion dépassé ou échec de démarrage — `ensure_ready(timeout=120)` a abandonné, ou le worker a signalé un échec de démarrage.
**Diagnostic :** vérifiez `session.last_error` et `session.init_info` ; vérifiez la sortie de `render_session_status()` dans l'UI.
**Correction :** corrigez le problème d'environnement que pointe `last_error`, puis appelez `reset_session(...)` (ou utilisez l'action de réinitialisation de la barre latérale/start-gate) pour redémarrer la session.
**Si cela échoue :** relancez `check_environment()` de manière autonome pour confirmer le statut SDK/CLI/Snowflake en dehors d'une session en direct avant de réessayer.

### Saisie désactivée après le démarrage {#input-disabled-after-boot}

**Symptôme :** le champ de saisie du chat reste désactivé même après que la start gate indique que la session a démarré.
**Cause probable :** la session s'est retrouvée en statut `SessionNotReadyError` / `ERROR` juste après le démarrage (même cause sous-jacente que [session-not-ready](#session-not-ready)).
**Diagnostic :** vérifiez le badge de statut de session / `render_session_status()`.
**Correction :** corrigez l'environnement, puis réinitialisez la session depuis la barre latérale (`stop_session()` suivi d'un redémarrage de la start gate).
**Si cela échoue :** voir l'étape d'escalade de [session-not-ready](#session-not-ready).

## Approbations

### Approbation expirée {#approval-timeout}

**Symptôme :** `Approval timed out for tool <tool_name>` (`ApprovalTimeoutError`).
**Cause probable :** personne n'a résolu l'approbation en attente dans le délai `CocoOptions.approval_timeout_seconds` (par défaut `600.0`, 10 minutes).
**Diagnostic :** vérifiez que `show_approvals=True` a bien été passé à `panel()`/`copilot_rail()` afin que l'UI d'approbation ait réellement été affichée ; vérifiez si les boutons d'approbation étaient accessibles (non couverts par une autre boîte de dialogue).
**Correction :** répondez dans la fenêtre impartie la prochaine fois, ou augmentez `approval_timeout_seconds` pour les sessions qui nécessitent une revue humaine plus longue, puis renvoyez l'invite.
**Si cela échoue :** appelez `approve_pending()` / `deny_pending()` directement sur la session pour une UI d'approbation personnalisée qui ne dépend pas du timing par défaut de `render_approvals()`.

### « Always allow » ne persiste pas {#always-allow-scope}

**Symptôme :** un outil qui était « Always allowed » plus tôt redemande une approbation après une réinitialisation de session ou un redémarrage de l'application.
**Cause probable :** c'est le comportement attendu. `PermissionManager.always_allowed_tools` est un ensemble en mémoire sur la `CocoSession` vivante ; il n'est jamais écrit sur disque et est effacé par `session.reset()`, `session.close()`, et un redémarrage du processus.
**Diagnostic :** vérifiez si une réinitialisation/un redémarrage a eu lieu entre les deux approbations (réinitialisation depuis la barre latérale, `stop_session()`, ou un rechargement de page qui a créé une nouvelle session).
**Correction :** cliquez à nouveau sur **Always allow** dans la nouvelle session ; il n'existe aucun moyen de faire persister « Always allow » à travers une réinitialisation, par conception (voir [security](sections/security.html)).
**Si cela échoue :** si une politique par outil durable à travers les sessions est requise, ce n'est pas implémenté aujourd'hui — suivez-le sous SEC-01 dans [limits](sections/limits.html) plutôt que de chercher un réglage caché.

## Téléversements de fichiers

### Téléversement rejeté : extension {#upload-rejected-extension}

**Symptôme :** `Disallowed file extension for '<name>' (allowed: <list>)` (`CwdUploadError`).
**Cause probable :** le suffixe du fichier téléversé n'est pas dans `DEFAULT_ALLOWED_EXTENSIONS` (ou dans un `allowed_extensions` fourni par l'appelant).
**Diagnostic :** comparez l'extension du fichier avec la constante de liste d'autorisation dans `streamlit_coco/upload.py`.
**Correction :** convertissez/renommez le fichier vers un type autorisé, ou appelez `upload_to_cwd(..., allowed_extensions={...})` avec une liste d'autorisation plus large pour cette application.
**Si cela échoue :** vérifiez si le fichier a réellement besoin d'atteindre le `cwd` de l'agent — certains flux n'ont besoin que de communiquer le contenu à l'agent, pas le fichier brut.

### Téléversement rejeté : taille {#upload-rejected-size}

**Symptôme :** `File '<name>' is <n> bytes; max allowed is <max_bytes>` (`CwdUploadError`).
**Cause probable :** le fichier dépasse `DEFAULT_MAX_BYTES` (10 Mio) ou un `max_bytes` fourni par l'appelant.
**Diagnostic :** vérifiez la taille réelle du fichier par rapport à la limite configurée.
**Correction :** scindez ou compressez le fichier, ou appelez `upload_to_cwd(..., max_bytes=...)` avec une limite plus élevée pour cette application.
**Si cela échoue :** demandez-vous si le fichier ne devrait pas plutôt se trouver dans un stage Snowflake plutôt que dans la quarantaine locale `cwd` — les jeux de données volumineux sont explicitement hors périmètre pour ce chemin de téléversement (voir `doc/features/file-upload/file-upload.md`).

### Conflit de nom de téléversement {#upload-name-conflict}

**Symptôme :** `File already exists: <relative path> (pass overwrite='replace' or 'skip')` (`CwdUploadError`).
**Cause probable :** `overwrite="error"` (valeur par défaut de `upload_to_cwd`) et un fichier avec le même nom assaini existe déjà sous le sous-répertoire de téléversement.
**Diagnostic :** listez le répertoire de téléversement (`list_cwd_uploads(target)`) pour voir le fichier existant.
**Correction :** passez `overwrite="replace"` ou `overwrite="skip"` à `upload_to_cwd()` / `cwd_uploader()`, ou renommez le fichier avant de le téléverser. Notez que `chat_input_bar(accept_file=...)` définit déjà `upload_overwrite="replace"` par défaut, donc ceci apparaît surtout via des appels directs à `upload_to_cwd()` ou un `cwd_uploader()` configuré avec `overwrite="error"`.
**Si cela échoue :** si les collisions sont attendues et doivent toujours l'emporter, changez le mode d'écrasement par défaut de l'appelant plutôt que de gérer chaque conflit manuellement.

## Aperçu d'application

### L'aperçu ne démarre pas {#preview-wont-start}

**Symptôme :** cliquer sur **Run** dans `app_viewer()` ne produit aucune iframe ni URL accessible.
**Cause probable :** la plage de ports libres (`8511`–`8520`) est épuisée, `app_dir` ne contient pas de `streamlit_app.py` (ou un autre `script_name`), ou un processus d'aperçu périmé pour le même `app_dir` occupe déjà le port.
**Diagnostic :** vérifiez `preview_running(app_dir)` / `preview_url(app_dir)` ; vérifiez `.preview.log`, `.preview.pid`, `.preview.port` dans `app_dir` ; vérifiez `last_preview_exception(app_dir)`.
**Correction :** appelez `stop_app_preview(app_dir)` pour nettoyer un processus périmé, confirmez que `app_dir` contient bien `streamlit_app.py`, puis cliquez à nouveau sur **Run**.
**Si cela échoue :** libérez la plage de ports `8511`–`8520` sur l'hôte (un autre aperçu ou un processus sans rapport peut l'occuper), et vérifiez qu'un seul `app_viewer()` cible ce `app_dir` (voir [limits](sections/limits.html)).

### « Fix with CoCo » n'est pas câblé {#fix-with-coco-not-wired}

**Symptôme :** cliquer sur **Fix with CoCo** ne fait rien, ou affiche un toast demandant de « wire `on_fix=` ».
**Cause probable :** l'application hôte a appelé `app_viewer()` sans callback `on_fix=`. `app_viewer()` ne met jamais de job en file d'attente de lui-même — il construit seulement l'invite via `default_fix_prompt()`.
**Diagnostic :** vérifiez l'appel `app_viewer(...)` pour `on_fix=`.
**Correction :** passez `on_fix=<callback>` qui met en file d'attente `default_fix_prompt(traceback, app_dir)` comme job sur la propre session Copilot de l'hôte et ouvre le rail Copilot — voir `doc/features/app-viewer/app-viewer.md` pour le patron de référence.
**Si cela échoue :** vérifiez que l'hôte compose bien `copilot_rail()` aux côtés de `app_viewer()` — `app_viewer()` n'importe délibérément pas et ne connaît pas `copilot_rail()` (voir [architecture](sections/architecture.html)).

### L'analyse du journal de l'aperçu passe à côté {#preview-log-parse-miss}

**Symptôme :** l'application enfant est visiblement cassée, mais l'expander **Preview exception** n'affiche pas de traceback.
**Cause probable :** dérive du format de journal. Le parseur recherche les marqueurs littéraux `Uncaught app exception` et `Traceback (most recent call last):` dans `.preview.log`, et traite toute ligne horodatée ultérieure comme « erreur effacée » — un journal qui ne correspond pas à ces marqueurs, ou qui journalise une ligne ultérieure sans rapport, se lit comme effacé même si l'application est toujours cassée.
**Diagnostic :** lisez `.preview.log` directement (ou `preview_log_tail(app_dir)`) plutôt que de vous fier à l'expander.
**Correction :** cliquez quand même sur **Fix with CoCo** — il envoie tout de même la fin du journal dans l'invite même quand le parseur n'a pas détecté d'exception en direct.
**Si cela échoue :** copiez les lignes de journal pertinentes dans une invite manuelle à CoCo, puisque les marqueurs automatiques ne couvrent pas cette forme de journal.

## Sortie structurée

### La sortie structurée ne s'affiche pas {#structured-output-not-rendering}

**Symptôme :** la réponse de l'agent a une forme JSON, mais aucun panneau structuré ni widget piloté par callback n'apparaît.
**Cause probable :** l'une de deux choses — soit `on_structured_output` / `structured_output_container` a été défini, ce qui saute intentionnellement le panneau structuré inline par défaut (exclusivité mutuelle), soit `CocoOptions.output_schema` n'a jamais été défini, donc l'agent n'a en réalité pas été contraint de produire une charge utile `structured_output` conforme au schéma même si le texte de la réponse ressemble à du JSON.
**Diagnostic :** vérifiez `session.chat_result().structured_output` après le tour ; vérifiez si `on_structured_output=` ou `structured_output_container=` a été passé à `panel()` / `copilot_rail()`.
**Correction :** définissez `CocoOptions.output_schema={...}` pour que le SDK impose `output_format`, et soit vous vous appuyez sur le panneau inline par défaut (aucun callback/conteneur défini), soit vous lisez `structured_output` depuis le callback.
**Si cela échoue :** vérifiez que la réponse provient bien d'un tour qui s'est réellement exécuté avec les `CocoOptions` porteuses du schéma — une session créée avant l'ajout du schéma conserve son worker d'origine jusqu'à ce que `options_hash()` change (voir [architecture](sections/architecture.html)).

### `$schema` / `$id` rejeté {#schema-dollar-schema-rejected}

**Symptôme :** `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`.
**Cause probable :** un fichier de contrat JSON Schema (comme ceux sous `examples/bi_to_semantic/contracts/`) inclut une clé `$schema` (ou `$id`), et celle-ci a été transmise telle quelle au SDK sans être retirée — le résolveur de schéma du SDK tente de récupérer cette URI et échoue.
**Diagnostic :** vérifiez la version de `streamlit-coco` utilisée ; vérifiez si `output_schema` est construit en fusionnant à la main un fichier de contrat après la construction (ce qui pourrait réintroduire `$schema`).
**Correction :** passez à `>=0.1.6` — `CocoOptions.to_sdk_options()` retire désormais automatiquement `$schema`/`$id` (`_schema_for_sdk()` dans `streamlit_coco/options.py`) avant de transmettre le schéma au SDK.
**Si cela échoue :** si l'erreur persiste en `>=0.1.6`, vérifiez que rien en aval ne réinsère `$schema` dans le dict passé comme `output_schema` après la construction de `CocoOptions`.

## Publication et CI

### Faux positif `pip-audit` sur le package en mode editable {#pip-audit-editable-false-positive}

**Symptôme :** `pip-audit` rapporte `streamlit-coco … Dependency not found on PyPI and could not be audited (<version>)`.
**Cause probable :** exécution d'un `pip-audit` nu contre une installation pré-tag ou editable de `streamlit-coco` lui-même, qui n'est pas encore publiée à cette version.
**Diagnostic :** vérifiez quelle commande a été lancée — `pip-audit` seul fera apparaître ceci ; `make audit` / `pip-audit --skip-editable` non.
**Correction :** utilisez `make audit` (ou `pip-audit --skip-editable` directement) — ceci a été corrigé en `0.1.7` à la fois pour la cible Makefile et pour la CI, afin qu'un incrément de version pré-tag ne soit pas signalé comme un échec d'audit en faux positif.
**Si cela échoue :** si le même message apparaît avec `--skip-editable` déjà défini, traitez-le comme une véritable lacune d'audit et signalez-le plutôt que de supposer qu'il s'agit de ce faux positif connu.

## Mode debug

### Le mode debug n'affiche pas les charges utiles {#debug-mode-not-showing-payloads}

**Symptôme :** `STREAMLIT_COCO_DEBUG` (ou `COCO_DEBUG`) a été défini, mais aucune section « Raw tool payload » n'apparaît dans la transcription.
**Cause probable :** la valeur n'est pas l'une des chaînes reconnues comme vraies (`"1"`, `"true"`, `"yes"`, `"on"`, insensible à la casse), ou la variable a été exportée dans un shell/processus différent de celui qui exécute Streamlit.
**Diagnostic :** `echo $STREAMLIT_COCO_DEBUG` dans le shell exact qui lance `streamlit run` ; vérifiez que l'ensemble des valeurs vraies de `is_debug_mode()` correspond à la valeur utilisée.
**Correction :** `export STREAMLIT_COCO_DEBUG=1` (ou `COCO_DEBUG=1`) avant de démarrer Streamlit dans ce même shell, ou définissez `st.session_state["coco_debug"] = True` dans l'application pour un bascule piloté par l'UI.
**Si cela échoue :** vérifiez que le processus Streamlit a bien été redémarré après la définition de la variable — les variables d'environnement sont lues au moment de l'appel par `is_debug_mode()`, mais un processus démarré avant que l'export ne soit défini dans son propre shell ne la verra pas.

## App Builder

### Course d'écrasement du brief App Builder {#app-builder-brief-overwrite-race}

**Symptôme :** des modifications faites dans l'expander **App brief** du Studio semblent perdues, ou une exécution de **Save & regenerate** utilise un brief périmé.
**Cause probable :** avant `0.1.8`, **Save & regenerate** pouvait mettre CoCo en file d'attente avant que `BRIEF.md` ne soit écrit à partir des valeurs de champs actuelles de l'expander, et la page Brief pouvait écraser `BRIEF.md` à nouveau lors du même tour — une course entre les deux écritures.
**Diagnostic :** vérifiez la version installée (`streamlit_coco.__version__`).
**Correction :** passez à `>=0.1.8` — **Save & regenerate** écrit désormais `BRIEF.md` à partir des widgets de l'expander avant de mettre CoCo en file d'attente, et la page Brief n'écrase plus ce fichier lors du même tour.
**Si cela échoue :** si le problème persiste en `>=0.1.8`, capturez la séquence exacte de clics (quelle page, quel bouton, dans quel ordre) et signalez-le — la correction d'ordonnancement ciblait spécifiquement le chemin Save & regenerate, pas toute séquence possible de modification concurrente.
