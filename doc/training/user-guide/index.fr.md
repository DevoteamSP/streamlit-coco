# Guide utilisateur — streamlit-coco

Ce guide décrit streamlit-coco 0.1.9.

Il documente le produit tel qu'il est construit : comment l'utiliser, ce que
fait chaque partie de son API publique, et ce que produit chaque écran ou
commande. Ce n'est pas un tutoriel — pour une première prise en main guidée,
voir Enablement [`guided-tour.html`](../enablement/guided-tour.html) et
[`hands-on.html`](../enablement/hands-on.html).

## À qui s'adresse ce guide

À toute personne qui écrit du Python contre `streamlit-coco` : intégrer un
panneau ou un rail Copilot dans une app Streamlit, exécuter ou adapter une
des exemples d'apps, ou appeler l'API headless depuis un script. Il suppose
une connaissance pratique de Python et des bases de Streamlit ; il ne
suppose aucune exposition préalable au Cortex Code Agent SDK.

## Parcours de lecture

**Construire une app.** Lisez [Concepts](sections/concepts.html), puis
[Prise en main](sections/getting-started.html), puis
[Je veux construire une app CoCo minimale](sections/task-build-a-minimal-app.html).
Gardez la [Référence API](sections/reference-api.html) ouverte pendant que vous codez.

**Évaluer le produit.** Lisez [Concepts](sections/concepts.html), puis
[Je veux exécuter les exemples d'apps](sections/task-run-the-example-apps.html) et
[Référence des exemples d'apps](sections/reference-examples.html). Consultez la
[FAQ](sections/faq.html) pour les questions les plus posées par les évaluateurs.

**Étendre ou intégrer plus en profondeur.** Lisez la
[Référence API](sections/reference-api.html) et la
[Référence des commandes](sections/reference-commands.html) de bout en bout, puis les
pages de tâches pour [les approbations d'outils](sections/task-configure-tool-approvals.html),
[les téléversements de fichiers](sections/task-add-file-uploads.html),
[la sortie structurée](sections/task-use-structured-output.html) et
[l'usage headless](sections/task-run-headless.html). Le Guide Technique
`architecture.html` et `extending.html` couvrent ce qui se trouve derrière cette API.

## Sommaire

### Démarrage
- [Concepts](sections/concepts.html)
- [Prise en main](sections/getting-started.html)

### Tâches
- [Je veux construire une app CoCo minimale](sections/task-build-a-minimal-app.html)
- [Je veux exécuter les exemples d'apps](sections/task-run-the-example-apps.html)
- [Je veux configurer les approbations d'outils](sections/task-configure-tool-approvals.html)
- [Je veux ajouter des téléversements de fichiers](sections/task-add-file-uploads.html)
- [Je veux utiliser la sortie structurée](sections/task-use-structured-output.html)
- [Je veux exécuter CoCo en headless](sections/task-run-headless.html)

### Référence
- [Référence API](sections/reference-api.html)
- [Référence des commandes](sections/reference-commands.html)
- [Référence des exemples d'apps](sections/reference-examples.html)
- [Sorties](sections/outputs.html)

### Réponses
- [FAQ](sections/faq.html)

## Non couvert

- **Module Skills** — il n'y a pas de couche d'orchestration
  `.cortex/skills/*/SKILL.md` à la racine du dépôt. Les fichiers propres
  `types/<id>/SKILL.md` de l'exemple App Builder sont des skills de
  directives CoCo internes à l'exemple, documentées dans la
  [Référence des exemples d'apps](sections/reference-examples.html) → App Builder,
  pas comme un chapitre de référence des skills séparé.
- **Objets Snowflake** — cette bibliothèque ne crée ni ne possède aucun DDL
  Snowflake. L'exécution SQL passe uniquement par l'outil SQL propre de
  l'agent, soumis à approbation, avec ce que le rôle connecté peut déjà faire.
- **Native App** — le dépôt n'a pas de `manifest.yml` ni de `snowflake.yml`.
  Le packaging Native App n'est pas livré.
- **Modes de déploiement au-delà du local** — une seule cible est livrée
  aujourd'hui : local (Streamlit, la CLI CoCo et la configuration Snowflake
  sur la même machine). Streamlit in Snowflake et SPCS ne sont évoqués que
  comme périmètre du modèle de menace dans le Guide Technique ; ils ne sont
  pas implémentés.
- **Catalogue de contrôles** — il n'y a pas de couche de fichiers de règles
  ni de grille de notation dans ce dépôt.
- **Infrastructure as code** — il n'y a pas de Terraform dans ce dépôt.
- **Écrans des exemples d'apps, page par page** — les trois exemples d'apps
  ont chacun leurs propres écrans, mais ce guide couvre chaque app comme une
  seule entrée de référence dans la
  [Référence des exemples d'apps](sections/reference-examples.html) plutôt
  qu'une entrée par page Streamlit. Chaque exemple embarque son propre
  README avec une visite guidée page par page ; dupliquer cela ici finirait
  par diverger.
