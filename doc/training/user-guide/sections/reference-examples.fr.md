# Référence des exemples d'apps

Chaque exemple d'app maison sous `examples/`, ce qu'il démontre, comment
l'exécuter, et ce dont il a besoin. Voir la
[Référence des commandes](reference-commands.html) pour les cibles `make`
sous-jacentes et [Sorties](outputs.html) pour les fichiers que chacun
produit.

## `chat_app.py`

À exécuter avec `make chat`. Démontre le pattern d'intégration préféré :
`check_environment()` → `render_start_gate()` → `get_or_create_session()` →
`panel()` + `chat_input_bar()`. Sa barre latérale inclut un lanceur de
prompts de test adossé à `examples/testdata/prompts.json`. Nécessite une
connexion Snowflake avec accès Cortex Code.

## `approval_gate.py`

À exécuter avec `make approval`. Démontre le widget tout-en-un `chat()` CCv2
legacy au lieu de `panel()` — utile comme référence pour les apps encore sur
l'ancienne API. Nécessite une connexion Snowflake.

## `structured_output.py`

À exécuter avec `make structured`. Démontre `output_schema` avec
`on_structured_output`, routant le JSON de l'agent vers un widget au lieu du
texte de chat. Nécessite une connexion Snowflake.

## `headless_pipeline.py`

À exécuter avec `make headless`. Du Python asynchrone pur sans aucun import
Streamlit ; pilote `query()` et `CocoSession` depuis un terminal, chacun
dans sa propre boucle d'événements. Nécessite une connexion Snowflake ; ne
produit aucune interface navigateur.

## `cwd_upload_chat.py`

À exécuter avec `make cwd-upload`. Démontre `chat_input_bar(accept_file=...)`
et `cwd_uploader()` — des téléversements navigateur écrits dans le `cwd` de
l'agent. Nécessite une connexion Snowflake pour les tours de l'agent ; les
mécanismes de téléversement eux-mêmes n'en ont pas besoin.

## `backlog_desk/`

À exécuter avec `make backlog`. Un Product Backlog Desk multipage : adossé
à des fichiers/JSON (pas de SQL), avec des pages Board / Epic / Ticket /
Release et un Copilot en rail à droite ouvert depuis un bouton **Copilot**
d'en-tête ou un lien d'action (fermé avec **Close** — ce n'est pas une page
de navigation). Son Copilot embarque quatre skills basées sur des prompts
(pas des skills d'orchestration `.cortex/skills/`) : Summarize sprint, Draft
release notes (soumis à approbation), Propose ticket update (soumis à
approbation), Check definition of done. Les données vivent sous
`data/{epics,tickets,releases,policies}`. C'est l'exemple maison d'un rail
intégré dans un produit non-SQL, non-chat. Nécessite une connexion
Snowflake pour le Copilot ; les pages Board/Epic/Ticket/Release elles-mêmes
ne lisent que du JSON local.

## `bi_to_semantic/`

À exécuter avec `make bi-semantic` (alias : `make tableau-semantic`,
déprécié). Lit des classeurs Tableau (`.twb`/`.twbx`) et/ou Power BI
(`.pbix`/`.pbit`), fait apparaître les KPI et les divergences de règles
d'accès, arbitre les désaccords via `request_input(schema=...)`, et écrit
une vue sémantique, une politique d'accès par ligne, et une app
consommatrice Streamlit générée (déconnectée par défaut, aucun entrepôt
requis pour la consulter). Six écrans : Welcome, 1 Load, 2 Estate map
(parsing déterministe), 3 KPI inventory (déterministe), 4 Access-rule
comparator (Power BI parsé localement ; Tableau parsé via CoCo), 5
Arbitration (`request_input`), 6 Generate (approbation Write + aperçu). Les
écrans 2 et 3 ne nécessitent aucun agent CoCo ni entrepôt ; le chemin
Tableau de l'écran 4 et l'écran 6 en ont besoin. Des fixtures d'exemple (un
pack Tableau Server sous licence MIT et un pack Power BI Obvience) vivent
sous `examples/bi_samples/`. Le `cwd` de l'agent pour cet exemple est
`examples/workspaces/bi_to_semantic/` (ignoré par git). Aperçu : un
consommateur Python (déterministe) sur `127.0.0.1:8511` et un consommateur
rédigé par CoCo sur `:8512`, tous deux via `app_viewer()`. Les JSON Schemas
des artefacts intermédiaires vivent sous
`examples/bi_to_semantic/contracts/`. Voir [Sorties](outputs.html) pour les
noms de fichiers exacts.

## `app_builder/`

À exécuter avec `make app-builder`. Génération guidée d'apps Streamlit pour
les utilisateurs métier. Pages : Welcome, Library (cartes Resume et
Create-a-new-project, avec un filtre par pill de sujet), Brief (un brief en
texte libre et des croquis, ou des questions typées), Studio (Build this
app / regenerate ; Open Copilot ; Open Preview ; un expandeur App brief avec
Save / Save & regenerate), Admin (éditeurs CRUD de types et de skills de
directives). Chaque type d'app est un `types/<id>/type.json` (sa carte de
catalogue) plus un `types/<id>/SKILL.md` optionnel (avec `reference/` et
`CHECKLIST.md`) que CoCo lit via `add_dirs` ; `types/shared/SKILL.md`
contient les règles de génération communes à tous les types et n'est pas
lui-même une carte de catalogue. L'ensemble de types verrouillé et actif
est : KPI presentation, Data quality, Call transcription, Meeting recap,
Prompt library, CSV explorer — chacun déclare un `grounding_kind`
(`tabular` / `semantic_view` / `documents` / `urls`) qui décide si son étape
de profilage est un parseur pandas déterministe (`engine/profile.py`) ou un
job CoCo. Les documents et URLs sont récupérés par l'application hôte,
jamais par la session CoCo elle-même — aucun outil réseau ne lui est
accordé. La sortie générée atterrit sous
`examples/app_builder/out/<slug>/` (`brief.json`, `BRIEF.md`, `sketches/`,
`streamlit_app.py`) ; l'aperçu tourne sur le port 8513. Nécessite une
connexion Snowflake pour tout type utilisant une étape de profilage pilotée
par CoCo ou pour l'étape Build/regenerate de Studio.
