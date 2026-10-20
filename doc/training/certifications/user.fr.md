# streamlit-coco — Certification Utilisateur

**Seuil de réussite : 24/30.** Prérequis : formation (Training) terminée.

### Q1. Quel est l'ordre recommandé des trois cas de la formation (Training) ?

a) `03-advanced` → `02-intermediate` → `01-simple`
b) `01-simple` → `02-intermediate` → `03-advanced`
c) `02-intermediate` → `01-simple` → `03-advanced`
d) N'importe quel ordre — il n'y a pas de séquence recommandée

### Q2. Qu'est-ce qui distingue `01-simple` de `02-intermediate` ?

a) `01-simple` utilise des données d'exemple et est entièrement guidé ; `02-intermediate` travaille sur les données propres de l'apprenant, avec des points de contrôle plutôt que des étapes pas à pas
b) `01-simple` est le seul cas qui utilise de vraies données Snowflake
c) `02-intermediate` supprime toutes les données et tout le guidage
d) Les deux cas sont identiques, à l'exception de leur budget de temps

### Q3. Quelle est la caractéristique déterminante de `03-advanced` ?

a) Il reprend `01-simple` avec un jeu de données d'exemple plus large
b) Quelque chose se casse — tiré d'un incident réel ou d'une entrée « Fixed » du CHANGELOG — et l'apprenant diagnostique seul
c) Il est entièrement à choix multiple, sans composante pratique
d) Il ne couvre que l'API headless `query()`

### Q4. Quelle séquence d'appels `examples/chat_app.py` utilise-t-il pour implémenter le pattern préféré ?

a) `chat()` → `render_approvals()` → `send_prompt()`
b) `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()`
c) `require_environment()` → `copilot_rail()` → `app_viewer()`
d) `CocoSession()` → `query()` → `events_to_dataframe()`

### Q5. Que retourne `panel()` ?

a) `None`
b) Un `CocoChatResult`
c) Un `CocoEnvironment`
d) Une `CocoSession`

### Q6. Dans `panel()`, que fait le fait de définir `output_label=None` ?

a) Affiche la sortie avec le libellé par défaut « CoCo output »
b) Masque le conteneur bordé de la sortie
c) Bascule le mode de sortie de `"transcript"` à `"field"`
d) Désactive le bouton Stop

### Q7. Quel paramètre de `panel()` bascule entre l'affichage de l'historique de conversation en cours et l'affichage uniquement de la dernière sortie de type champ ?

a) `output_mode` (`"transcript"` ou `"field"`)
b) `show_status`
c) `status_expanded`
d) `text_renderer`

### Q8. Que permet `chat_input_bar(session, accept_file=True)` ?

a) Le rendu de sortie JSON structurée
b) La pièce jointe de fichiers, enregistrée dans le répertoire de travail de la session via les fonctions d'aide au téléversement
c) Un sélecteur de questions d'exemple en rail latéral
d) Une bannière de mode plan avec un bouton Execute plan

### Q9. Lequel de ces éléments est un véritable paramètre de `copilot_rail()` ?

a) `example_questions`
b) `demo_mode`
c) `sidebar_width`
d) `rail_theme`

### Q10. À quoi sert `job=` dans `copilot_rail()` ?

a) Il planifie une tâche de fond basée sur un cron
b) Il transmet un dict tel que `{prompt, label, status, expect_structured}` pour mettre en file d'attente un job que le rail doit envoyer
c) Il définit l'entrepôt (warehouse) Snowflake pour la session
d) Il configure le job CI qui construit le rail

### Q11. Qu'ajoute `transcript_display_config()` à une interface basée sur le rail ?

a) Une popover avec des pastilles/curseurs « Last messages » et « First n characters » pour contrôler l'affichage de l'historique de conversation
b) Un bouton qui exporte l'historique de conversation au format CSV
c) Un bouton pour basculer entre mode clair et mode sombre
d) Un contrôle pour basculer l'interface entre libellés en anglais et en français

### Q12. Vers quoi `app_dir` doit-il pointer pour que `app_viewer()` fonctionne correctement ?

a) Le même répertoire que l'application hôte qui appelle `app_viewer()`
b) Un dossier contenant un `streamlit_app.py` (ou le script nommé via `script_name`)
c) N'importe quel répertoire contenant un `Makefile`
d) Le dossier `dist/` produit par `make build`

### Q13. Que fait le bouton « Fix with CoCo » dans `app_viewer()` par défaut ?

a) Il réécrit automatiquement l'application générée sans étape d'approbation
b) Il appelle `on_fix` avec un prompt construit à partir de `default_fix_prompt(traceback, app_dir)`, mettant typiquement en file d'attente un job pour CoCo
c) Il redémarre le processus enfant `streamlit run` avec les paramètres par défaut
d) Il supprime le journal de prévisualisation précédent

### Q14. Combien de prévisualisations `app_viewer()` sont censées pointer vers le même `app_dir` en même temps ?

a) Illimité, tant que les ports diffèrent
b) Une seule
c) Deux — une pour l'application déterministe et une pour l'application écrite par CoCo
d) Autant que ce qui tient dans la plage de ports 8511–8520

### Q15. Quel champ de `CocoOptions` contrôle la durée pendant laquelle l'application attend une décision humaine sur une approbation en attente avant de lever une erreur ?

a) `max_turns`
b) `approval_timeout_seconds` (valeur par défaut `600.0`)
c) `permission_mode`
d) `require_approval_for`

### Q16. Quelle est la valeur par défaut de `CocoOptions.permission_mode` ?

a) `"plan"`
b) `"auto"`
c) `"default"`
d) `"approve_all"`

### Q17. Quelle fonction sonde l'environnement (installation du SDK, accessibilité du CLI, configuration Snowflake) sans démarrer d'agent, et ne lève jamais d'exception ?

a) `require_environment()`
b) `check_environment()`
c) `CocoSession.ensure_ready()`
d) `resolve_snowflake_config_path()`

### Q18. Si `toml_file` n'est pas transmis et qu'il existe exactement un fichier `*.toml` sous `~/.snowflake/`, que se passe-t-il ?

a) La librairie refuse de démarrer et lève `SnowflakeConfigNotFoundError`
b) Ce fichier unique est utilisé, quel que soit son nom
c) La librairie ne recherche qu'un fichier littéralement nommé `connections.toml`
d) L'utilisateur est invité de manière interactive à choisir un fichier

### Q19. Avec plusieurs fichiers `*.toml` sous `~/.snowflake/` et sans `toml_file` fourni, quel est l'ordre de sélection ?

a) Alphabétique uniquement
b) `connections.toml` en premier, puis `config.toml`, puis par ordre alphabétique
c) Le fichier modifié le plus récemment en premier
d) `config.toml` en premier, puis `connections.toml`, puis par ordre alphabétique

### Q20. Que démontre `examples/structured_output.py` ?

a) `output_schema` associé à `on_structured_output`, acheminant le JSON de l'agent vers un widget d'application plutôt que vers le texte du chat
b) Un pipeline purement asynchrone sans import de Streamlit
c) Le téléversement de fichiers dans le répertoire de travail de l'agent
d) Un Copilot en rail latéral sans outil SQL

### Q21. Que démontre `examples/headless_pipeline.py` ?

a) `panel()` intégré dans une application multipage
b) Du Python asynchrone pur utilisant `query()` / `CocoSession`, sans import de Streamlit, exécuté depuis un terminal
c) `copilot_rail()` combiné avec `app_viewer()`
d) Le composant hérité CCv2 `chat()`

### Q22. Quel type de démo est `examples/approval_gate.py` ?

a) Le pattern préféré (`panel()` + `chat_input_bar()`)
b) Un script headless
c) Le composant hérité CCv2 `chat()` tout-en-un
d) Un exemple basé sur le rail sans outil SQL

### Q23. Qu'est-ce qui distingue `examples/backlog_desk/` des autres applications d'exemple ?

a) C'est le premier exemple basé sur le rail et qui n'utilise aucun outil SQL — ses données sont soutenues par des fichiers/JSON
b) C'est le seul exemple qui nécessite un entrepôt (warehouse) Snowflake dédié
c) C'est le seul exemple qui utilise le composant hérité CCv2
d) C'est le seul exemple sans aucun Copilot

### Q24. Dans `examples/backlog_desk/`, comment son Copilot est-il ouvert ?

a) C'est une page de navigation dédiée dans la barre latérale
b) Il s'ouvre automatiquement à chaque chargement de page
c) Depuis un bouton d'en-tête « Copilot » ou un lien d'action, et fermé avec « Close » — ce n'est pas une page de navigation
d) Uniquement via la cible `make headless`

### Q25. Quels types de fichiers sources `examples/bi_to_semantic/` lit-il en entrée ?

a) Uniquement des fichiers de stage Snowflake
b) Des classeurs Tableau `.twb`/`.twbx` et/ou Power BI `.pbix`/`.pbit`
c) Uniquement des exports CSV depuis un entrepôt de données
d) Des fichiers `.cortex/skills/*/SKILL.md`

### Q26. Où atterrissent par défaut les fichiers téléversés via `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)` ?

a) `<CocoOptions.cwd>/_uploads/` (le nom du sous-répertoire est configurable)
b) Le répertoire d'installation propre de l'application Streamlit
c) `~/.snowflake/`
d) `dist/`

### Q27. Que l'étape « Build » de l'App Builder écrit-elle dans `examples/app_builder/out/<slug>/` ?

a) Uniquement un fichier `.whl` compilé
b) `brief.json`, `BRIEF.md`, `sketches/*`, et `streamlit_app.py`
c) Un SBOM CycloneDX
d) Uniquement un fichier `.preview.log`

### Q28. Où le SBOM de la version release est-il publié ?

a) Dans `examples/app_builder/out/`
b) En tant qu'assets de GitHub Release (JSON CycloneDX), généré uniquement en CI
c) Dans `_uploads/`
d) Il n'est encore généré nulle part

### Q29. Que présente `render_approvals()`, et dans quel ordre de boutons ?

a) Deny, Always allow, Approve once
b) Approve once, Always allow, Deny
c) Approve once, Deny (il n'y a pas d'option « Always allow »)
d) Un seul bouton « Approve » sans option de refus

### Q30. Lesquelles de ces familles d'outils n'exposent jamais d'option « Always allow » dans l'interface d'approbation ? (Choix multiple — sélectionnez toutes les réponses applicables)

a) `AskUserQuestion`
b) `ExitPlanMode`
c) L'outil SQL
d) Edit
e) Write
f) Grep

## Answer Key

| Q | Réponse | Explication |
|---|--------|-------------|
| 1 | **b** | Les cas sont numérotés et progressent `01-simple` → `02-intermediate` → `03-advanced`, en difficulté croissante. |
| 2 | **a** | `01-simple` est le chemin heureux entièrement guidé, avec données d'exemple ; `02-intermediate` utilise les données propres de l'apprenant, avec des points de contrôle plutôt que des étapes pas à pas. |
| 3 | **b** | `03-advanced` présente une véritable casse (incident réel ou entrée « Fixed » du CHANGELOG) que l'apprenant diagnostique sans étapes guidées. |
| 4 | **b** | C'est exactement la chaîne d'appels que l'exemple de référence du pattern préféré utilise. |
| 5 | **b** | `panel(session, **kwargs) -> CocoChatResult`. |
| 6 | **b** | `output_label=None` masque le conteneur bordé de la sortie ; le libellé par défaut est sinon « CoCo output ». |
| 7 | **a** | `output_mode` bascule entre le rendu `"transcript"` (par défaut) et `"field"`. |
| 8 | **b** | `accept_file=True` (ou `"multiple"`) active la pièce jointe de fichiers, enregistrée via les fonctions d'aide au téléversement dans le `cwd` de la session. |
| 9 | **a** | `example_questions` est un paramètre documenté de `copilot_rail()` ; les trois autres ne font pas partie de sa signature. |
| 10 | **b** | `job=` prend un dict (`prompt`, `label`, `status`, `expect_structured`) qui met en file d'attente un prompt à envoyer par le rail. |
| 11 | **a** | `transcript_display_config()` affiche la popover des paramètres d'affichage avec les contrôles Last-messages/First-n-characters. |
| 12 | **b** | `app_viewer(app_dir, ...)` nécessite un dossier contenant `streamlit_app.py` (ou la surcharge `script_name`) ; il ne doit jamais pointer vers le répertoire propre de l'application hôte. |
| 13 | **b** | L'action Fix appelle `on_fix` avec un prompt issu de `default_fix_prompt(traceback, app_dir)`, mettant normalement en file d'attente un job CoCo. |
| 14 | **b** | La limitation documentée est une seule prévisualisation par `app_dir`. |
| 15 | **b** | `approval_timeout_seconds` (valeur par défaut `600.0`, soit 10 minutes) régit l'attente human-in-the-loop avant `ApprovalTimeoutError`. |
| 16 | **c** | `CocoOptions.permission_mode` a pour valeur par défaut `"default"` ; `"plan"` est utilisé explicitement pour les flux ExitPlanMode. |
| 17 | **b** | `check_environment()` est la sonde qui ne lève jamais d'exception ; `require_environment()` lève des erreurs typées à la place. |
| 18 | **b** | Lorsqu'il n'existe qu'un seul `*.toml` sous `~/.snowflake/`, il est utilisé quel que soit son nom de fichier. |
| 19 | **b** | Avec plusieurs fichiers, `connections.toml` l'emporte en premier, puis `config.toml`, puis l'ordre alphabétique. |
| 20 | **a** | `structured_output.py` montre `output_schema` + `on_structured_output` acheminant le JSON vers un widget plutôt que vers le texte du chat. |
| 21 | **b** | `headless_pipeline.py` est du Python asynchrone pur utilisant `query()`/`CocoSession`, sans import de Streamlit. |
| 22 | **c** | `approval_gate.py` démontre le composant hérité CCv2 `chat()` tout-en-un. |
| 23 | **a** | `backlog_desk` est le premier exemple basé sur le rail, sans SQL, soutenu par des fichiers JSON locaux. |
| 24 | **c** | Son Copilot s'ouvre depuis un bouton d'en-tête « Copilot » ou un lien d'action, et se ferme avec « Close » — ce n'est pas une page de navigation. |
| 25 | **b** | `bi_to_semantic` lit des classeurs Tableau `.twb`/`.twbx` et/ou Power BI `.pbix`/`.pbit`. |
| 26 | **a** | Les fonctions d'aide au téléversement écrivent par défaut dans `<CocoOptions.cwd>/_uploads/` (nom du sous-répertoire configurable). |
| 27 | **b** | L'étape Build écrit `brief.json`, `BRIEF.md`, `sketches/*`, et `streamlit_app.py` dans `out/<slug>/`. |
| 28 | **b** | Le SBOM (CycloneDX) est attaché aux assets de GitHub Release et n'est produit qu'en CI, lors d'une release taggée. |
| 29 | **b** | `render_approvals()` ordonne ses contrôles Approve once, Always allow, Deny. |
| 30 | **A, B** | `AskUserQuestion` et `ExitPlanMode` invitent toujours à une nouvelle décision et ne montrent jamais « Always allow » ; l'outil SQL et Edit/Write/Grep peuvent être toujours-autorisés. |
