# Exercices pratiques

6 exercices progressifs utilisant les véritables applications de
`examples/`. Terminez la [checklist de configuration](setup.html) et la
[visite guidée](guided-tour.html) d'abord. Budget total : ~120–150 minutes.

---

## Exercice 1 — Exécuter le pattern préféré (`panel()` + `chat_input_bar()`)

**Objectif** : Voir le pattern d'intégration recommandé de bout en bout et
comprendre la répartition des responsabilités (« vous possédez la page,
CoCo possède la session »).

**Étapes** :

1. `make chat` (exécute `examples/chat_app.py`).
2. Ouvrez `examples/chat_app.py` dans un éditeur. Identifiez les quatre
   appels qui composent le pattern : `check_environment()`,
   `render_start_gate()`, `get_or_create_session()`, `panel()` +
   `chat_input_bar()`.
3. Dans le navigateur, tapez : *« What tables are available in
   SNOWFLAKE_SAMPLE_DATA.TPCH_SF1? »*
4. Observez le streaming de l'historique de conversation, et notez la carte
   d'outil qui apparaît (probablement une carte SQL ou Glob).

**Résultat attendu** : Une réponse en streaming se rend progressivement
(pas d'un seul coup), avec au moins une carte d'outil montrant ce que
l'agent a fait.

**Dépannage** : Si rien ne s'affiche en streaming, confirmez que
`check_environment(...).ready` était `True` dans la checklist de
configuration — une session bloquée signifie généralement que la CLI ou la
connexion n'est pas correcte. Voir
[`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting).

---

## Exercice 2 — Déclencher et résoudre une porte d'approbation

**Objectif** : Comprendre le modèle de sécurité de supervision humaine
(human-in-the-loop) — le différenciateur central de cette bibliothèque par
rapport à une intégration d'agent nue.

**Étapes** :

1. Toujours dans `make chat`, tapez : *« Show me the top 5 customers by
   total order amount. Write the SQL and run it. »*
2. Quand la bannière d'approbation apparaît, lisez l'instruction SQL
   complète affichée.
3. Cliquez sur **Approve once** — confirmez que la requête s'exécute et que
   les résultats apparaissent dans l'historique de conversation.
4. Tapez : *« Now create a summary table called TOP_CUSTOMERS in my
   schema. »*
5. Quand la porte d'approbation se déclenche à nouveau, cliquez sur
   **Deny** avec une raison (par ex. « not for this exercise ») —
   confirmez que l'agent reconnaît le refus.

**Résultat attendu** : L'exécution SQL se met en pause pour approbation les
deux fois ; approuver la laisse s'exécuter, refuser l'arrête et l'agent
adapte sa réponse suivante.

**Dépannage** : Si aucune porte d'approbation n'apparaît pour un `CREATE
TABLE`, vérifiez que `require_approval_for=["Edit", "Write", "Bash"]` (ou
similaire) est défini dans `CocoOptions` — ouvrez `examples/chat_app.py` et
confirmez les pastilles **Requires approval** de la barre latérale.

---

## Exercice 3 — Sortie structurée vers un widget

**Objectif** : Voir comment la sortie de l'agent peut alimenter vos propres
widgets Streamlit au lieu de simplement s'afficher comme texte de chat.

**Étapes** :

1. Arrêtez la démo précédente (Ctrl+C) et lancez `make structured`
   (`examples/structured_output.py`).
2. Ouvrez le fichier et trouvez la définition de `output_schema` et le
   callback `on_structured_output` passé à `panel()`.
3. Dans le navigateur, tapez : *« Give me a breakdown of orders by
   status. »*
4. Confirmez que la réponse se rend comme un graphique/dataframe
   Streamlit, et non comme du texte JSON brut.

**Résultat attendu** : La réponse structurée de l'agent est routée vers un
widget que vous avez défini, sans parsing JSON manuel dans le code de votre
application.

**Dépannage** : Si elle s'affiche comme du texte brut au lieu d'un widget,
la réponse ne correspond peut-être pas à `output_schema` — essayez de
reformuler le prompt pour être plus explicite sur les champs souhaités.
Voir
[`help.html#structured-output-not-rendering`](../technical-guide/help.html#structured-output-not-rendering).

---

## Exercice 4 — Mode headless (sans interface Streamlit)

**Objectif** : Confirmer que la même bibliothèque fonctionne en dehors de
Streamlit — pour la CI, les scripts et les jobs par lots.

**Étapes** :

1. Lancez `make headless` (`examples/headless_pipeline.py`).
2. Ouvrez le fichier et notez : aucun import `streamlit` nulle part, la
   même fonction `query()` utilisée pour le flux d'événements asynchrone.
3. Observez la sortie du terminal — les événements s'affichent en
   streaming pendant que l'agent travaille, avec les mêmes types
   d'événements (`assistant_text`, `tool_use`, `result`) qu'en mode UI.

**Résultat attendu** : Le script s'exécute jusqu'au bout, en affichant les
événements en streaming entièrement depuis le terminal — aucun navigateur
impliqué.

**Dépannage** : S'il se bloque, vérifiez les mêmes prérequis
d'environnement que l'exercice 1 (`check_environment`) — le mode headless a
exactement la même dépendance CLI/connexion.

---

## Exercice 5 — Construire une application minimale à partir de zéro

**Objectif** : Prouver que vous pouvez reproduire le pattern sans copier un
exemple existant — le véritable test du « formé ». C'est une situation
réelle, pas un exercice mécanique : vous rencontrerez au moins l'une des
deux erreurs de permissions d'outils que les gens font réellement avec
`CocoOptions`.

**Étapes** :

1. Créez un nouveau fichier `my_first_app.py` à la racine du dépôt.
2. En utilisant le [quickstart du README](../../../README.md#quickstart)
   comme seule référence (ne copiez pas directement `examples/chat_app.py`),
   écrivez une application qui :
   - Utilise `connection="analytics"` (ou le nom de votre connexion
     configurée)
   - Définit `allowed_tools=["Read", "Glob", "Grep"]`
   - Définit `require_approval_for=["Edit", "Write", "Bash"]`
   - Affiche la porte de démarrage, puis `panel()` + `chat_input_bar()`
3. Exécutez-la : `uv run streamlit run my_first_app.py`
4. Demandez-lui de lire un fichier du dépôt (par ex. *« Read the README and
   summarize it in 3 bullets »*) et confirmez qu'elle s'exécute sans
   requérir d'approbation (`Read` est dans `allowed_tools`).
5. Demandez-lui d'écrire un nouveau fichier — confirmez que la porte
   d'approbation se déclenche cette fois.

**Résultat attendu** : Une application fonctionnelle construite à partir du
README seul, distinguant correctement les outils à exécution automatique
des outils soumis à approbation.

**Dépannage** : Si `Read` demande quand même une approbation, vérifiez que
vous ne l'avez pas aussi listé dans `require_approval_for` —
`allowed_tools` et `require_approval_for` ne devraient pas se chevaucher
pour un même outil.

**Supprimez `my_first_app.py` une fois terminé** — c'est un artefact de
formation jetable, qui ne fait pas partie du dépôt.

---

## Exercice 6 — Rail Copilot dans une application produit

**Objectif** : Voir `copilot_rail()` comme un Copilot en rail latéral, pas
un chat plein écran, et utiliser ses contrôles Display config pour garder
un historique de conversation en direct lisible.

**Étapes** :

1. `make bi-semantic` (`examples/bi_to_semantic/`).
2. Chargez le MIT Tableau Server pack sur l'écran 1 (aucun entrepôt
   requis).
3. Connectez Copilot à droite. Notez le popover **Connection** et, à côté,
   le popover **Display config** en icône seule
   (`:material/display_settings:`). Ouvrez-le : deux curseurs, **Last
   messages** (par défaut 8) et **First n characters** (par défaut 200),
   chacun activé par une pastille. Déplacez chaque curseur et confirmez que
   l'historique de conversation se met à jour en direct pendant que le
   popover reste ouvert.
4. Mettez en file d'attente une règle d'accès ou un job de génération et
   observez le badge compact **Working · thinking…** sur la ligne de
   titre — pas une grande carte de statut. **Cancel job** se trouve sur
   cette même ligne, à côté de **Close**.

**Résultat attendu** : CoCo vit dans le rail ; l'application possède la
colonne de gauche. L'historique de conversation reste compact quelle que
soit la durée de la conversation, grâce aux curseurs Display config, et non
à cause d'une troncature fixe. Même primitive sous-jacente (`panel()`) que
`make backlog`.

**Dépannage** : Si le popover Display config est absent, confirmez que
votre checkout est au moins en `0.1.8` (`uv run python -c "import
streamlit_coco as c; print(c.__version__)"`) — le popover est apparu dans
la `0.1.8` ; le sélecteur **Config file** de la connexion est apparu dans
la `0.1.9`. Le `pyproject.toml` de l'exemple épingle (path-pin) la
bibliothèque à ce checkout du dépôt.

---

## Conclusion

Vous avez maintenant exécuté chaque mode d'interaction principal : panneau
interactif, portes d'approbation, sortie structurée, headless, une
construction à partir de zéro, et un rail Copilot intégré dans une
application produit. Suite : lisez [`demo-guide.md`](demo-guide.html) et
faites une répétition chronométrée.
