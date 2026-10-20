# Cas 1 — Simple : le motif recommandé, guidé

**Niveau :** Simple — entièrement guidé, données d'exemple. **Durée :** 20–30 min.

## Contexte

Toute intégration de `streamlit-coco` part de la même structure : vous possédez
la page Streamlit, CoCo possède la session. `examples/chat_app.py` est la
référence fonctionnelle fournie pour cette structure — les quatre mêmes appels que le
[README quickstart](../../../README.md#quickstart) présente isolément :
`check_environment()`, `render_start_gate()`, `get_or_create_session()`, et
`panel()` + `chat_input_bar()`.

## Objectif

Lancez l'application de référence fournie, identifiez chacun des quatre appels dans le
code source, et exercez à la fois un tour en lecture seule et un tour soumis à
approbation — de façon à pouvoir pointer n'importe quelle ligne de `chat_app.py` et dire
ce qu'elle fait.

## Données

**Fournies.** Aucun objet Snowflake à créer : `SNOWFLAKE_SAMPLE_DATA`
(livré avec tout compte Snowflake ayant les données d'exemple activées), en particulier
le schéma `TPCH_SF1`, est en lecture seule et disponible par défaut. Un ensemble
de prompts sélectionnés est également fourni dans `examples/testdata/prompts.json`, consultable
depuis le bouton **Test prompts** (prompts de test) de la barre latérale dans `make chat`.

## Étapes

1. Vérifiez que votre environnement est prêt — la [checklist de configuration](../enablement/setup.html)
   doit être entièrement cochée avant de commencer.
2. Exécutez `make chat`. Cela lance `examples/chat_app.py`.
3. Ouvrez `examples/chat_app.py` dans un éditeur à côté de l'onglet du navigateur. Repérez
   et lisez, dans l'ordre :
   - `env = st_coco.check_environment(connection=connection)` — sonde le SDK, la
     CLI et la configuration Snowflake sans démarrer d'agent.
   - `st_coco.render_start_gate(opts, session_key=SESSION_KEY, gate_key=GATE_KEY, env=env)`
     — l'écran d'accueil ; renvoie `False` tant que vous n'avez pas cliqué sur **Start CoCo
     Chat**.
   - `session = st_coco.get_or_create_session(opts, key=SESSION_KEY)` — récupère
     ou crée le worker en arrière-plan, stocké dans `st.session_state`.
   - `st_coco.panel(session=session, ...)` suivi de
     `st_coco.chat_input_bar(session, ...)` — l'interface de l'historique de conversation/sortie et
     la zone de saisie.
4. Dans le navigateur, cliquez sur **Start CoCo Chat** si ce n'est pas déjà fait.
5. Saisissez : *"What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1?"*
   (« Quelles tables sont disponibles dans SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 ? »)
   Observez l'historique de conversation s'afficher progressivement plutôt que d'apparaître d'un coup,
   et notez la carte d'outil qui apparaît.
6. Saisissez : *"Create a summary table called TOP_CUSTOMERS in my schema."*
   (« Créez une table de synthèse appelée TOP_CUSTOMERS dans mon schéma. ») Une
   bannière d'approbation apparaît avec **Approve once** (approuver une fois), **Always allow**
   (toujours autoriser), **Deny** (refuser).
   Cliquez sur **Deny** en indiquant un motif — vérifiez que l'agent en prend acte et ne
   crée pas la table.

## Résultat attendu

- L'historique de conversation de l'étape 5 s'affiche progressivement, avec au moins une carte
  d'outil visible (généralement SQL ou Glob).
- L'historique de conversation de l'étape 6 marque une pause sur une bannière d'approbation avant qu'une table
  ne soit créée ; la refuser ne laisse aucun nouvel objet dans votre schéma.
- Vous pouvez citer, de mémoire, lequel des quatre appels dans `chat_app.py`
  a produit l'écran d'accueil, la session et le panneau.

## Où chercher en cas de blocage

- Si l'application ne quitte jamais l'écran d'accueil ou si l'historique de conversation ne commence
  jamais à s'afficher : [`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting)
  et [`help.html#coco-connection-error`](../technical-guide/help.html#coco-connection-error).
- Si aucune bannière d'approbation n'apparaît pour la requête `CREATE TABLE`, revérifiez
  `require_approval_for` dans les pastilles **Requires approval** (nécessite une approbation) de la
  barre latérale de `chat_app.py`, ou l'étape de vérification d'environnement de la checklist de
  configuration.
