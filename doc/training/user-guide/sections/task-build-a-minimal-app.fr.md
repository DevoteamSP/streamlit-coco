# Je veux construire une app CoCo minimale

**Pour** un développeur Python construisant une app Streamlit · **10 min** · **un environnement Python fonctionnel**

Vous obtenez une app Streamlit à page unique qui intègre un panneau CoCo et
une barre de saisie, en utilisant le pattern d'intégration préféré.

## Avant de commencer

- `streamlit-coco[sdk]` installé (voir Enablement
  [`setup.html`](../../enablement/setup.html)).
- Une connexion Snowflake configurée et accessible —
  `check_environment().ready` devrait déjà valoir `True` ; voir
  [Prise en main](getting-started.html).
- Aucune app CoCo préalable n'est nécessaire ; c'est le point de départ pour
  chaque autre page de tâche de ce guide.

## Étapes

1. Créez `streamlit_app.py` et construisez un `CocoOptions` avec au moins un
   nom de connexion :

   ```python
   import streamlit as st
   import streamlit_coco as st_coco

   st.set_page_config(page_title="Minimal CoCo app")

   options = st_coco.CocoOptions(
       connection="my_connection",
       cwd=".",
   )
   ```

2. Appelez `check_environment()` via la porte d'accès, et arrêtez le script
   si elle n'est pas prête :

   ```python
   if not st_coco.render_start_gate(options):
       st.stop()
   ```

   `render_start_gate()` affiche lui-même l'écran d'accueil (statut
   SDK/CLI/Snowflake, une action **Start**) et retourne `False` tant que
   l'environnement ou l'utilisateur n'a pas confirmé — votre app doit
   appeler `st.stop()` dans ce cas, `render_start_gate()` n'arrête pas le
   script pour vous.

3. Récupérez ou créez la session pour cette page, et montez le panneau et sa
   barre de saisie :

   ```python
   session = st_coco.get_or_create_session(options)
   st_coco.panel(session)
   st_coco.chat_input_bar(session)
   ```

   `get_or_create_session()` stocke la session dans
   `st.session_state["coco"]` par défaut (à surcharger avec `key=`) et la
   réutilise d'un rerun à l'autre.

4. Exécutez l'app :

   ```bash
   streamlit run streamlit_app.py
   ```

5. Tapez un prompt dans la barre de saisie en bas de la page et vérifiez que
   l'historique de conversation affiche une réponse en streaming au-dessus.

## Résultat

Un onglet de navigateur affichant le panneau CoCo : un en-tête de statut, un
historique de conversation vide, et la barre de saisie. Après un prompt,
l'historique se remplit avec la réponse en streaming de l'agent et les
cartes d'outils qu'il a utilisées. Aucun fichier n'est écrit par cette app
minimale à elle seule — la sortie fichier démarre une fois que vous ajoutez
des téléversements
([Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html))
ou que l'agent écrit dans `cwd`.

## Variations

- Utilisez `copilot_rail()` au lieu de `panel()` + `chat_input_bar()` pour
  intégrer CoCo comme un rail à droite dans une app multipage plus large
  plutôt qu'un chat à page unique — voir les exemples Backlog Desk et
  BI → Semantic dans
  [Référence des exemples d'apps](reference-examples.html).
- Définissez `panel(session, output_mode="field")` pour n'afficher que la
  dernière sortie de l'assistant au lieu de l'historique complet.
- Définissez `warm_up=True` sur `render_start_gate()` (le défaut) pour
  démarrer la session dès que la porte d'accès est franchie, plutôt que
  d'attendre le premier prompt.

## En cas d'échec

- [`SDKNotInstalledError`](../../technical-guide/help.html#sdk-not-installed)
- [`CLINotFoundError`](../../technical-guide/help.html#cli-not-found)
- [Session bloquée sur « Starting CoCo… »](../../technical-guide/help.html#session-stuck-connecting)
- [Saisie désactivée après le démarrage](../../technical-guide/help.html#input-disabled-after-boot)
