# Prise en main

## Accès et prérequis

- Python >=3.10, un environnement virtuel, et Streamlit >=1.55.
- Un compte Snowflake avec accès Cortex Code, et une connexion configurée
  dans `~/.snowflake/connections.toml` (ou l'ancien `~/.snowflake/config.toml`).
  Cette bibliothèque ne stocke ni ne journalise jamais les identifiants
  elle-même — l'authentification est déléguée à la CLI CoCo, au SDK, et à la
  configuration Snowflake au niveau du système d'exploitation.
- La CLI `cortex` accessible sur `PATH`, ou `CORTEX_CODE_CLI_PATH` défini
  vers son emplacement.

L'installation et la configuration de la CLI sont couvertes pas à pas dans
Enablement [`setup.html`](../../enablement/setup.html) — suivez d'abord
cette page si vous n'avez pas encore installé `streamlit-coco`. Cette page
suppose que l'installation est faite et reprend à partir d'un checkout
fonctionnel.

## Première exécution

1. Confirmez que l'environnement est prêt avant d'écrire le moindre code
   d'app :

   ```python
   import streamlit_coco as st_coco

   env = st_coco.check_environment()
   print(env.ready, env.sdk_installed, env.cli_ok, env.snowflake_config_found)
   ```

   `check_environment()` ne lève jamais d'exception — elle retourne toujours
   un `CocoEnvironment`, donc un `False` ici signale quelque chose à
   corriger, pas un plantage. Voir
   [Concepts](concepts.html#cocoenvironment) et
   [Référence API](reference-api.html) pour chaque champ.

2. Lancez la démo maison pour voir une app fonctionnelle avant d'écrire la
   vôtre :

   ```bash
   make chat
   ```

   Cela exécute `examples/chat_app.py` — le pattern d'intégration préféré
   (`check_environment` → `render_start_gate` → `get_or_create_session` →
   `panel()` + `chat_input_bar()`) sous sa forme la plus réduite possible.
   Les détails et les autres exemples d'apps sont dans
   [Je veux exécuter les exemples d'apps](task-run-the-example-apps.html).

3. Construisez votre propre app minimale à partir du même pattern :
   [Je veux construire une app CoCo minimale](task-build-a-minimal-app.html).

## Vous avez terminé quand…

- `check_environment().ready` vaut `True` pour la connexion que vous comptez
  utiliser.
- `make chat` ouvre un onglet de navigateur affichant le panneau CoCo, et un
  prompt que vous tapez obtient une réponse en streaming.
- Vous pouvez pointer les quatre appels du pattern préféré
  (`check_environment` → `render_start_gate` → `get_or_create_session` →
  `panel()`) dans `examples/chat_app.py` et expliquer ce que fait chacun.

Si `check_environment()` signale un problème, ou si l'app reste bloquée
avant qu'une réponse n'apparaisse, voir la
[FAQ](faq.html) ou
[`help.html`](../../technical-guide/help.html) dans le Guide Technique.
