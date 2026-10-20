# Installation

Une seule cible de déploiement est livrée aujourd'hui : **locale** —
Streamlit, le CLI CoCo, et la configuration de connexion Snowflake, tous sur
le même hôte. Les chemins d'installation Streamlit in Snowflake (SiS) et
SPCS ne sont pas implémentés dans ce dépôt aujourd'hui. Ils n'apparaissent
que comme périmètre dans [security](security.html#threat-model-summary)
(contexte du modèle de menace) et dans la feuille de route du projet, pas
comme quelque chose que vous pouvez installer.

## Matrice des prérequis

| Prérequis | Version | Pourquoi |
|---|---|---|
| Python | 3.10+ | `requires-python = ">=3.10"` dans `pyproject.toml` |
| Streamlit | >=1.55 | `streamlit-coco` déclare `streamlit>=1.55` comme sa seule dépendance forte |
| CLI CoCo (`cortex`) | accessible sur le `PATH`, ou `CORTEX_CODE_CLI_PATH` défini | Le SDK le fait naître comme sous-processus ; la bibliothèque ne l'embarque pas |
| `cortex-code-agent-sdk` | >=1.0.7 | Installé via l'extra `[sdk]` ; la bibliothèque parle à CoCo à travers ce SDK |
| Connexion Snowflake | un profil dans `~/.snowflake/connections.toml` (ou l'ancien `config.toml`) | Le CLI/SDK s'authentifient via ce fichier ; la bibliothèque ne stocke jamais d'identifiants |

## Installation locale — étapes ordonnées

### 1. Installer le package

```bash
pip install "streamlit-coco[sdk]"
```

ou, depuis un clone (contributeurs sur `streamlit-coco-dev`) :

```bash
git clone https://github.com/DevoteamSP/streamlit-coco.git
cd streamlit-coco
make install   # uv sync --extra dev
```

Vérifier :

```bash
python -c "import streamlit_coco as c; print(c.__version__)"
# -> 0.1.9
```

### 2. Installer le CLI CoCo

Le Cortex Code Agent SDK fait naître le CLI CoCo (`cortex`) comme
sous-processus. Il doit être installé et accessible sur la même machine que
l'application Streamlit.

Vérifier :

```bash
cortex --version
```

S'il n'est pas sur le `PATH` :

```bash
export CORTEX_CODE_CLI_PATH=/path/to/cortex
```

(ou passez `cli_path=` sur `CocoOptions` — voir
[configuration](configuration.html)).

### 3. Configurer une connexion Snowflake

Créez ou mettez à jour `~/.snowflake/connections.toml` :

```toml
[connections.analytics]
account = "xy12345"
user = "you@company.com"
authenticator = "externalbrowser"
```

L'ancien `~/.snowflake/config.toml` est également détecté. Voir
[security](security.html#roles-and-grants) pour le rôle que cette connexion
devrait utiliser.

Vérifier (sonde le SDK, le CLI, et la configuration sans démarrer d'agent) :

```python
import streamlit_coco as st_coco

env = st_coco.check_environment(connection="analytics")
print(env.ready, env.sdk_version, env.cli_version, env.snowflake_config_display)
```

Pour un script qui doit échouer rapidement plutôt que de renvoyer un objet
de statut :

```python
st_coco.require_environment(connection="analytics")
```

### 4. Lancer une application d'exemple

```bash
make chat
```

Vérifier : le navigateur s'ouvre sur la démo de chat et la start gate
(« Start CoCo Chat ») affiche le statut SDK / CLI / Snowflake en vert avant
que vous ne cliquiez dessus. Voir [operations](operations.html) pour la
liste complète des cibles `make` qui lancent des applications d'exemple.

## Ce qui n'est pas installable aujourd'hui

- **Streamlit in Snowflake (SiS)** — aucun chemin d'installation n'existe
  dans ce dépôt. SiS n'apparaît que comme contexte de déploiement dans le
  modèle de menace, pas comme cible prise en charge.
- **SPCS** — même chose : périmètre du modèle de menace, pas une cible
  d'installation.
- **Native App** — aucun `manifest.yml` / `snowflake.yml` dans le dépôt ; il
  n'y a rien à installer comme Native App.
