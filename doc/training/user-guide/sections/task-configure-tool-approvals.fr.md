# Je veux configurer les approbations d'outils

**Pour** un développeur décidant quels outils de l'agent nécessitent une supervision humaine · **15 min** · **une app minimale fonctionnelle**

Vous obtenez une session où des outils spécifiques s'exécutent
automatiquement et d'autres se mettent en pause pour approbation, résolue
soit via l'interface intégrée, soit programmatiquement.

## Avant de commencer

- Une app minimale fonctionnelle ([Je veux construire une app CoCo minimale](task-build-a-minimal-app.html)).
- Savoir quels outils l'agent peut appeler dans votre app (`Read`, `Glob`,
  `Grep`, `Edit`, `Write`, `Bash`, l'outil SQL, `AskUserQuestion`,
  `ExitPlanMode`, les outils fournis par MCP, …) et lesquels sont destructifs
  dans votre contexte.

## Étapes

1. Définissez `allowed_tools` sur `CocoOptions` pour les outils qui ne
   devraient jamais nécessiter de prompt, et `require_approval_for` pour
   ceux qui doivent toujours se mettre en pause :

   ```python
   options = st_coco.CocoOptions(
       connection="my_connection",
       allowed_tools=["Read", "Glob", "Grep"],
       require_approval_for=["Edit", "Write", "Bash"],
   )
   ```

   `AskUserQuestion` et `ExitPlanMode` se mettent toujours en pause pour une
   décision, quel que soit ce qui est listé dans l'une ou l'autre option.

2. Montez le panneau avec les approbations visibles (le défaut) :

   ```python
   st_coco.panel(session, show_approvals=True)
   ```

   Quand l'agent appelle un outil reconnu par `require_approval_for`,
   l'état de la session devient `awaiting_user` et `render_approvals()`
   affiche trois contrôles : **Approve once**, **Always allow**, **Deny**.
   Ni les requêtes `AskUserQuestion` ni celles `ExitPlanMode` n'affichent
   **Always allow**.

3. Pour résoudre les approbations depuis votre propre interface au lieu des
   contrôles intégrés, appelez directement les résolveurs bas niveau avec
   l'id de la requête en attente (depuis
   `session.chat_result().pending_approval`) :

   ```python
   result = session.chat_result()
   if result.pending_approval:
       request_id = result.pending_approval["request_id"]
       st_coco.approve_pending(session, request_id, always=False)
       # ou : st_coco.deny_pending(session, request_id, reason="not now")
   ```

4. Optionnellement, restreignez ou élargissez le verrou à l'exécution en
   passant un callable à `require_approval_for` plutôt qu'une liste fixe,
   puis appelez `session.sync_options(options)` après l'avoir changé pour
   que la session prenne en compte le nouveau hash.

## Résultat

Les outils dans `allowed_tools` s'exécutent sans aucun prompt. Les outils
reconnus par `require_approval_for` mettent l'exécution en pause et
affichent le contrôle d'approbation à trois boutons (ou attendent
`approve_pending`/`deny_pending` dans une interface personnalisée) avant de
s'exécuter. Un refus n'exécute pas l'appel d'outil ; le tour de l'agent
continue à partir de là, optionnellement avec la raison que vous avez
transmise.

## Variations

- **Always allow** s'applique uniquement à la session en cours — c'est
  effacé au `session.reset()` ou au redémarrage du processus, jamais écrit
  dans une politique persistée.
- `permission_mode="plan"` fait passer les appels d'outils par un flux
  `ExitPlanMode` au lieu d'une approbation par outil ; `render_plan_banner()`
  affiche la bannière du mode plan et l'appel à l'action **Execute plan**.
- `approval_timeout_seconds` (défaut `600.0`, dix minutes) contrôle combien
  de temps une approbation en attente patiente avant que l'exécution échoue
  avec `ApprovalTimeoutError`.

## En cas d'échec

- [Délai d'approbation dépassé](../../technical-guide/help.html#approval-timeout)
- [« Always allow » est limité à la session](../../technical-guide/help.html#always-allow-scope)
