# Configuration

Faites fonctionner le dépôt de développement en local et vérifiez que vous
êtes prêt pour la [visite guidée](guided-tour.html) et les
[exercices pratiques](hands-on.html). Référence complète :
[`doc/deployment/local.md`](../../deployment/local.md) — cette page est le
chemin condensé, spécifique à la formation, à travers ce document.

## Comptes et permissions requis

- Un compte Snowflake avec **accès à Cortex Code**. Demandez à votre asset
  owner si vous n'en avez pas pour la formation — une connexion
  partagée/sandbox peut être disponible.
- Un accès Git à `DevoteamSP/streamlit-coco-dev` (le dépôt de
  développement). Si vous n'avez besoin que du paquet publié,
  `pip install "streamlit-coco[sdk]"` depuis PyPI suffit et vous pouvez
  sauter l'étape 1 ci-dessous.

## 1. Cloner et installer

```bash
git clone https://github.com/DevoteamSP/streamlit-coco-dev.git
cd streamlit-coco-dev
make install     # uv sync --extra dev
```

Vérifiez que le paquet s'importe et consultez la version :

```bash
uv run python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.9
```

## 2. Installer et vérifier la CLI CoCo

```bash
cortex --version
```

Si elle n'est pas dans le `PATH`, installez-la ou pointez vers le binaire :

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

`CocoOptions(cli_path=...)` fonctionne aussi, dans le code, comme
alternative à la variable d'environnement.

## 3. Configurer une connexion Snowflake

Créez ou confirmez `~/.snowflake/connections.toml` :

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
# warehouse, role, database, schema as needed
```

L'ancien `~/.snowflake/config.toml` est également détecté. Quand
`connection` est omis dans `CocoOptions`, le SDK utilise la connexion par
défaut de la Snowflake CLI.

## 4. Vérification de l'environnement (aucun agent démarré pour l'instant)

```bash
uv run python -c "
import streamlit_coco as st_coco
env = st_coco.check_environment(connection='analytics')
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
"
```

`env.ready` doit afficher `True`. Si ce n'est pas le cas, consultez le
tableau de dépannage dans
[`doc/deployment/local.md` §7](../../deployment/local.md#7-troubleshooting)
avant de continuer.

## 5. Exécuter la suite de tests

```bash
make check    # ruff + unit/smoke pytest (excludes tests/e2e)
```

Tous les tests doivent passer. Cela confirme que votre environnement Python
correspond à celui de la CI.

## 6. Lancer votre première démo

```bash
make chat
```

Un onglet de navigateur s'ouvre avec la démo `panel()` + `chat_input_bar()`
(`examples/chat_app.py`). Tapez un prompt — par exemple *« What tables are
available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1? »* (quelles tables sont
disponibles dans SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 ?) — et confirmez que vous
voyez une réponse en streaming avec au moins une carte d'outil.

## Checklist de vérification — vous êtes prêt quand...

- [ ] `uv run python -c "import streamlit_coco as c; print(c.__version__)"` affiche `0.1.9`
- [ ] `cortex --version` réussit
- [ ] `check_environment(...).ready` vaut `True`
- [ ] `make check` passe sans échec
- [ ] `make chat` ouvre une application fonctionnelle et vous obtenez une réponse en streaming avec au moins une carte d'outil

Si toutes les cases sont cochées, passez à [`guided-tour.md`](guided-tour.html).

## Référence rapide de dépannage

| Symptôme | Correctif |
| --- | --- |
| `SDKNotInstalledError` | Relancez `make install`, ou `pip install streamlit-coco[sdk]` |
| `CLINotFoundError` | Installez la CLI ; définissez `CORTEX_CODE_CLI_PATH` |
| `CocoConnectionError` | Corrigez `connections.toml` ; testez avec `cortex --version` et la Snowflake CLI directement |
| Session bloquée sur « Starting CoCo… » | Consultez les logs du terminal ; définissez `STREAMLIT_COCO_DEBUG=1` |

Tableau complet :
[`doc/deployment/local.md` §7](../../deployment/local.md#7-troubleshooting).
Le Guide technique contient la référence complète :
[`help.html`](../technical-guide/help.html).
