# Introduction

## Ce qu'est streamlit-coco

`streamlit-coco` est une bibliothèque Python/Streamlit qui intègre le SDK
Cortex Code Agent de Snowflake (« CoCo ») dans une application Streamlit : un
Copilot en rail latéral ou en panneau complet, des portes d'approbation
supervisées par un humain (human-in-the-loop) pour les outils destructifs, un
aperçu en direct d'une application que CoCo vient d'écrire, une sortie
structurée vers vos propres widgets, et une API headless `query()` /
`CocoSession` pour les scripts et la CI.

Paquet PyPI : `streamlit-coco`. Version actuelle : **0.1.9** (alpha — l'API
peut encore évoluer). Python 3.10+, Streamlit 1.55+. Licence : Apache-2.0.

## Le problème qu'elle résout

Câbler le SDK CoCo dans une application Streamlit à la main signifie
construire, à partir de zéro : un état de session qui survit aux reruns
Streamlit, un rendu en streaming de l'historique de conversation de l'agent,
des cartes d'outils lisibles plutôt que des dumps JSON bruts, et un flux
d'approbation pour tout ce que l'agent pourrait écrire, modifier ou exécuter.
`streamlit-coco` fournit cette plomberie sous forme d'un ensemble de
fonctions composables (`panel()`, `chat_input_bar()`, `copilot_rail()`,
`render_approvals()`, …) afin qu'un auteur d'application écrive la page et
les options, pas le pont de session.

## À qui ça s'adresse

Aux consultants et ingénieurs qui doivent ajouter un Copilot basé sur CoCo à
une application Streamlit sur un compte Snowflake avec accès à Cortex Code.
Cela suppose des bases en Python et une familiarité suffisante avec
Streamlit pour lire du code `st.container` / `st.session_state` — la
bibliothèque masque l'essentiel de la plomberie de gestion de session, donc
une expertise Streamlit approfondie n'est pas requise.

## Objectifs pédagogiques

À l'issue de ce parcours, vous serez capable de :

1. Expliquer ce que fait `streamlit-coco`, et quand l'utiliser plutôt que la
   CLI CoCo ou le SDK directement (voir la section « When not to use » du
   README).
2. Installer la bibliothèque, la connecter à un compte Snowflake, et
   exécuter chaque application d'exemple fournie (`make chat`, `make
   backlog`, `make bi-semantic`, `make headless`, …).
3. Construire une application Streamlit selon le pattern préféré —
   `panel()` + `chat_input_bar()` — avec `require_approval_for` configuré
   pour que les outils destructifs se mettent en pause en attendant une
   décision humaine.
4. Configurer `CocoOptions` pour un workflow réel et intégrer
   `copilot_rail()` dans une application multipage existante.
5. Diagnostiquer une session qui échoue à se connecter ou un outil qui ne
   s'exécute pas, à l'aide de `check_environment()`, de
   `STREAMLIT_COCO_DEBUG`, et de la [référence d'aide](../technical-guide/help.html)
   du Guide technique.

## Estimation du temps

| Module | Temps |
| --- | --- |
| `intro.md` (cette page) | 10 min |
| [`setup.md`](setup.html) | 20–30 min |
| [`guided-tour.md`](guided-tour.html) | 20–30 min |
| [`hands-on.md`](hands-on.html) — 6 exercices | 120–150 min |
| [`demo-guide.md`](demo-guide.html) — lecture + une répétition | 30–40 min |
| **Total enablement** | **~3,5–4,5 heures** |

Les cas d'entraînement ([`01-simple`](../training/01-simple.html),
[`02-intermediate`](../training/02-intermediate.html),
[`03-advanced`](../training/03-advanced.html)) constituent un parcours
séparé, budgété respectivement à 20–30, 45–60 et 30–45 minutes.

## Prérequis

- Python 3.10+ et `uv` installés localement.
- Un compte Snowflake avec **accès à Cortex Code**, et un fichier
  `~/.snowflake/connections.toml` fonctionnel (l'ancien `config.toml`
  fonctionne aussi) — ou la connexion par défaut de la Snowflake CLI.
- La **CLI CoCo** (`cortex`) installée et accessible dans le `PATH`
  (vérifiez avec `cortex --version`), ou un chemin que vous pouvez définir
  via `CORTEX_CODE_CLI_PATH`.
- Un accès Git au dépôt de développement
  (`github.com/DevoteamSP/streamlit-coco-dev`) si vous prévoyez d'exécuter
  les exemples fournis, ou simplement `pip install "streamlit-coco[sdk]"` si
  vous n'avez besoin que du paquet publié.
- Rien de plus : aucun entrepôt (warehouse) Snowflake dédié n'est requis pour
  suivre ce parcours — les exemples utilisent par défaut des données
  d'exemple en lecture seule ou des fixtures déconnectées.
