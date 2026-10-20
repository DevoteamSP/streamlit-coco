# FAQ

## Comment installer streamlit-coco ?

`pip install streamlit-coco[sdk]`. Les étapes complètes, les prérequis et
la vérification sont dans Enablement [`setup.html`](../../enablement/setup.html).

## Est-ce prêt pour la production ?

Non — la version que décrit ce guide est alpha (voir l'[index](../index.html)
pour savoir laquelle).

## Faut-il une connexion Snowflake ?

Pour toute fonctionnalité adossée à CoCo, oui — l'agent s'exécute via la
CLI/le SDK Cortex Code contre une connexion Snowflake configurée. Certains
écrans d'exemples d'apps fonctionnent sans : les écrans estate-map et
KPI-inventory de BI → Semantic parsent les classeurs de façon
déterministe, et le consommateur Streamlit déterministe qu'il génère ne
nécessite aucun entrepôt pour être consulté.

## Quel LLM utilise-t-il ?

Quel que soit le modèle que Cortex Code fait tourner en interne. Aucune
configuration de modèle n'est requise au-delà de `CocoOptions.model`
(laissez-le à `None`, ou définissez-le à `"auto"`).

## Puis-je personnaliser quels outils nécessitent une approbation ?

Oui — `CocoOptions.allowed_tools` et `CocoOptions.require_approval_for`.
`AskUserQuestion` et `ExitPlanMode` nécessitent toujours une approbation
quel que soit l'un ou l'autre réglage. Voir
[Je veux configurer les approbations d'outils](task-configure-tool-approvals.html).

## Que se passe-t-il si je refuse une approbation ?

L'appel d'outil ne s'exécute pas. Le tour de l'agent continue à partir de
là, optionnellement avec la raison passée à `deny_pending()`.

## Existe-t-il un journal persisté des décisions d'approbation ?

Non — les décisions d'approbation, y compris « Always allow », sont
conservées uniquement dans la session et ne sont pas écrites dans un
journal d'audit persisté.

## En quoi est-ce différent d'utiliser la CLI CoCo directement ?

La bibliothèque ajoute la plomberie spécifique à Streamlit que la CLI ne
fournit pas par elle-même : un état de session résistant aux reruns, un
rendu en streaming, des cartes d'outils, et l'interface d'approbation.

## Le téléversement de fichiers fonctionne-t-il ?

Oui — `upload_to_cwd()` / `cwd_uploader()` /
`chat_input_bar(accept_file=...)` écrivent dans le `cwd` de l'agent. Voir
[Je veux ajouter des téléversements de fichiers](task-add-file-uploads.html).

## Qu'est-ce que `copilot_rail()` ?

Un Copilot en rail à droite construit autour de `panel()`, pour intégrer
CoCo à l'intérieur d'une app multipage plus large plutôt que comme un chat
en pleine page. Voir les entrées Backlog Desk et BI → Semantic dans la
[Référence des exemples d'apps](reference-examples.html).

## Fonctionne-t-il avec Streamlit in Snowflake (SiS) ou SPCS ?

Pas aujourd'hui. Local — Streamlit, la CLI CoCo et la configuration
Snowflake sur la même machine — est la seule cible de déploiement que
livre cette version.

## Comment voir les charges utiles brutes de requête/réponse des outils ?

Définissez `STREAMLIT_COCO_DEBUG=1` ou `COCO_DEBUG=1` (ou
`st.session_state["coco_debug"] = True`). Si les charges utiles ne
s'affichent toujours pas, voir
[`help.html#debug-mode-not-showing-payloads`](../../technical-guide/help.html#debug-mode-not-showing-payloads).

## La session affiche « Starting CoCo… » et ne se connecte jamais — que vérifier ?

Voir
[`help.html#session-stuck-connecting`](../../technical-guide/help.html#session-stuck-connecting)
et, si la connexion elle-même est le problème,
[`help.html#coco-connection-error`](../../technical-guide/help.html#coco-connection-error) /
[`help.html#snowflake-config-not-found`](../../technical-guide/help.html#snowflake-config-not-found).

## `make audit` échoue juste après avoir monté la version dans `pyproject.toml` — est-ce réel ?

Généralement non — voir
[`help.html#pip-audit-editable-false-positive`](../../technical-guide/help.html#pip-audit-editable-false-positive).

## La page Studio d'App Builder semble écraser mes modifications de brief sur Save & regenerate

Voir
[`help.html#app-builder-brief-overwrite-race`](../../technical-guide/help.html#app-builder-brief-overwrite-race).

## Où trouver la liste actuelle des lacunes connues pour cet asset ?

`dsp-assets/audits/streamlit-coco/` contient le dernier rapport de lacunes ;
ce guide ne répète pas son contenu puisqu'il change entre les releases.
