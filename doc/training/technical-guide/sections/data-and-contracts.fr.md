# Données et contrats

## `CocoEvent`

`streamlit_coco/messages.py` définit `CocoEvent`, l'événement normalisé et
sérialisable en JSON que la bibliothèque produit à partir des messages
SDK/NDJSON. Chaque événement porte `to_dict()` / `CocoEvent.from_dict()`
pour l'aller-retour.

Champs :

| Champ | Type | Notes |
|---|---|---|
| `type` | `str` | `assistant_text`, `stream_event`, `thinking`, `tool_use`, `tool_result`, `permission_request`, `result`, `system`, `error` |
| `id` | `str` | UUID, généré par événement |
| `text` | `str \| None` | Texte assistant/réflexion |
| `delta` | `str \| None` | Texte delta de streaming |
| `name` | `str \| None` | Nom de l'outil (sur les événements tool-use) |
| `tool_use_id` | `str \| None` | Corrèle un résultat d'outil à son événement tool-use |
| `input` | `dict \| None` | Entrée de l'outil |
| `content` | `Any` | Charge utile de contenu brute |
| `is_error` | `bool \| None` | Drapeau d'erreur du résultat d'outil |
| `request_id` | `str \| None` | Identifiant de requête de permission |
| `tool_name` | `str \| None` | Nom de l'outil sur les événements de requête de permission |
| `tool_input` | `dict \| None` | Entrée de l'outil sur les événements de requête de permission |
| `subtype` | `str \| None` | Sous-type d'événement |
| `duration_ms` | `int \| None` | Durée du tour/de l'outil, quand le SDK la fournit |
| `structured_output` | `Any` | Charge utile de sortie structurée, quand présente |
| `cost_usd` | `float \| None` | Coût, quand le SDK le fournit |
| `message` | `str \| None` | Message en texte libre (événements system/error) |
| `code` | `str \| None` | Code d'erreur |
| `metadata` | `dict` | Champs supplémentaires libres |

`events_to_dataframe(events)` (nécessite `pandas`) aplatit une liste de
`CocoEvent` en un `DataFrame` pour inspection ou journalisation.

## Contrats JSON Schema — `examples/bi_to_semantic/contracts/`

Trois fichiers JSON Schema contraignent les sorties structurées que
l'exemple BI → Semantic demande à CoCo (et à ses propres parseurs
déterministes) de produire. Chacun est un schéma draft 2020-12 avec
`additionalProperties: false` :

| Fichier | Objet |
|---|---|
| `estate_map.schema.json` | Forme de `estate_map.json` — tables, colonnes, jointures, et usage par classeur découvert depuis l'estate Tableau/Power BI |
| `kpi_inventory.schema.json` | Forme de `kpi_inventory.json` — noms de métriques, les classeurs qui les définissent, leurs définitions, un drapeau de conflit, et une description en langage clair |
| `access_rules.schema.json` | Forme de `access_rules.json` — branches et divergences de règles d'accès par classeur, en langage clair |

Ces fichiers ne sont pas reproduits ici ; lisez-les directement sous
`examples/bi_to_semantic/contracts/` lorsque vous construisez contre la
forme qu'ils imposent. Comme ils portent une URI de draft `$schema`, ce
sont exactement le genre de fichier de contrat qui fait trébucher
[help.html#schema-dollar-schema-rejected](../help.html#schema-dollar-schema-rejected)
s'ils sont passés tels quels à `CocoOptions.output_schema` — la
bibliothèque retire `$schema` / `$id` avant de transmettre au SDK, donc
passer ces fichiers tels quels via `CocoOptions.output_schema` est sûr ;
seul un appelant qui réimplémente ce retrait doit faire attention.

## `brief.json` / `BRIEF.md` d'App Builder

Chaque projet App Builder sous `examples/app_builder/out/<slug>/` porte :

- `brief.json` — le brief lisible par machine : identifiant de type,
  contexte saisi par le propriétaire, les questions déclarées du type et
  leurs réponses.
- `BRIEF.md` — le même brief rendu en Markdown, le formulaire que CoCo lit
  (monté via `add_dirs`) en écrivant ou régénérant l'application. Les
  actions **Save** et **Save & regenerate** de la page Studio écrivent
  `BRIEF.md` à partir de l'état actuel du formulaire avant de mettre CoCo
  en file d'attente — voir
  [help.html#app-builder-brief-overwrite-race](../help.html#app-builder-brief-overwrite-race)
  pour le bug d'ordonnancement corrigé par cela en `0.1.8`.
- `sketches/` — images d'esquisse jointes en option au brief.
- `streamlit_app.py` — l'application consommatrice générée (ou l'ébauche de
  démo), une fois construite.

Il n'y a pas de fichier JSON Schema pour `brief.json` dans le dépôt ; sa
forme est définie implicitement par la liste `brief.questions` de
`types/<id>/type.json` plus les champs de premier niveau fixes que le
moteur App Builder écrit (`examples/app_builder/engine/paths.py` localise
ces fichiers sous `OUT_DIR = examples/app_builder/out/`).

## Contrat du sous-répertoire de téléversement (`_uploads/`)

`upload_to_cwd()` (`streamlit_coco/upload.py`) écrit les téléversements
navigateur sous `<CocoOptions.cwd>/_uploads/` par défaut
(`DEFAULT_UPLOAD_SUBDIR = "_uploads"`). Le contrat qu'il applique à chaque
écriture :

- Les noms de fichiers sont assainis en un simple basename
  (`sanitize_upload_name`) — les séparateurs de chemin et les caractères
  dangereux sont retirés ; `.`/`..` et les noms vides sont rejetés.
- Le répertoire de destination est résolu et vérifié comme étant à
  l'intérieur de `cwd` (`subdir` doit être relatif et ne doit pas contenir
  `..`).
- Liste d'autorisation d'extensions : `DEFAULT_ALLOWED_EXTENSIONS`, un
  frozenset fixe d'extensions de document/données sûres (voir la constante
  dans `streamlit_coco/upload.py` pour la liste exacte) — rejette tout ce
  qui est en dehors sauf si un appelant fournit son propre
  `allowed_extensions`.
- Limite de taille : `DEFAULT_MAX_BYTES = 10 * 1024 * 1024` (10 Mio) sauf
  si un appelant surcharge `max_bytes`.
- La politique d'écrasement est explicite par appel : `"error"` (défaut
  pour `upload_to_cwd` — lève `CwdUploadError` si le fichier existe),
  `"replace"` (défaut pour `upload_overwrite` de `chat_input_bar`), ou
  `"skip"`.

Chaque écriture réussie renvoie un `UploadedPath` (`path`, `relative`,
`name`, `bytes_written`, `overwritten`, `skipped`).

## Versionnage

Il n'existe pas de schéma de versionnage séparé pour `CocoEvent`, les JSON
Schema BI → Semantic, ou la forme du brief App Builder. Tous versionnent
avec le package : le champ `version` de `pyproject.toml` et
`CHANGELOG.md` sont les seuls registres de quand la forme d'un contrat a
changé (voir les entrées `Fixed` de `0.1.6` et `0.1.8` dans
[help](../help.html) pour des exemples de corrections liées à des
contrats). Un changement cassant sur l'une de ces formes est un événement
de version du package, pas un schéma versionné indépendamment.
