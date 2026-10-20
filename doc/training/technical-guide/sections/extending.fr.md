# Étendre

Une section par point d'extension que le dépôt expose réellement.

## Rendu de texte enfichable (`text_renderer=`)

`panel()`, `render_transcript()`, et `render_output_field()`
(`streamlit_coco/ui.py`, `streamlit_coco/display.py`) acceptent
`text_renderer=` afin qu'une application puisse rendre le texte
assistant/utilisateur avec n'importe quelle API texte de Streamlit, ou un
callable personnalisé, au lieu du `st.markdown` codé en dur par défaut.

**Valeurs nommées :** `"markdown"` (défaut), `"write"`, `"text"`,
`"caption"`, `"code"` (accepte aussi les noms préfixés `st.*`). Passer un
nom inconnu lève une `ValueError` listant les noms connus.

**Forme callable :** passez n'importe quelle fonction de forme
`Callable[[str], None]` — elle est invoquée avec le texte du message.

**Fichiers à toucher :**
- `streamlit_coco/text_renderer.py` — la table de résolution nom →
  callable. Ajoutez une nouvelle valeur nommée ici si vous étendez
  l'ensemble intégré.
- Les points d'appel dans `streamlit_coco/ui.py` (`panel`) et
  `streamlit_coco/display.py` (`render_transcript`, `render_output_field`)
  font déjà transiter `text_renderer` ; un nouveau rendu n'a besoin d'être
  enregistré qu'une seule fois.

**Étape de régénération/vérification :** lancez `examples/chat_app.py`
(`make chat`) avec le nouveau rendu passé explicitement et confirmez que le
texte assistant/utilisateur se rend comme attendu ; aucune étape de build
n'est nécessaire puisque c'est du Python pur.

**Tests à ajouter :** étendez
`doc/features/text-renderer/test-checklist.md` avec la nouvelle valeur
nommée, et ajoutez un cas au fichier de test unitaire pertinent couvrant la
résolution de rendu (il n'y a pas de `test_text_renderer.py` dédié dans
l'arborescence actuelle — vérifiez `tests/` pour la couverture existante
la plus proche avant d'ajouter un nouveau fichier).

## Dispatch par famille d'outil / nom d'outil

`streamlit_coco/tool_names.py` associe un nom d'outil brut à une
énumération `ToolFamily` (`ASK_USER`, `SQL`, `READ`, `WRITE`, `EDIT`,
`BASH`, `GLOB`, `GREP`, `EXIT_PLAN`, `GENERIC`) via `tool_family(name)`, en
utilisant une table de correspondance normalisée (en minuscules, sans
séparateurs). Tout nom d'outil qui ne correspond à aucune famille connue —
y compris les outils MCP — retombe sur `GENERIC` et reçoit une tool-card
générique plutôt qu'une spécifique à sa famille.

**Fichiers à toucher :**
- `streamlit_coco/tool_names.py` — ajoutez le(s) nom(s) normalisé(s) de
  l'outil à `_FAMILY_BY_NORMALIZED`, et ajoutez un cas à `family_label()`
  s'il a besoin d'un libellé d'en-tête dédié plutôt que le nom d'outil
  brut.
- `streamlit_coco/tool_cards.py` / `streamlit_coco/tool_extract.py` —
  ajoutez le rendu de carte spécifique à la famille et toute extraction
  d'entrée/diff/SQL dont la nouvelle famille a besoin. Une famille non
  enregistrée ici se rend quand même (via le repli `GENERIC`) ;
  l'enregistrer ne change que la façon dont elle s'affiche.

**Étape de régénération/vérification :** lancez une démo de chat
(`make chat`) avec une invite qui exerce le nouvel outil et confirmez que
la tool-card se rend avec le libellé de famille et l'aperçu attendus au
lieu du repli générique.

**Tests à ajouter :** un cas dans les tests unitaires couvrant
`tool_family()` / `family_label()` pour le nouveau nom d'outil (voir le
patron de couverture par famille d'outil existant dans `tests/`), et une
fixture NDJSON sous `tests/fixtures/ndjson/` si la nouvelle famille
nécessite une couverture de normalisation d'événements dans
`test_ndjson_fixtures.py`.

## Catalogue `types/<id>/` et packs de skills d'App Builder

Chaque type d'application App Builder est un dossier sous
`examples/app_builder/types/` :

```text
types/<id>/
  type.json          carte de catalogue : id, name, icon, users, needs,
                      needs_snowflake, topics, grounding_kind, brief
                      (context, enables, does_not, questions)
  SKILL.md            optionnel — règles de mise en page et de données
                      spécifiques au type, lu par CoCo via add_dirs lors
                      de la génération de l'application
  reference/           optionnel — matériel de référence à l'appui de SKILL.md
  CHECKLIST.md          optionnel — liste d'autocontrôle que l'invite de
                      génération exécute une fois après une écriture,
                      avant de s'arrêter
types/shared/SKILL.md   règles de génération pour chaque type (pas de
                      type.json — ce n'est pas une carte de catalogue) ;
                      chaque invite de Build/regénération dit à CoCo de
                      lire ce fichier plus le SKILL.md propre au type
                      (les deux montés via add_dirs)
```

C'est un point d'extension au niveau du contenu : ajouter un type ne
nécessite pas de changement de code Python, seulement un nouveau dossier
`types/<id>/` (ou l'utilisation de l'éditeur de types de l'écran Admin, qui
écrit les mêmes fichiers).

**Fichiers à toucher :**
- `examples/app_builder/types/<id>/type.json` — requis ; suivez la forme
  d'un type existant (par ex. `types/call-transcription/type.json`) pour
  la structure `brief.questions` et les valeurs de `grounding_kind`
  (`tabular` / `semantic_view` / `documents` / `urls`) qui décident si
  l'étape de profilage est un parseur pandas déterministe
  (`examples/app_builder/engine/profile.py`) ou un job CoCo.
- `examples/app_builder/types/<id>/SKILL.md` — optionnel mais attendu
  pour un type réel ; sans lui, CoCo ne génère qu'en s'appuyant sur les
  règles partagées.
- `examples/app_builder/engine/paths.py` — aucun changement nécessaire ;
  `TYPES_DIR` pointe déjà vers `types/`, donc un nouveau dossier est
  détecté automatiquement.

**Étape de régénération/vérification :** `make app-builder`, ouvrez la
Library, confirmez que la nouvelle carte de type apparaît (filtrée
correctement par ses `topics`), remplissez un brief, et Build — confirmez
que le `streamlit_app.py` généré suit les règles du nouveau `SKILL.md` et
(si un `CHECKLIST.md` est présent) que l'invite de génération s'autocontrôle
contre lui une fois.

**Tests à ajouter :** un cas dans `test_app_builder_catalog.py` couvrant
le fait que le nouveau `type.json` s'analyse et se valide contre les
champs de carte de catalogue que lisent les pages Library/Brief/Admin ; un
cas dans `test_app_builder_profile.py` si `grounding_kind` déclenche un
nouveau chemin de profilage déterministe.

## Ajouter une nouvelle application d'exemple

Le patron établi pour un exemple basé sur un rail (comme dans
`examples/bi_to_semantic/` et `examples/app_builder/`) compose
`copilot_rail()` pour le Copilot et `app_viewer()` pour un aperçu en direct
de ce que CoCo écrit, câblés ensemble via `on_fix` / la mise en file
d'attente de jobs — voir
[architecture](architecture.html#example-app-orchestration).

**Fichiers à toucher :**
- `examples/<name>/` — nouveau dossier avec son propre `app.py` (ou
  `app_pages/` multipage), suivant le patron de composition de l'exemple
  existant le plus proche de la forme du nouveau
  (`backlog_desk/` pour un exemple de rail sans SQL ; `bi_to_semantic/` ou
  `app_builder/` pour un exemple rail + aperçu).
- `Makefile` — ajoutez une cible `<name>:` qui lance le nouvel exemple
  (calquez sur une cible existante, par ex. `bi-semantic:`), ajoutez-la à
  `.PHONY`, et ajoutez une ligne à `help`.
- `doc/deployment/local.md` §5 et `doc/testing.md` — ajoutez la nouvelle
  cible `make` au tableau des exemples pour qu'elle soit découvrable
  depuis la documentation qui les liste déjà.

**Étape de régénération/vérification :** `make <name>` s'exécute et
atteint un écran utilisable ; si l'exemple utilise `app_viewer()`,
confirmez que le port d'aperçu n'entre pas en collision avec le port fixe
d'un exemple existant (les exemples chat/backlog n'utilisent pas
`app_viewer` ; `bi_to_semantic` utilise `:8511`/`:8512` ; `app_builder`
utilise `:8513`).

**Tests à ajouter :** au minimum un test smoke parallèle à la couverture
de `test_smoke.py` des exemples existants, et une checklist de
documentation de fonctionnalité sous
`doc/features/<feature>/test-checklist.md` si l'exemple exerce un nouveau
comportement UI plutôt que de simplement recomposer des primitifs
existants.
