# streamlit-coco — Certification Expert

**Seuil de réussite : 24/30.** Prérequis : ≥ 12 mois d'utilisation.

### Q1. Qu'est-ce que `CocoSession` utilise en interne pour piloter le client du SDK ?

a) Un appel bloquant synchrone depuis le thread principal de Streamlit
b) Un thread d'arrière-plan (`threading.Thread`, nommé `coco-session`) exécutant une boucle asyncio qui enveloppe `CortexCodeSDKClient`
c) Un processus Streamlit séparé par session
d) Une file de tâches adossée à un broker externe

### Q2. Quel invariant permet à `examples/headless_pipeline.py` de s'exécuter depuis un terminal ordinaire sans Streamlit installé ?

a) Les exports UI (`panel`, `copilot_rail`, `chat_input_bar`, …) se résolvent paresseusement via `streamlit_coco.__getattr__` ; les imports headless du cœur (`CocoSession`, `query`, `CocoOptions`, les fonctions de permission, la hiérarchie d'erreurs) n'importent jamais `streamlit`
b) `streamlit` est embarqué comme dépendance vendorisée à l'intérieur de `streamlit_coco`
c) L'exemple headless applique un monkey-patch sur `sys.modules["streamlit"]`
d) `CocoSession` détecte l'absence de Streamlit et bascule automatiquement en mode CLI seul

### Q3. Quand un appel d'outil nécessite une approbation, qu'est-ce qui bloque exactement, et jusqu'à quand ?

a) Le thread principal de Streamlit bloque jusqu'au rafraîchissement de la page
b) Le callback `can_use_tool` (construit par `build_can_use_tool()`) bloque le thread worker de la session sur `PermissionManager.wait_for_decision()`, jusqu'à ce que l'interface résolve la décision ou que `approval_timeout_seconds` s'écoule
c) Rien ne bloque ; l'outil s'exécute et est annulé (rollback) s'il est refusé
d) Le sous-processus CLI se termine et doit être redémarré manuellement

### Q4. Quels champs `CocoOptions.options_hash()` hashe-t-il, et à quoi cela sert-il ?

a) Chaque champ de `CocoOptions` ; il redémarre toujours le worker à chaque changement
b) Uniquement les champs qui affectent ce qu'un outil est autorisé à faire (par ex. `allowed_tools`, `disallowed_tools`, `permission_mode`, `require_approval_for`, `add_dirs`) ; `CocoSession` ne redémarre son worker que lorsque ce hash change
c) Uniquement `connection` et `cwd`, utilisés purement pour la journalisation
d) Un hash de l'ensemble de l'historique de conversation, utilisé pour la mise en cache des réponses

### Q5. Pourquoi `app_viewer()` n'importe-t-il jamais `copilot_rail()` (et inversement) ?

a) Ils sont mutuellement incompatibles et ne peuvent pas être utilisés dans la même application
b) Le composant de prévisualisation reste agnostique de l'hôte — il ne connaît pas les files de jobs ; une application hôte compose les deux et câble elle-même `on_fix`
c) `copilot_rail()` a été déprécié au profit de `app_viewer()`
d) Un bug d'import circulaire n'a pas encore été corrigé

### Q6. Quelles familles d'outils sont traitées comme cas particulier dans `permissions.py` pour toujours créer une nouvelle demande d'approbation, en ignorant tout « always allow » antérieur ?

a) L'outil SQL et Write
b) `AskUserQuestion` et `ExitPlanMode`
c) Grep et Glob
d) Edit et Read

### Q7. Quel message `SnowflakeConfigNotFoundError` porte-t-elle ?

a) « CoCo CLI not found on PATH »
b) « No Snowflake config found. Create ~/.snowflake/connections.toml (or legacy config.toml)... »
c) « Approval timed out for tool {tool_name} »
d) « cortex-code-agent-sdk is required. Install with: pip install streamlit-coco[sdk] »

### Q8. Quelle exception est levée lorsqu'un binaire `cortex` est trouvé au chemin configuré mais ne répond pas correctement à `--version` ?

a) `CLINotFoundError`
b) `CLIProbeError`
c) `CocoConnectionError`
d) `SessionStartError`

### Q9. En quoi `SessionStartError` diffère-t-elle de `SessionNotReadyError` ?

a) Ce sont la même exception sous deux noms
b) `SessionStartError` couvre un worker qui échoue à démarrer ; `SessionNotReadyError` couvre un délai de connexion ou un échec de démarrage une fois le worker en cours d'exécution
c) `SessionStartError` n'est utilisée que pour le `query()` headless
d) `CocoConnectionError` remplace les deux

### Q10. Que fait le kwarg `context=` de `wrap_exception()` ?

a) Il est purement cosmétique et n'affecte pas le type d'erreur levé
b) Il oriente la correspondance par détection de message (par ex. `"session_start"`, `"session_ready"`/`"session"`, `"query"`, `"approval"`) vers la bonne sous-classe `CocoError`, selon l'endroit où l'exception brute s'est produite
c) Il définit la clé de session Streamlit
d) Il journalise l'exception vers un serveur distant

### Q11. Que couvre `CwdUploadError` ?

a) Uniquement les téléversements surdimensionnés
b) Les noms de fichiers invalides (protection contre le path-traversal), les extensions non autorisées, les charges utiles surdimensionnées, et les conflits d'écrasement
c) Uniquement les échecs de connexion Snowflake pendant le téléversement
d) Uniquement les incompatibilités d'extension, jamais la taille

### Q12. Quelle exception est également une `TimeoutError`, en plus d'être une `CocoError` ?

a) `SessionNotReadyError`
b) `ApprovalTimeoutError`
c) `CLIProbeError`
d) `QueryError`

### Q13. Dans le modèle de menace STRIDE, quelle sévérité est attribuée à l'injection de prompt déclenchant des outils dangereux, et qu'est-ce qui l'atténue ?

a) Sévérité faible ; atténuée par la sanitisation des entrées
b) Sévérité élevée ; atténuée par les portes d'approbation (`PermissionManager` intercepte avant l'exécution), avec un rôle à privilège minimal également recommandé
c) Sévérité critique ; atténuée en désactivant tous les outils par défaut
d) Sévérité moyenne ; atténuée par une limitation de débit (rate limiting)

### Q14. Quelle sévérité et quelle atténuation s'appliquent au risque d'escalade lié à « Always allow » ?

a) Sévérité élevée ; atténuée en exigeant une ressaisie de mot de passe
b) Sévérité moyenne ; atténuée par la portée — par outil, par session uniquement, effacée à la réinitialisation ou au redémarrage
c) Sévérité faible ; aucune atténuation n'est appliquée
d) Sévérité élevée ; atténuée par un journal d'audit persistant (déjà livré)

### Q15. Quel est le statut du risque de répudiation (absence de journal persisté des actions destructrices approuvées) ?

a) Résolu en `0.1.8`
b) Ouvert, sévérité moyenne, suivi comme SEC-01 — l'historique de conversation n'existe que dans l'état de session Streamlit, rien de durable n'est écrit
c) Ce n'est pas un risque reconnu dans le modèle de menace
d) Atténué par l'analyse CodeQL

### Q16. Comment le risque de divulgation d'informations lié à l'apparition de secrets dans l'historique de conversation/les journaux est-il atténué ?

a) La librairie chiffre l'historique de conversation au repos
b) La librairie ne journalise pas les identifiants, et le SDK les masque (redacte) de sa sortie
c) Ce n'est pas atténué ; c'est un point ouvert
d) En désactivant entièrement l'historique de conversation

### Q17. Quel risque de chaîne d'approvisionnement le modèle de menace signale-t-il, et comment est-il atténué ?

a) Élévation de privilège via une dépendance compromise ; atténuée par `pip-audit` en CI et l'analyse Gitleaks, avec `uv.lock` commité pour des builds reproductibles
b) Injection SQL dans les appels d'outils de l'agent ; atténuée par des requêtes paramétrées
c) Détournement de session ; atténué par la rotation des clés API
d) Usurpation DNS du registre PyPI ; atténuée par l'épinglage de certificat

### Q18. Selon le guidage « Roles and grants », pourquoi se connecter avec `ACCOUNTADMIN` (ou un grant tel que `MANAGE WAREHOUSES`) est-il déconseillé, même avec des portes d'approbation en place ?

a) Les portes d'approbation contrôlent si une instruction s'exécute, pas ce qu'elle est autorisée à toucher une fois approuvée — les permissions SQL effectives sont exactement les grants du rôle connecté
b) Les sessions `ACCOUNTADMIN` sont techniquement incompatibles avec le CLI CoCo
c) La librairie bloque activement les connexions `ACCOUNTADMIN`
d) `MANAGE WAREHOUSES` désactive entièrement le flux d'approbation

### Q19. Lesquels de ces éléments sont explicitement hors périmètre pour le pack de guides de ce produit, selon la décision de cadrage par module ? (Choix multiple — sélectionnez toutes les réponses applicables)

a) Un chapitre de référence Skills pour les `.cortex/skills/*/SKILL.md` à la racine du dépôt
b) Un chapitre `reference-procedures` pour les objets Snowflake
c) Un chapitre de déploiement Native App
d) Un chapitre `reference-commands` pour les cibles du Makefile
e) Un chapitre `reference-api` pour l'API Python
f) Un chapitre catalogue de contrôles (fichiers de règles / grille de notation)

### Q20. Quelles cibles de déploiement le modèle de menace considère-t-il, et lesquelles sont réellement livrées aujourd'hui ?

a) Local, SiS et SPCS sont tous livrés aujourd'hui
b) Seul SiS est livré aujourd'hui ; local et SPCS ne sont que du périmètre du modèle de menace
c) Local, SiS et SPCS sont tous considérés dans le modèle de menace, mais seul local est réellement livré aujourd'hui
d) Seul SPCS est livré aujourd'hui

### Q21. Pourquoi le pack de guides omet-il un chapitre « Infrastructure as code » ?

a) Des fichiers Terraform existent mais n'ont pas été documentés
b) Il n'existe aucun fichier `*.tf` dans ce dépôt
c) L'IaC est hors périmètre pour des raisons de sécurité uniquement
d) C'est prévu pour une version future et reporté intentionnellement

### Q22. Pourquoi `reference-examples` traite-t-il chacune des trois applications d'exemple comme une seule section, plutôt que de documenter chaque page Streamlit interne de chaque application ?

a) Documenter page par page pour trois applications d'exemple reviendrait à reformuler les README d'exemple déjà liés, donc chaque application obtient un seul H2
b) Les pages Streamlit ne peuvent pas être documentées en Markdown
c) Seul `chat_app.py` a plus d'une page
d) La documentation au niveau des pages est générée automatiquement et ne nécessite aucune rédaction

### Q23. Qu'est-ce que `text_renderer` en tant que point d'extension ?

a) Un paramètre requis sans défaut, utilisé pour sélectionner l'entrepôt (warehouse) Snowflake
b) Une option de rendu de texte enfichable sur `panel()` (et les fonctions d'aide à l'affichage associées) — un nom de préréglage (`"markdown"`, `"write"`, `"text"`, `"caption"`, `"code"`) ou un callable
c) Un flag CLI pour `make chat`
d) Un fichier YAML définissant les couleurs de l'historique de conversation

### Q24. Comment la librairie décide-t-elle de rendre la carte d'un outil inconnu ou fourni via MCP ?

a) Elle refuse de rendre quoi que ce soit pour les outils qu'elle ne reconnaît pas
b) Via un dispatch par nom d'outil (`tool_family(name)` dans `tool_names.py`) qui fait correspondre un nom d'outil à une `ToolFamily`, avec `tool_cards.py`/`tool_extract.py` gérant le rendu par famille
c) Elle rend toujours du JSON brut pour les outils non reconnus, sans logique de dispatch
d) Chaque outil doit d'abord être enregistré dans `CocoOptions.allowed_tools` avant de pouvoir être rendu

### Q25. Comment l'App Builder permet-il à un « type » d'apporter son propre guidage CoCo dans un job de génération ?

a) En codant en dur des prompts à l'intérieur de `streamlit_coco` lui-même
b) Chaque dossier `types/<id>/` peut inclure un `SKILL.md` (+ `reference/`, `CHECKLIST.md`) monté via `add_dirs`, aux côtés de `types/shared/SKILL.md` pour les règles qui s'appliquent à chaque type
c) En appelant une API REST hébergée hors du dépôt
d) En écrivant directement dans `streamlit_coco/tool_names.py`

### Q26. Qu'est-ce qui détermine si l'étape de profilage d'un type de l'App Builder est un analyseur déterministe ou un job CoCo ?

a) La version de Streamlit installée
b) Le `grounding_kind` du type (`tabular`, `semantic_view`, `documents`, ou `urls`) — le grounding `tabular` utilise un analyseur pandas déterministe (`engine/profile.py`) ; les autres types passent par CoCo
c) Le fait que l'utilisateur soit sur la page Admin
d) Le `permission_mode` global défini pour l'application

### Q27. Qui récupère les sources de grounding « documents » ou « urls » de l'App Builder — la session CoCo ou l'application hôte ?

a) La session CoCo, via un outil réseau accordé
b) L'application hôte — les documents/URLs sont récupérés par l'hôte, jamais par la session CoCo, puisqu'aucun outil réseau ne lui est accordé
c) Ni l'un ni l'autre ; les sources de grounding doivent être pré-téléchargées manuellement avant chaque exécution
d) Une fonction externe séparée

### Q28. Un collègue demande pourquoi le dépôt n'a pas besoin d'un chapitre `reference-commands` de flags CLI comme le ferait un outil CLI typique. Quelle est l'explication exacte ?

a) La librairie ne fournit aucune commande
b) La surface principale du produit est une librairie Python (l'API), pas un CLI — les cibles du Makefile sont documentées comme `reference-commands` pour exécuter les démos, tandis que la référence propre de la librairie est la surface de l'API, traitée comme un analogue de « Commands »
c) La documentation CLI est intentionnellement retenue aux clients
d) La documentation propre du CLI CoCo remplace entièrement le besoin de toute référence locale

### Q29. Deux dépôts sont impliqués dans la publication vers PyPI aujourd'hui. Quel est l'arrangement actuel (temporaire), et pourquoi ?

a) Les releases sont taguées et publiées directement depuis `DevoteamSP/streamlit-coco-dev`
b) Les tags sur `lletourmy/streamlit-coco` (une surface de release publique temporaire) déclenchent la publication PyPI, jusqu'à ce que `DevoteamSP/streamlit-coco` soit validé pour PyPI et que la configuration Trusted Publisher y soit déplacée
c) Les releases PyPI sont des téléversements manuels sans tag de dépôt impliqué
d) `DevoteamSP/streamlit-coco` est déjà le dépôt de publication ; `-dev` ne sert qu'au suivi des issues

### Q30. En formant un nouveau membre de l'équipe au flux de release : quelle étape vient immédiatement après que `DRY_RUN=1 make sync-release` semble correct ?

a) `git push --tags` sur le dépôt `-dev` directement
b) `COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release`, puis taguer `vX.Y.Z` sur `lletourmy/streamlit-coco` (pas sur `-dev`)
c) Exécuter immédiatement `make publish` depuis le checkout `-dev`
d) Passer directement à `pip install streamlit-coco==X.Y.Z` pour vérifier

## Answer Key

| Q | Réponse | Explication |
|---|--------|-------------|
| 1 | **b** | `CocoSession` possède un `threading.Thread` nommé `coco-session` exécutant une boucle asyncio qui enveloppe `CortexCodeSDKClient`. |
| 2 | **a** | Les symboles headless du cœur s'importent sans charger Streamlit ; les exports UI se résolvent paresseusement via `__getattr__`/`_LAZY_ATTRS`, ce qui est ce qui permet à `headless_pipeline.py` de fonctionner sans Streamlit installé. |
| 3 | **b** | `can_use_tool` bloque le thread worker sur `PermissionManager.wait_for_decision()` jusqu'à résolution ou jusqu'à ce que `approval_timeout_seconds` s'écoule. |
| 4 | **b** | `options_hash()` ne hashe que les champs affectant les permissions d'outils ; le worker ne redémarre que lorsque ce hash change, pas à chaque édition d'option. |
| 5 | **b** | C'est un invariant documenté : le composant de prévisualisation reste agnostique de l'hôte et ne connaît pas les files de jobs. |
| 6 | **b** | `permissions.py` traite `AskUserQuestion` et `ExitPlanMode` comme cas particulier pour toujours créer une nouvelle demande, indépendamment de tout « always allow » antérieur. |
| 7 | **b** | C'est le texte exact du message de `SnowflakeConfigNotFoundError`. |
| 8 | **b** | `CLIProbeError` signifie spécifiquement que le binaire existe mais a échoué à répondre à `--version` ; `CLINotFoundError` couvre le cas non-sur-PATH. |
| 9 | **b** | `SessionStartError` est une erreur de worker qui échoue à démarrer ; `SessionNotReadyError` couvre le délai/échec de démarrage une fois démarré. |
| 10 | **b** | `context=` (`"session_start"`, `"session_ready"`/`"session"`, `"query"`, `"approval"`) oriente vers quelle sous-classe `CocoError` la détection de message aboutit. |
| 11 | **b** | `CwdUploadError` est levée aussi bien pour les noms invalides, les extensions non autorisées, les charges surdimensionnées, que les conflits d'écrasement. |
| 12 | **b** | `ApprovalTimeoutError` est documentée comme étant aussi une `TimeoutError`. |
| 13 | **b** | L'injection de prompt est notée sévérité élevée ; les portes d'approbation interceptant avant l'exécution sont l'atténuation principale, aux côtés d'une recommandation de rôle à privilège minimal. |
| 14 | **b** | L'escalade « Always allow » est de sévérité moyenne, atténuée purement par sa portée par outil/par session. |
| 15 | **b** | La répudiation est de sévérité moyenne, ouverte sous SEC-01 — rien de durable n'est écrit en dehors de l'état de session en mémoire. |
| 16 | **b** | L'atténuation est que la librairie ne journalise jamais les identifiants et que le SDK les masque (redacte) de sa propre sortie. |
| 17 | **a** | Le risque signalé est l'élévation de privilège via une dépendance compromise ; l'atténuation est `pip-audit`, Gitleaks, et un `uv.lock` commité. |
| 18 | **a** | Les portes d'approbation décident seulement si une instruction s'exécute ; une fois approuvée, sa portée est bornée uniquement par les grants réels du rôle connecté. |
| 19 | **A, B, C, F** | Skills, procédures Snowflake, Native App, et un catalogue de contrôles sont tous listés comme « n'ont pas déclenché » / hors périmètre ; commands et la référence API ont déclenché et sont documentés. |
| 20 | **c** | Le modèle de menace considère local/SiS/SPCS, mais seul local est réellement livré ; SiS/SPCS ne sont que du périmètre du modèle de menace et de la feuille de route. |
| 21 | **b** | La raison de cadrage donnée est simplement qu'il n'existe aucun fichier `*.tf` où que ce soit dans le dépôt. |
| 22 | **a** | La décision de cadrage explicite est un H2 par application d'exemple, pour éviter de reformuler les README d'exemple page par page. |
| 23 | **b** | `text_renderer` accepte un nom de préréglage ou un callable sur `panel()` et les fonctions d'aide à l'affichage associées. |
| 24 | **b** | Le dispatch `tool_family(name)` dans `tool_names.py` fait correspondre les noms d'outils à une `ToolFamily`, consommée par `tool_cards.py`/`tool_extract.py` pour le rendu. |
| 25 | **b** | Chaque dossier de type peut porter son propre `SKILL.md` (+ reference/checklist), monté via `add_dirs`, plus un `types/shared/SKILL.md` partagé. |
| 26 | **b** | `grounding_kind` décide : `tabular` utilise l'analyseur déterministe `engine/profile.py`, les autres types passent par CoCo. |
| 27 | **b** | Les documents/URLs sont récupérés par l'application hôte ; aucun outil réseau n'est accordé à la session CoCo. |
| 28 | **b** | La surface principale de la librairie est l'API Python, pas un CLI ; les cibles du Makefile obtiennent `reference-commands` pour les démos, tandis que l'API est le propre analogue « Commands » de la librairie. |
| 29 | **b** | `lletourmy/streamlit-coco` est la surface de release publique temporaire taguée pour la publication PyPI, jusqu'à ce que `DevoteamSP/streamlit-coco` soit validé pour PyPI. |
| 30 | **b** | Après un dry run propre, l'étape suivante documentée est la synchronisation commitée/poussée, puis le tag `vX.Y.Z` sur `lletourmy/streamlit-coco`, jamais sur `-dev`. |
