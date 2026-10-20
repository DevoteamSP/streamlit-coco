# Je veux exécuter les exemples d'apps

**Pour** toute personne évaluant ou apprenant la bibliothèque · **20 min** · **une connexion Snowflake pour les démos adossées à CoCo**

Vous obtenez chacun des exemples d'apps du dépôt en cours d'exécution en
local, et savez lequel démontre quelle partie de l'API.

## Avant de commencer

- `streamlit-coco[sdk]` installé et `check_environment().ready` vaut `True`
  (voir [Prise en main](getting-started.html)).
- Un checkout du dépôt (les exemples s'exécutent via des cibles `make`, pas
  via une simple installation pip).
- `headless_pipeline.py` et les écrans estate-map/KPI de BI → Semantic
  fonctionnent sans connexion Snowflake active ; les autres en ont besoin.

## Étapes

1. Exécutez la démo de chat au pattern préféré :

   ```bash
   make chat
   ```

   C'est `examples/chat_app.py` — l'app fonctionnelle la plus réduite,
   construite sur `check_environment` → `render_start_gate` →
   `get_or_create_session` → `panel()` + `chat_input_bar()`. Sa barre
   latérale inclut un lanceur de prompts de test adossé à
   `examples/testdata/prompts.json`.

2. Exécutez la démo legacy tout-en-un :

   ```bash
   make approval
   ```

   C'est `examples/approval_gate.py`, construit sur le helper `chat()` CCv2
   legacy plutôt que `panel()`.

3. Exécutez la démo de sortie structurée :

   ```bash
   make structured
   ```

   C'est `examples/structured_output.py` — elle définit `output_schema` et
   route le JSON de l'agent vers un widget via `on_structured_output` au
   lieu du texte de chat.

4. Exécutez la démo headless depuis un terminal, sans navigateur :

   ```bash
   make headless
   ```

   C'est `examples/headless_pipeline.py` — du Python asynchrone pur sans
   aucun import Streamlit, pilotant directement `query()` et `CocoSession`.

5. Exécutez la démo de téléversement de fichiers :

   ```bash
   make cwd-upload
   ```

   C'est `examples/cwd_upload_chat.py` — `chat_input_bar(accept_file=...)`
   et `cwd_uploader()` câblent les téléversements du navigateur vers le
   `cwd` de l'agent.

6. Exécutez les deux démos multipages en rail à droite :

   ```bash
   make backlog        # Product Backlog Desk — fichier/JSON, sans SQL
   make bi-semantic     # BI -> Semantic (alias : make tableau-semantic)
   ```

7. Exécutez la démo de génération d'app guidée :

   ```bash
   make app-builder
   ```

Chaque cible `make` et ses variables sont listées dans la
[Référence des commandes](reference-commands.html) ; ce que chaque exemple
démontre et ce dont il a besoin figure dans la
[Référence des exemples d'apps](reference-examples.html).

## Résultat

Chaque cible `make` ouvre (ou affiche, pour `make headless`) une app en
cours d'exécution sur son propre port. Rien en dehors de `examples/` n'est
modifié par l'exécution d'une démo ; les artefacts générés atterrissent sous
le répertoire `out/` ou `data/` propre à chaque exemple — voir
[Sorties](outputs.html).

## Variations

- `make run` exécute `examples/chat_app.py` par défaut ; définissez
  `EXAMPLE=` pour la pointer vers un autre fichier d'exemple.
- `make tableau-semantic` est un alias déprécié de `make bi-semantic` —
  utilisez ce dernier.

## En cas d'échec

- [L'aperçu ne démarre pas](../../technical-guide/help.html#preview-wont-start)
- [« Fix with CoCo » non câblé pour un écran](../../technical-guide/help.html#fix-with-coco-not-wired)
- [Échec de parsing du log d'aperçu](../../technical-guide/help.html#preview-log-parse-miss)
