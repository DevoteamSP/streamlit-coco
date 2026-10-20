# Je veux exécuter CoCo en headless

**Pour** un développeur scriptant CoCo depuis un job CI ou un terminal · **15 min** · **un terminal, sans interface Streamlit**

Vous obtenez un script qui pilote l'agent sans importer Streamlit, que ce
soit pour un seul tour ou une session multi-tours, en résolvant toute
approbation dans le code.

## Avant de commencer

- `streamlit-coco[sdk]` installé ; `check_environment().ready` vaut `True`
  pour la connexion que vous allez utiliser (voir [Prise en main](getting-started.html)).
- Les symboles headless principaux (`CocoSession`, `query`, `CocoOptions`,
  les types de permission et d'erreur) s'importent sans charger Streamlit —
  les exports UI se résolvent paresseusement, donc un simple
  `import streamlit_coco` est sans risque dans un script qui ne touche
  jamais à Streamlit.

## Étapes

1. Pour un seul tour, utilisez `query()` :

   ```python
   import asyncio
   import streamlit_coco as st_coco

   async def main() -> None:
       options = st_coco.CocoOptions(connection="my_connection")
       async for event in st_coco.query("Summarize sales by region.", options=options):
           if event.type == "assistant_text":
               print(event.text)

   asyncio.run(main())
   ```

2. Pour une session multi-tours sans aucune interface, pilotez directement
   `CocoSession` :

   ```python
   session = st_coco.CocoSession(options=options, key="headless")
   session.start()
   await session.ensure_ready(timeout=120)
   result = await session.run("List the tables in my schema.")
   async for event in session.stream():
       ...
   session.close()
   ```

3. Résolvez les approbations dans le code plutôt que dans une interface —
   vérifiez `session.chat_result().pending_approval` après une exécution et
   appelez `approve_pending()` / `deny_pending()` comme montré dans
   [Je veux configurer les approbations d'outils](task-configure-tool-approvals.html),
   ou pré-approuvez tout ce que vous prévoyez via `allowed_tools` pour que
   le script ne se bloque jamais.

4. Convertissez les événements accumulés en tableau quand vous avez besoin
   de les inspecter ou de les journaliser en masse :

   ```python
   df = st_coco.events_to_dataframe(session.events)  # nécessite pandas
   ```

## Résultat

`query()` produit des objets `CocoEvent` pour un seul tour et ne retourne
rien d'autre — il n'y a pas d'objet session à conserver après coup.
`CocoSession` exécuté hors de Streamlit se comporte exactement comme dans
`panel()` : le même historique de conversation, les mêmes transitions de
`CocoRunStatus`, les mêmes pauses d'approbation — seul le rendu manque.

## Variations

- `examples/headless_pipeline.py` (`make headless`) montre à la fois
  `query()` et `CocoSession` depuis un simple script terminal, chacun dans
  sa propre boucle d'événements.
- `query()` lève `SDKNotInstalledError` ou `QueryError` (ou une autre
  sous-classe `CocoError`) au lieu de retourner un résultat partiel en cas
  d'échec — enveloppez l'appel en conséquence pour un job CI.

## En cas d'échec

- [`SDKNotInstalledError`](../../technical-guide/help.html#sdk-not-installed)
- [Session non prête](../../technical-guide/help.html#session-not-ready)
