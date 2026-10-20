# Je veux utiliser la sortie structurée

**Pour** un développeur rendant la sortie de l'agent dans un widget plutôt qu'en texte de chat · **15 min** · **une app minimale fonctionnelle**

Vous obtenez une session qui retourne du JSON conforme à un schéma que vous
définissez, routé vers votre propre widget au lieu de l'historique de
conversation.

## Avant de commencer

- Une app minimale fonctionnelle ([Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)).
- Un JSON Schema décrivant la forme que vous voulez récupérer. N'incluez pas
  les clés `$schema` ou `$id` — la bibliothèque les retire avant de
  transmettre le schéma au SDK, mais un schéma rédigé ailleurs (par exemple
  un fichier de contrat partagé) peut encore les porter.

## Étapes

1. Définissez `output_schema` sur `CocoOptions` :

   ```python
   options = st_coco.CocoOptions(
       connection="my_connection",
       output_schema={
           "type": "object",
           "properties": {
               "status": {"type": "string"},
               "count": {"type": "integer"},
           },
           "required": ["status", "count"],
       },
   )
   ```

2. Traitez la charge utile structurée à son arrivée, soit avec un callback,
   soit en la relisant après le tour :

   ```python
   def on_structured(payload: dict, result: st_coco.CocoChatResult) -> None:
       st.metric("Count", payload["count"])

   st_coco.panel(session, on_structured_output=on_structured)
   ```

   Ou lisez `session.structured_output` /
   `session.chat_result().structured_output` une fois le tour terminé, sans
   callback.

3. Optionnellement, donnez au rendu structuré son propre conteneur au lieu
   de le laisser apparaître en ligne dans l'historique de conversation :

   ```python
   box = st.container()
   st_coco.panel(session, structured_output_container=box)
   ```

4. Pour un appel headless ponctuel, passez `output_schema` directement à
   `query()` plutôt que via `CocoOptions` — voir
   [Je veux exécuter CoCo en headless](task-run-headless.html).

## Résultat

Quand le résultat final de l'agent porte une charge utile structurée,
`panel()` (ou votre callback `on_structured_output`) la reçoit sous forme de
`dict` Python conforme à votre schéma, et
`session.chat_result().structured_output` contient la même valeur. Si le
tour ne produit aucune charge utile structurée, ces valeurs restent `None`
— l'historique de conversation affiche quand même la réponse en texte brut.

## Variations

- `structured_output.py` démontre le flux complet — exécutez-le avec
  `make structured` (voir
  [Référence des exemples d'apps](reference-examples.html)).
- `request_input(question, schema=...)` est un mécanisme différent : il
  recueille une réponse structurée de l'*utilisateur* entre deux tours, pas
  de l'agent — voir [Référence API](reference-api.html).

## En cas d'échec

- [`no schema with key or ref "https://json-schema.org/draft/2020-12/schema"`](../../technical-guide/help.html#schema-dollar-schema-rejected)
- [La sortie structurée ne s'affiche pas](../../technical-guide/help.html#structured-output-not-rendering)
