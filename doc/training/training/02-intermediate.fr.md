# Cas 2 — Intermédiaire : portes d'approbation et rail Copilot dans une application réelle

**Niveau :** Intermédiaire — vos données / une tâche réelle, moins guidé. **Durée :**
45–60 min.

## Contexte

Un rail à côté de vos propres pages est la structure pour laquelle `copilot_rail()`
est conçu : `examples/backlog_desk/` (adossé à des fichiers/JSON, sans SQL) et
`examples/bi_to_semantic/` (Tableau/Power BI → vue sémantique) l'intègrent tous deux
dans une application multipage existante plutôt que de remplacer l'application par une fenêtre
de chat. Ce cas vous demande de faire de même sur un workflow réel, avec des points de
contrôle plutôt que des instructions pas à pas.

## Objectif

Configurez un `CocoOptions` avec `require_approval_for` pour un workflow qui
modifie réellement quelque chose, et intégrez `copilot_rail()` comme colonne de droite
à côté d'une application multipage existante (ou celle fournie).

## Données

**Les vôtres, ou un substitut.** Si vous exploitez déjà une application
Streamlit multipage, utilisez-la. Sinon, utilisez `examples/backlog_desk/` comme substitut à « vos
données » : des tickets, epics et releases adossés à des fichiers sous
`examples/backlog_desk/data/{epics,tickets,releases,policies}` — de vrais fichiers
que vous pouvez inspecter avec `git diff` après que CoCo les a modifiés. `examples/bi_samples/`
(packs de fixtures Tableau/Power BI sous licence MIT) est le substitut alternatif si
vous préférez suivre la structure BI → Sémantique.

## Points de contrôle

1. **Choisissez votre surface.** Identifiez une page de votre application (ou
   la page Ticket de `examples/backlog_desk/`) où une action de modification n'a
   actuellement aucun garde-fou human-in-the-loop (supervision humaine), ou où vous souhaitez
   qu'un agent rédige quelque chose qu'une personne relit avant application.

2. **Définissez `CocoOptions` pour ce workflow.** Séparez les outils qui peuvent
   s'exécuter sans surveillance (exploration en lecture seule : `Read`, `Glob`, `Grep`) des
   outils qui doivent marquer une pause (`Edit`, `Write`, `Bash`, et `SQL` si votre workflow
   touche Snowflake). Placez le premier ensemble dans `allowed_tools` et le second dans
   `require_approval_for` — ils ne doivent pas se chevaucher pour un même outil.
   *Point de contrôle : vous pouvez indiquer, pour chaque outil que votre workflow pourrait
   invoquer, à quelle liste il appartient et pourquoi.*

3. **Limitez une session à la page.** Utilisez `get_or_create_session(opts,
   key=...)` avec une clé spécifique à ce workflow, et décidez quand elle doit se
   réinitialiser — `copilot_rail()` ne se réinitialise pas d'elle-même lors d'un changement de
   `cwd` ou de schéma ; c'est à l'appelant que revient cette décision de cycle de vie.
   *Point de contrôle : vous savez exactement quelle action utilisateur doit déclencher
   `reset_session(...)`.*

4. **Intégrez `copilot_rail()`.** Ajoutez-le comme colonne de droite de votre mise en
   page, en suivant le motif de `examples/backlog_desk/` (ouvert depuis un bouton
   d'en-tête, fermé avec **Close** (fermer)) ou le motif de `examples/bi_to_semantic/`
   (un popover de connexion à côté du rail). Reportez-vous à
   `doc/features/copilot-rail/copilot-rail.md` dans le dépôt pour la liste complète des
   paramètres (`job=`, `on_job_sent=`, `on_job_finished=`,
   `example_questions=`, `toml_file=`). *Point de contrôle : le rail s'ouvre et se
   ferme sans relancer le reste de votre page.*

5. **Mettez une tâche réelle en file d'attente et observez sa mise sous garde.** Déclenchez
   l'action de modification depuis votre page (une tâche `status="queued"`, ou un prompt
   de chat direct) et vérifiez que `require_approval_for` la met en pause avec **Approve
   once** (approuver une fois) / **Always allow** (toujours autoriser) / **Deny**
   (refuser), et non avec une écriture silencieuse. *Point de contrôle : vous pouvez
   pointer la ligne exacte de votre `CocoOptions` responsable de la pause.*

6. **Gardez l'historique de conversation utilisable.** Ouvrez le popover de configuration
   d'affichage du rail (`:material/display_settings:`) et ajustez **Last messages**
   (derniers messages) / **First n characters** (n premiers caractères) pour qu'une session
   longue reste lisible dans la largeur du rail.

## Résultat attendu

- Copilot se place dans une colonne de droite à côté du contenu existant de votre page —
  la page elle-même n'est jamais remplacée par un chat plein écran.
- L'action de modification choisie à l'étape 1 marque désormais une pause pour une
  décision explicite d'approbation/refus avant de s'exécuter.
- Vous pouvez expliquer, sans relire le code, pourquoi chaque outil de votre
  workflow est soit exécuté automatiquement, soit soumis à approbation.

## Où chercher en cas de blocage

- La porte d'approbation ne se déclenche pas, ou se déclenche pour le mauvais outil :
  [`help.html#always-allow-scope`](../technical-guide/help.html#always-allow-scope).
- La bannière d'approbation reste sans réponse jusqu'à expiration du délai :
  [`help.html#approval-timeout`](../technical-guide/help.html#approval-timeout).
- Quelque chose dans le workflow se comporte de façon inattendue et les cartes d'outil
  seules ne suffisent pas à l'expliquer : activez `STREAMLIT_COCO_DEBUG=1` et relancez — voir
  [`help.html#debug-mode-not-showing-payloads`](../technical-guide/help.html#debug-mode-not-showing-payloads)
  si la charge utile brute n'apparaît toujours pas.
