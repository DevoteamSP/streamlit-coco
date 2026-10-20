# streamlit-coco — Certification Avancée

**Seuil de réussite : 24/30.** Prérequis : ≥ 3 mois d'utilisation.

### Q1. Qu'est-ce que le correctif `0.1.8` a changé concernant la page Studio de l'App Builder ?

a) « Save & regenerate » écrit désormais `BRIEF.md` à partir des widgets expander avant de mettre CoCo en file d'attente, fermant une course où la page Brief pouvait écraser le fichier tout juste édité sur le même tour
b) La page Brief a gagné un nouveau bouton « Publish »
c) `output_schema` a cessé de retirer `$schema`/`$id`
d) Le port de prévisualisation de l'App Builder est passé de 8513 à 8511

### Q2. Qu'est-ce que le correctif `0.1.7` a changé concernant `make audit` / `pip-audit` en CI ?

a) Il est passé de `pip-audit` à `safety`
b) Il a ajouté `--skip-editable`, évitant un faux positif « dependency not found on PyPI » juste après un bump de version pré-tag
c) Il a désactivé `pip-audit` en CI entièrement
d) Il a déplacé le job d'audit de `security.yml` vers `release.yml`

### Q3. Quelles deux choses le correctif `0.1.6` a-t-il traitées ?

a) Ajout d'un nouveau champ `output_schema` et suppression de `on_structured_output`
b) Retrait de `$schema`/`$id` avant de transmettre le JSON Schema au SDK CoCo, et remplacement de `use_container_width` (déprécié) par `width="stretch"`
c) Ajout de `max_turns` et suppression de `approval_timeout_seconds`
d) Passage de l'exemple de sortie structurée de `panel()` à `chat()`

### Q4. Quelle erreur JSON Schema le correctif `0.1.6` a-t-il spécifiquement évitée ?

a) `no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`, provenant d'un fichier de contrat qui inclut un URI de draft
b) `KeyError: 'properties'`
c) `TypeError: schema must be a dict`
d) `ValidationError: additionalProperties not allowed`

### Q5. Qu'est-ce qui a changé dans le workflow de sécurité `0.1.5` ?

a) CodeQL a été ajouté pour la première fois
b) CodeQL a été retiré (une organisation privée a besoin d'une licence GHAS) ; Gitleaks et pip-audit ont été conservés
c) Gitleaks a été remplacé par la version payante `gitleaks-action@v2`
d) pip-audit a été abandonné au profit d'un autre scanner

### Q6. Qu'est-ce que le correctif `0.1.0` a changé concernant les cartes d'outils Grep/Glob terminées ?

a) Elles affichent désormais un résumé compact plutôt qu'un dump complet du résultat
b) Elles n'affichent désormais que du JSON brut
c) Elles ont été retirées entièrement de l'historique de conversation
d) Elles requièrent désormais une approbation manuelle à chaque fois

### Q7. Une session lève `SDKNotInstalledError`. Qu'est-ce que cela indique, et quelle est la solution ?

a) Le CLI CoCo n'est pas sur `PATH` ; définir `CORTEX_CODE_CLI_PATH`
b) Le SDK Python (`cortex-code-agent-sdk`) est manquant ; exécuter `pip install streamlit-coco[sdk]` (ou `make install`)
c) Le nom de connexion Snowflake est incorrect ; corriger `connections.toml`
d) L'approbation a expiré ; augmenter `approval_timeout_seconds`

### Q8. Une session lève `CLIProbeError`. Que signifie ceci ?

a) Le binaire `cortex` n'a été trouvé nulle part sur `PATH`
b) Un binaire existe au chemin configuré mais n'a pas répondu correctement à `--version`
c) Le nom de connexion Snowflake n'existe pas dans `connections.toml`
d) Le package du SDK Python n'est pas installé

### Q9. Une session reste bloquée sur « Starting CoCo… » sans autre progression. Quelle est l'étape de diagnostic initiale recommandée ?

a) Réinstaller `streamlit-coco` depuis PyPI
b) Vérifier les journaux du terminal et activer le mode debug (`STREAMLIT_COCO_DEBUG=1`)
c) Supprimer `~/.snowflake/connections.toml` et le recréer
d) Basculer `permission_mode` sur `"plan"`

### Q10. Le champ de saisie du chat reste désactivé juste après le démarrage de l'application. Quelle est la cause probable et la solution ?

a) `SessionNotReadyError` / un statut d'erreur — corriger l'environnement et réinitialiser la session depuis la barre latérale
b) `CwdUploadError` provenant d'une extension de fichier rejetée
c) `ApprovalTimeoutError` après 600 secondes sans réponse
d) Un `output_schema` manquant

### Q11. Quel est le comportement `overwrite` par défaut de `upload_to_cwd()`, et en quoi diffère-t-il du défaut de téléversement de `chat_input_bar()` ?

a) Les deux ont pour défaut `"replace"`
b) `upload_to_cwd()` a pour défaut `"error"` ; `chat_input_bar()` fixe son `upload_overwrite` par défaut à `"replace"`
c) `upload_to_cwd()` a pour défaut `"skip"` ; `chat_input_bar()` a pour défaut `"error"`
d) Les deux ont pour défaut `"skip"`

### Q12. Que recherche l'analyseur de journaux de `app_viewer()` pour détecter une erreur, et quelle en est une limitation connue ?

a) Il recherche `Uncaught app exception` / `Traceback (most recent call last):` ; une ligne horodatée ultérieure peut être lue comme « erreur résolue » même si l'erreur persiste
b) Il analyse directement le DOM de l'application prévisualisée, puisqu'elle partage une origine avec l'hôte
c) Il se fie uniquement au code de sortie du processus enfant
d) Il interroge le point de terminaison `/healthz` du serveur Streamlit

### Q13. Pourquoi l'application hôte de `app_viewer()` ne peut-elle pas lire directement la traceback DOM de l'application prévisualisée ?

a) L'application enfant s'exécute dans une iframe sur une autre origine, donc « Fix with CoCo » se limite à l'analyse du journal
b) Streamlit désactive l'accès au DOM pour toutes les iframes par politique
c) L'application enfant est rendue entièrement côté serveur, sans DOM
d) `on_fix` n'est jamais câblé dans aucun exemple officiel

### Q14. Quand `ApprovalTimeoutError` se déclenche-t-elle ?

a) L'outil s'exécute automatiquement dès que « Always allow » s'appliquerait
b) Après l'écoulement de `approval_timeout_seconds` (600 s par défaut, soit 10 min) sans réponse
c) Uniquement pour la famille d'outils SQL
d) Immédiatement dès qu'une carte d'outil est rendue, quel que soit le paramètre de timeout

### Q15. « Always allow » est-il jamais persisté à travers un redémarrage du processus Streamlit ?

a) Oui, il est écrit dans la configuration `~/.snowflake/`
b) Non — il est limité à la session uniquement et s'efface à la réinitialisation ou au redémarrage
c) Oui, mais uniquement pour la famille d'outils SQL
d) Oui, si `require_approval_for` est une liste plutôt qu'un callable

### Q16. Que remplace la variable d'environnement `CORTEX_CODE_CLI_PATH` ?

a) Le nom de connexion Snowflake
b) Le chemin du CLI `cortex`, lorsqu'il n'est pas sur `PATH` ou transmis via `CocoOptions.cli_path`
c) Le sous-répertoire de téléversement utilisé par `cwd_uploader()`
d) La durée du délai d'expiration d'approbation

### Q17. Quelles valeurs `is_debug_mode()` considère-t-elle comme vraies pour `STREAMLIT_COCO_DEBUG` / `COCO_DEBUG` ?

a) N'importe quelle chaîne non vide
b) `"1"`, `"true"`, `"yes"`, `"on"` (insensible à la casse), ou un `st.session_state["coco_debug"]` vrai
c) Uniquement l'entier `1`, rien d'autre
d) `"debug"` ou `"verbose"`

### Q18. Où `TTS_DATA_MODE` est-il lu, et qu'affecte-t-il ?

a) C'est une variable d'environnement globale lue par `streamlit_coco/diagnostics.py` pour sélectionner la connexion Snowflake
b) Elle n'est lue que par le processus de prévisualisation enfant de `examples/bi_to_semantic` (via `app_viewer(env=...)`) pour sélectionner le mode de données déconnecté ou connecté pour l'application consommatrice générée
c) Elle contrôle si les charges utiles de `STREAMLIT_COCO_DEBUG` sont affichées
d) C'est une variable requise pour chaque application d'exemple

### Q19. Quel est le statut du constat de sécurité SEC-01 ?

a) Résolu en `0.1.5` — un journal d'audit des approbations est désormais persisté
b) Ouvert, cible v0.2 — persister un journal d'audit des approbations (qui a approuvé quoi, quand)
c) Non suivi ; il n'y a aucune exigence de journal d'audit
d) Résolu en `0.1.0`

### Q20. Quel est le statut de SEC-02 ?

a) Résolu — un document de recommandation de rôle à privilège minimal dédié est commité dans le dépôt
b) Ouvert, cible v0.2 — documenter une recommandation de rôle à privilège minimal dédié ; la page de sécurité actuelle ne donne qu'un guidage intérimaire
c) Non applicable ; la librairie gère directement les grants Snowflake
d) Résolu en `0.1.5` en même temps que le retrait de CodeQL

### Q21. Quel est le statut actuel de CodeQL dans la CI de ce dépôt ?

a) Il s'exécute sur chaque PR, comme le tableau récapitulatif de `findings-report.md` l'indique toujours
b) Il a été retiré en `0.1.5` parce que l'organisation GitHub privée ne dispose pas d'une licence GHAS ; seuls Gitleaks et pip-audit s'exécutent aujourd'hui
c) Il ne s'exécute que selon la planification hebdomadaire du lundi, pas sur les PR
d) Il a été remplacé par un autre analyseur statique en `0.1.6`

### Q22. Quels deux scanners s'exécutent réellement dans `security.yml` aujourd'hui, et sur quels déclencheurs ?

a) CodeQL et Gitleaks, sur chaque push uniquement
b) Gitleaks (CLI) et `pip-audit --skip-editable`, sur chaque PR, chaque push vers `main`, et chaque semaine (lundi)
c) pip-audit et un scanner de dépendances, uniquement de nuit
d) Gitleaks uniquement, sur les tags de release

### Q23. Quels éléments de sécurité sont OUVERTS (non résolus) selon le modèle de menace ? (Choix multiple — sélectionnez toutes les réponses applicables)

a) SEC-01 — journal d'audit des approbations persisté
b) SEC-02 — document de recommandation de rôle à privilège minimal
c) SEC-03 — commiter `uv.lock`
d) SEC-04 — génération de SBOM en CI

### Q24. Selon la revue manuelle dans `findings-report.md` (version auditée `0.1.0`), lequel de ces éléments la revue n'a-t-elle PAS trouvé dans le code source ?

a) `shell=True`, des identifiants codés en dur, ou l'usage de `eval()`/`exec()`
b) Tout usage de `pandas`
c) Tout widget Streamlit
d) Toute annotation de type

### Q25. Qu'est-ce qui déclenche le redémarrage du worker en arrière-plan d'une `CocoSession` ?

a) Tout changement sur n'importe quel champ de `CocoOptions`
b) Un changement de `options_hash()`, calculé uniquement à partir des champs qui affectent les permissions d'outils (par ex. `allowed_tools`, `disallowed_tools`, `permission_mode`, `require_approval_for`)
c) Chaque appel à `session.send()`
d) Un rerun Streamlit, indépendamment des changements d'options

### Q26. Que fait `wrap_exception()` ?

a) Il retente un appel SDK échoué jusqu'à trois fois avant de lever une exception
b) Il fait correspondre les exceptions brutes du SDK/runtime aux sous-classes typées `CocoError` de la librairie, par détection de message combinée à un kwarg `context=` (par ex. `"session_start"`, `"query"`, `"approval"`)
c) Il supprime toutes les exceptions et les journalise silencieusement
d) Il convertit toute exception en `SDKNotInstalledError`

### Q27. Que sous-classe également `ApprovalTimeoutError`, en plus de `CocoError` ?

a) `ValueError`
b) `TimeoutError`
c) `ConnectionError`
d) `KeyError`

### Q28. Que sous-classe également `SDKNotInstalledError`, en plus de `CocoError` ?

a) `ImportError`
b) `RuntimeError`
c) `OSError`
d) `AttributeError`

### Q29. Que le workflow CI `ci.yml` exécute-t-il sur chaque PR vers `main` ?

a) Les tests unitaires et e2e, sans agent CoCo réel
b) Uniquement les checklists manuelles/live qui nécessitent un vrai CLI et Snowflake
c) Uniquement `make audit`
d) Une build de release complète et une publication vers PyPI

### Q30. Pourquoi `make audit` a-t-il pu échouer de manière fallacieuse juste après un bump de version, avant le correctif `0.1.7` ?

a) `pip-audit` traitait la version locale fraîchement bumpée, pas encore publiée, comme « dependency not found on PyPI » — corrigé en ajoutant `--skip-editable`
b) `ruff` signalait la chaîne de version comme invalide
c) Le fichier de lock n'était pas commité
d) CodeQL bloquait le pipeline

## Answer Key

| Q | Réponse | Explication |
|---|--------|-------------|
| 1 | **a** | CHANGELOG `0.1.8` Fixed : Save & regenerate écrit désormais `BRIEF.md` avant de mettre CoCo en file d'attente, fermant la course à l'écrasement. |
| 2 | **b** | CHANGELOG `0.1.7` Fixed : `--skip-editable` évite un faux échec d'audit « not found on PyPI » après un bump de version. |
| 3 | **b** | CHANGELOG `0.1.6` Fixed couvre à la fois le retrait de `$schema`/`$id` et le changement `use_container_width` → `width="stretch"`. |
| 4 | **a** | Le texte d'erreur exact cité dans l'entrée Fixed de `0.1.6` est le rejet de la référence de schéma avec URI de draft. |
| 5 | **b** | CHANGELOG `0.1.5` Changed (Security) : CodeQL retiré (manque de licence GHAS), Gitleaks et pip-audit conservés. |
| 6 | **a** | CHANGELOG `0.1.0` Fixed : les cartes Grep/Glob terminées affichent un résumé compact plutôt qu'un dump complet. |
| 7 | **b** | `SDKNotInstalledError` signifie que l'extra SDK optionnel est manquant ; la solution est `pip install streamlit-coco[sdk]` ou `make install`. |
| 8 | **b** | `CLIProbeError` signifie spécifiquement « binaire trouvé mais `--version` a échoué », distinct de `CLINotFoundError`. |
| 9 | **b** | La solution du tableau de dépannage pour une connexion bloquée est de vérifier les journaux du terminal et d'activer `STREAMLIT_COCO_DEBUG=1`. |
| 10 | **a** | Une saisie désactivée après le démarrage correspond à `SessionNotReadyError`/un statut d'erreur ; corriger l'environnement et réinitialiser depuis la barre latérale. |
| 11 | **b** | Le défaut propre de `upload_to_cwd()` est `overwrite="error"` ; `chat_input_bar()` fixe son défaut `upload_overwrite` à `"replace"`. |
| 12 | **a** | L'analyseur détecte ces deux chaînes ; une ligne horodatée ultérieure peut être mal interprétée comme une résolution de l'erreur. |
| 13 | **a** | La prévisualisation enfant est une autre origine (port différent), donc seul le journal analysé — pas le DOM — est disponible pour « Fix with CoCo ». |
| 14 | **b** | `ApprovalTimeoutError` se déclenche une fois `approval_timeout_seconds` (600 s par défaut) écoulé sans décision. |
| 15 | **b** | « Always allow » ne vit que dans `PermissionManager.always_allowed_tools` en mémoire ; il s'efface à `reset()`, `close()`, ou au redémarrage. |
| 16 | **b** | `CORTEX_CODE_CLI_PATH` remplace la recherche du chemin du CLI lorsque le CLI n'est pas sur `PATH` et que `cli_path` n'a pas été transmis. |
| 17 | **b** | L'ensemble de valeurs vraies documenté de `is_debug_mode()` est `"1"`/`"true"`/`"yes"`/`"on"` (insensible à la casse) ou un indicateur d'état de session vrai. |
| 18 | **b** | `TTS_DATA_MODE` n'est lu qu'à l'intérieur du processus de prévisualisation enfant de `bi_to_semantic`, via `app_viewer(env=...)`. |
| 19 | **b** | SEC-01 est listé comme ouvert, cible v0.2, dans `threat-model.md` §7. |
| 20 | **b** | SEC-02 est listé comme ouvert, cible v0.2 ; le guidage actuel de la page de sécurité est intérimaire, pas le livrable suivi. |
| 21 | **b** | `0.1.5` a retiré le job CodeQL pour des raisons de licence ; `security.yml` n'exécute aujourd'hui que Gitleaks et pip-audit. |
| 22 | **b** | Gitleaks (CLI) et `pip-audit --skip-editable` s'exécutent sur PR, push vers main, et la planification hebdomadaire du lundi. |
| 23 | **A, B** | SEC-01 et SEC-02 sont ouverts (cible v0.2) ; SEC-03 (fichier de lock) et SEC-04 (SBOM) sont tous deux résolus. |
| 24 | **a** | La revue manuelle indique explicitement qu'aucun `shell=True`, aucun identifiant codé en dur, et aucun usage de `eval()`/`exec()` n'a été trouvé. |
| 25 | **b** | `options_hash()` ne hashe que les champs affectant les permissions d'outils ; `CocoSession` ne redémarre son worker que lorsque ce hash change. |
| 26 | **b** | `wrap_exception()` détecte le message de l'exception brute et utilise `context=` pour choisir la bonne sous-classe `CocoError`. |
| 27 | **b** | `ApprovalTimeoutError` est documentée comme étant aussi une `TimeoutError`. |
| 28 | **a** | `SDKNotInstalledError` est documentée comme étant aussi une `ImportError`. |
| 29 | **a** | La CI exécute les tests unitaires et e2e sur chaque PR vers `main`, sans agent CoCo réel ; les vérifications live sont manuelles uniquement. |
| 30 | **a** | Avant `0.1.7`, `pip-audit` sans `--skip-editable` signalait la version locale tout juste bumpée comme absente de PyPI. |
