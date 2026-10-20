# Visite guidée

Une visite guidée de 20 à 30 minutes du produit en fonctionnement. Ceci
n'est pas un script de démo (c'est [`demo-guide.md`](demo-guide.html)) et ce
ne sont pas des exercices (c'est [`hands-on.md`](hands-on.html)) — juste ce
que vous allez voir en exécutant chaque commande, et ce à quoi prêter
attention.

Terminez d'abord la [checklist de configuration](setup.html).

## Partie 1 — `make chat`, le pattern préféré (~15 min)

```bash
make chat
```

Cela exécute `examples/chat_app.py`. C'est l'implémentation de référence du
pattern préféré de la bibliothèque : **vous possédez la page, CoCo possède
la session.**

**Ce qui apparaît en premier :** un titre (« CoCo for Streamlit »), une
porte de statut d'environnement (« Start CoCo Chat »), et une barre
latérale. Avant de cliquer sur Start, la porte affiche les résultats de la
sonde SDK / CLI / Snowflake — c'est `check_environment()` rendu par
`render_start_gate()`. Notez qu'elle ne démarre jamais de processus agent
d'elle-même ; elle ne démarre qu'une fois que vous cliquez sur le bouton.

**Cliquez sur Start CoCo Chat.** Le panneau principal est vide au départ,
avec une ligne de statut. Dans la barre latérale, ouvrez le popover
**Settings** (icône `:material/tune:`). Remarquez :

- Un contrôle segmenté **Output mode** (`transcript` / `field`) — cela
  correspond directement à `panel(output_mode=...)`.
- Un interrupteur **CoCo debug mode** — bascule un comportement équivalent à
  `STREAMLIT_COCO_DEBUG` via `st.session_state["coco_debug"]`, affichant les
  payloads d'outils bruts une fois activé.
- Un interrupteur **Plan mode** — définit `permission_mode="plan"` pour
  pouvoir exercer les approbations `ExitPlanMode`.
- Des pastilles d'outils **Auto-allowed** et **Requires approval** — elles
  alimentent en direct `CocoOptions.allowed_tools` et `require_approval_for`,
  et un bouton **Reset session** redémarre le worker quand vous les
  modifiez (les permissions d'outils font partie du hash des options de la
  session).

**Tapez un prompt** — par exemple *« What tables are available in
SNOWFLAKE_SAMPLE_DATA.TPCH_SF1? »*. Observez l'historique de conversation se
rendre progressivement, pas d'un seul coup : c'est la boucle de poll
`@st.fragment` (`run_every=0.25`) qui interroge le worker `CocoSession` en
arrière-plan, si bien que le reste de la page ne rerun pas pendant que CoCo
réfléchit. Une carte d'outil apparaît (probablement Glob ou SQL) — c'est la
carte lisible que la bibliothèque construit à la place d'un dump JSON brut.

**Demandez quelque chose qui écrit** — par exemple *« Create a summary
table called TOP_CUSTOMERS in my schema. »*. Une bannière d'approbation
apparaît avec **Approve once**, **Always allow**, **Deny** (dans cet
ordre). C'est `render_approvals()`, câblé automatiquement à l'intérieur de
`panel()` car `show_approvals=True` est la valeur par défaut. C'est la
porte de supervision humaine (human-in-the-loop) : `Edit`, `Write` et
`Bash` sont dans `require_approval_for` par défaut dans cet exemple.

**Prompts de test dans la barre latérale :** activez **Test prompts** pour
parcourir `examples/testdata/prompts.json` par catégorie et en envoyer un
sans avoir à taper — utile plus tard pour des démos reproductibles.

## Partie 2 — `make backlog`, un rail à côté d'une vraie application (~5 min)

```bash
make backlog
```

Cela exécute le Product Backlog Desk (`examples/backlog_desk/`), une
application multipage, adossée à des fichiers (pas de SQL) : pages
**Board**, **Epic**, **Ticket**, **Release**. Remarquez que Copilot n'est
**pas** une page de navigation — c'est un rail à droite ouvert depuis le
bouton **Copilot** de l'en-tête, ou depuis un lien d'action tel que « Check
DoD » sur un ticket. Fermez-le avec **Close** ; les pages
Board/Epic/Ticket/Release fonctionnent sans connecter Copilot du tout.
C'est la forme pour laquelle `copilot_rail()` est conçu : l'application
possède la page, CoCo se place dans une colonne à côté, pas à sa place.

## Partie 3 — `make bi-semantic`, le rail dans son intégralité (~8 min)

```bash
make bi-semantic
```

Cela exécute BI → Semantic (`examples/bi_to_semantic/`), l'utilisation la
plus complète de `copilot_rail()`. Sur l'écran 1 (**Load**), chargez le
**MIT Tableau Server pack** fourni — aucun entrepôt (warehouse) nécessaire.
Passez à l'écran 4 ou 6 et ouvrez Copilot à droite.

Remarquez, sur la ligne de titre du rail : **Copilot**, un popover
**Connection**, et un popover **Display config** en icône seule
(`:material/display_settings:`, le survol affiche « Display config ») à
côté. Ouvrez Display config — il comporte deux curseurs : **Last messages**
(par défaut 8, plage 1–50) et **First n characters** (par défaut 200, plage
40–1000), chacun avec une pastille marche/arrêt. Déplacer un curseur ne
rerun que le fragment du rail ; le popover reste ouvert et l'historique de
conversation se met à jour en direct. Cela remplace un ancien affichage à
base de pastilles uniquement — depuis cette version, la compacité de
l'historique de conversation est entièrement contrôlée depuis ce popover.

Pendant que CoCo travaille, observez la ligne de titre : un badge compact
**Working · thinking…** s'y trouve — pas une grande carte de statut — et un
bouton **Cancel job** apparaît à côté de **Close**. Après Connect, sur un
historique de conversation vide, vous pouvez voir des boutons **example
question** ; en cliquer un l'envoie immédiatement ou, s'il est marqué
différé, le copie dans le champ de saisie pour que vous puissiez l'éditer
d'abord.

## Ce qu'il faut remarquer dans les trois cas

- L'agent s'exécute toujours côté serveur ; le navigateur ne fait que
  rendre des widgets Streamlit — rien concernant le processus agent n'est
  exposé au client.
- Les portes d'approbation sont la même primitive partout
  (`render_approvals()` à l'intérieur de `panel()`), que l'application soit
  un chat plein écran ou un rail.
- `panel()` est le socle commun ; `copilot_rail()` est `panel()` plus
  l'habillage de connexion, la mise en file d'attente des jobs, et les
  contrôles de compacité de l'historique de conversation, conçu pour
  s'intégrer à côté d'une application existante plutôt que de la remplacer.

Suite : [`hands-on.md`](hands-on.html) pour construire et casser des choses
vous-même.
