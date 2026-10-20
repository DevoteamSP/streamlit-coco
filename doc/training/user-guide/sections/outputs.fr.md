# Sorties

Chaque fichier ou artefact que `streamlit-coco` ou ses exemples d'apps
produisent, ce qu'il contient, et où il atterrit.

## Fichiers téléversés

Produit par : `upload_to_cwd()`, `cwd_uploader()`, ou
`chat_input_bar(accept_file=...)` — voir
[Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html).

Atterrit à : `<CocoOptions.cwd>/_uploads/` (le nom du sous-répertoire est
configurable via `subdir`/`upload_subdir`).

Pour le lire : c'est une simple copie du fichier téléversé par
l'utilisateur, sous son nom original (validé) ; tout outil de l'agent
lisant depuis `cwd` peut le voir directement.

## Sortie de build App Builder

Produit par : l'action **Build this app** / **regenerate** de la page
Studio dans `examples/app_builder/`.

Atterrit à : `examples/app_builder/out/<slug>/`, contenant `brief.json` (le
brief structuré), `BRIEF.md` (le brief lisible par un humain, modifiable et
rechargeable dans l'éditeur CoCo), `sketches/` (les croquis téléversés le
cas échéant), et `streamlit_app.py` (l'app générée).

Pour le lire : `streamlit_app.py` est un script Streamlit exécutable ;
`BRIEF.md` est la source de vérité de ce qui a été demandé, et c'est ce que
**Save & regenerate** écrit avant de mettre en file d'attente un nouveau
tour CoCo.

## Artefacts intermédiaires de BI → Semantic

Produit par : les écrans 2 à 5 de `examples/bi_to_semantic/`.

Atterrit à : `examples/bi_to_semantic/out/`, contenant `estate_map.json`
(écran 2), `kpi_inventory.json` (écran 3), `access_rules.json` (écran 4),
et `decisions.json` (le registre d'arbitrage de l'écran 5).

Pour le lire : chaque fichier correspond à son JSON Schema sous
`examples/bi_to_semantic/contracts/` (`estate_map.schema.json`,
`kpi_inventory.schema.json`, `access_rules.schema.json`) ; `decisions.json`
enregistre ce que le relecteur a choisi à chaque point d'arbitrage de
l'écran 5.

## Sortie générée de BI → Semantic

Produit par : l'écran 6 (Generate) de `examples/bi_to_semantic/`, après
l'approbation Write.

Atterrit à : `examples/bi_to_semantic/out/streamlit_dash/` (le consommateur
déterministe) et `examples/bi_to_semantic/out/streamlit_dash_coco/` (le
consommateur rédigé par CoCo), ainsi que le SQL/YAML de la vue sémantique
générée et la politique d'accès par ligne.

Pour le lire : les deux répertoires consommateurs sont des apps Streamlit
exécutables, prévisualisées via `app_viewer()` sur les ports 8511
(déterministe) et 8512 (rédigé par CoCo). Les fichiers de vue sémantique et
de politique d'accès par ligne sont le SQL/YAML à relire avant de les
appliquer à un compte Snowflake.

## Écritures du Copilot Backlog Desk

Produit par : les skills Edit/Write du Copilot Backlog Desk (Draft release
notes, Propose ticket update), toutes deux soumises à approbation.

Atterrit à : `examples/backlog_desk/data/tickets/` (JSON de tickets mis à
jour) et `examples/backlog_desk/data/releases/` (notes de version en
Markdown).

Pour le lire : le JSON de tickets suit la même forme que celle déjà lue par
les pages Board/Epic/Ticket ; les notes de version sont du Markdown brut.

## Fichiers du processus enfant `app_viewer()`

Produit par : tout appel à `app_viewer(app_dir, ...)`.

Atterrit à : à l'intérieur de l'`app_dir` prévisualisé lui-même —
`.preview.log`, `.preview.pid`, `.preview.port`.

Pour le lire : `.preview.log` est la sortie stdout/stderr du processus
Streamlit enfant, utilisée par la fonction de suivi de log du flux « Fix
with CoCo » ; `.preview.pid` et `.preview.port` identifient le processus
enfant en cours d'exécution. Il n'y a qu'un seul aperçu par `app_dir` à la
fois — ne pointez jamais `app_dir` vers l'app qui héberge le viewer
lui-même.

## Artefacts de build de release

Produit par : `make build` (destiné aux mainteneurs, voir la
[Référence des commandes](reference-commands.html)).

Atterrit à : `dist/` — un sdist et un wheel.

Pour le lire : ce sont les fichiers que `make publish` envoie vers PyPI ;
non produits par un usage normal de la bibliothèque.
