# streamlit-coco — Certification Enablement

**Seuil de réussite : 8/10.** Prérequis : parcours Enablement.

### Q1. Quel problème `streamlit-coco` résout-il pour l'auteur d'une application Streamlit ?

a) Il remplace entièrement le CLI CoCo, de sorte qu'aucune installation de CLI n'est jamais nécessaire
b) Il fournit une plomberie prête à l'emploi pour la session, le rendu en streaming, les cartes d'outils et le flux d'approbation, afin que l'auteur n'ait pas à la construire lui-même
c) Il génère automatiquement les définitions de rôles et de grants Snowflake
d) Il provisionne et gère l'entrepôt (warehouse) Snowflake contre lequel s'exécute une session CoCo

### Q2. Quel énoncé décrit le mieux `panel()` ?

a) Un Copilot en rail latéral composé pour les applications multipages
b) Une primitive native historique/champ/approbations/Stop qui retourne un `CocoChatResult`
c) Un widget de chat tout-en-un hérité de Custom Component v2
d) Une colonne de prévisualisation qui intègre une application Streamlit enfant dans une iframe

### Q3. Qu'ajoute `copilot_rail()` par rapport à `panel()` ?

a) Un Copilot en rail latéral avec un sélecteur de connexion, des jobs en file d'attente et des questions d'exemple
b) Une API headless purement asynchrone sans import de Streamlit
c) Un routeur de sortie structurée basé sur JSON Schema
d) Une protection contre le path-traversal dans les noms de fichiers téléversés

### Q4. Que fait `app_viewer()` ?

a) Exécute l'outil SQL de l'agent contre le rôle Snowflake connecté
b) Lance un processus enfant `streamlit run` pour une application générée, l'intègre dans une iframe, et propose une action Fix
c) Diffuse les événements NDJSON bruts de l'agent vers le terminal
d) Téléverse des fichiers du navigateur dans le répertoire de travail de l'agent

### Q5. Quelle commande lance l'implémentation de référence officielle du pattern préféré (`panel()` + `chat_input_bar()`) ?

a) `make demo`
b) `make chat`
c) `make run-app`
d) `make copilot`

### Q6. Quel ensemble de prérequis est exact pour démarrer le parcours Enablement ?

a) Python 3.10+, un compte Snowflake avec accès à Cortex Code, le CLI CoCo (`cortex`) accessible sur `PATH` ou via `CORTEX_CODE_CLI_PATH`, et une configuration de connexion Snowflake fonctionnelle
b) Node.js 18+, un entrepôt (warehouse) Snowflake dédié, et une licence GHAS payante
c) Python 3.8+, Docker, et un manifeste Native App
d) Un compte Streamlit Community Cloud et un fichier `snowflake.yml`

### Q7. Lesquels de ces éléments font partie du pipeline du pattern préféré démontré dans `examples/chat_app.py` ? (Choix multiple — sélectionnez toutes les réponses applicables)

a) `check_environment()`
b) `render_start_gate()`
c) `get_or_create_session()`
d) `panel()`
e) `chat_input_bar()`
f) `chat()` (composant hérité CCv2)

### Q8. Quelle commande installe `streamlit-coco` pour quelqu'un qui a seulement besoin du package publié, et non d'un checkout du dépôt de développement ?

a) `pip install "streamlit-coco[sdk]"`
b) `npm install streamlit-coco`
c) `make install` (fonctionne uniquement à l'intérieur du checkout du dépôt de développement)
d) `uv build`

### Q9. Sous quelle licence `streamlit-coco` est-il publié ?

a) MIT
b) Apache-2.0
c) GPL-3.0
d) BSD-3-Clause

### Q10. Quelle est la version actuelle du package et son statut de publication décrits par ce pack de formation ?

a) `0.1.6`, une version stable
b) `0.1.9`, alpha — l'API peut encore évoluer
c) `1.0.0`, disponibilité générale
d) `0.2.0`, bêta

## Answer Key

| Q | Réponse | Explication |
|---|--------|-------------|
| 1 | **b** | La librairie fournit l'état de session, le streaming de l'historique de conversation, les cartes d'outils et la plomberie d'approbation sous forme de fonctions composables, afin que l'auteur d'application écrive la page et les options, pas le pont vers la session. |
| 2 | **b** | `panel(session, **kwargs) -> CocoChatResult` est la primitive native de sortie historique/champ, avec approbations et un contrôle Stop. |
| 3 | **a** | `copilot_rail()` compose `panel()` en un Copilot en rail latéral avec un sélecteur de connexion, des jobs en file d'attente, une configuration d'affichage de l'historique de conversation et des questions d'exemple. |
| 4 | **b** | `app_viewer(app_dir, ...)` lance un processus enfant `streamlit run`, l'intègre dans une iframe, et propose Fix with CoCo en analysant le journal de prévisualisation. |
| 5 | **b** | Le Makefile associe `chat` à « Run examples/chat_app.py » ; `demo`, `run-app` et `copilot` ne sont pas des cibles du Makefile. |
| 6 | **a** | Les prérequis sont Python 3.10+, un compte Snowflake avec Cortex Code activé, le CLI `cortex` sur PATH (ou `CORTEX_CODE_CLI_PATH`), et un `connections.toml`/`config.toml` fonctionnel — aucun entrepôt dédié, Docker ou manifeste Native App n'est requis. |
| 7 | **A, B, C, D, E** | `chat_app.py` enchaîne `check_environment()` → `render_start_gate()` → `get_or_create_session()` → `panel()` + `chat_input_bar()` ; `chat()` est le composant hérité CCv2 utilisé dans `examples/approval_gate.py`, pas dans cet exemple. |
| 8 | **a** | Le chemin réservé au package publié uniquement est `pip install "streamlit-coco[sdk]"` ; `make install` cible un checkout de dépôt, et les deux autres commandes n'installent pas ce package. |
| 9 | **b** | `streamlit-coco` est publié sous licence Apache-2.0. |
| 10 | **b** | Le pack décrit la version `0.1.9`, indiquée comme alpha — l'API peut encore évoluer. |
