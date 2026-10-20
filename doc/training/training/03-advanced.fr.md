# Cas 3 — Avancé : une session qui ne se connecte jamais

**Niveau :** Avancé — quelque chose casse, vous diagnostiquez seul(e). **Durée :** 30–45
min.

## Contexte

Ce cas s'appuie sur un symptôme documenté dans les références de dépannage
de la bibliothèque elle-même (pas une hypothèse) : une session qui démarre correctement
l'interface mais ne quitte jamais l'état de connexion. La cause profonde ne vous sera pas
communiquée à l'avance — le même symptôme peut provenir de plusieurs couches de
la pile, et une partie de l'exercice consiste à déterminer laquelle.

## Objectif

Diagnostiquez, sans qu'on vous en donne la cause, pourquoi une session CoCo ne devient
pas prête — et corrigez-la — en utilisant les mêmes outils que `check_environment()`
utilise en interne, et non en devinant.

## Données

**Votre propre environnement local.** Aucun objet Snowflake particulier n'est
nécessaire ; il s'agit purement d'un diagnostic d'environnement/connectivité. Utilisez
l'application d'exemple que vous avez déjà fait fonctionner lors des exercices précédents
(`examples/chat_app.py` via `make chat`, ou votre propre application du
[Cas 1](01-simple.html) / [Cas 2](02-intermediate.html)).

## Symptômes

C'est tout ce qui vous est donné. Ne présumez pas de la cause à partir de cette
seule liste — confirmez-la.

- Vous exécutez `make chat` (ou votre propre application construite sur le motif du quickstart).
- L'écran d'accueil s'affiche normalement et montre sa sonde SDK/CLI/Snowflake.
- Vous cliquez sur **Start CoCo Chat**.
- La ligne de statut du panneau reste sur un état de connexion ; la zone de
  l'historique de conversation affiche un « Starting CoCo… » (Démarrage de CoCo…) persistant et ne
  progresse jamais.
- La zone de saisie du chat reste désactivée.
- Aucune bannière d'erreur n'apparaît dans l'interface elle-même.

## Étapes

1. **Reproduisez-le.** Si votre propre environnement ne présente pas actuellement ce
   symptôme, vous pouvez tout de même suivre la méthode de diagnostic ci-dessous — l'objectif
   est la méthode, pas nécessairement de forcer une reproduction en direct.

2. **Activez la sortie de débogage.** Définissez `STREAMLIT_COCO_DEBUG=1` (ou `COCO_DEBUG=1`)
   et relancez. Lisez le terminal, pas seulement le navigateur — cherchez tout ce qui
   s'affiche après « Starting CoCo… ».

3. **Contournez l'interface.** Dans un shell Python, appelez `check_environment()`
   directement avec la même valeur `connection=` que votre application utilise, et affichez
   chaque champ : `sdk_installed`, `sdk_version`, `cli_path`, `cli_version`,
   `snowflake_config_file`, `connection_hint`. Ne vous arrêtez pas au premier
   champ qui semble erroné — lisez-les tous ; plusieurs peuvent être incorrects en
   même temps.

4. **Associez ce que vous avez trouvé à une erreur typée.** `streamlit_coco.errors`
   définit une classe d'exception par couche de défaillance (SDK manquant, CLI
   introuvable, CLI présente mais ne répondant pas, absence de configuration Snowflake,
   connexion/authentification incorrecte, session qui n'atteint jamais l'état prêt). Pour le
   ou les champs qui semblaient erronés à l'étape 3, déterminez laquelle de ces
   classes `require_environment()` aurait levée à la place de la sonde silencieuse de
   `check_environment()` — c'est votre diagnostic.

5. **Corrigez la couche précise que vous avez identifiée**, puis répétez le chemin de
   reproduction (écran d'accueil → **Start CoCo Chat**) et vérifiez que la session atteint
   désormais un état prêt et répond à un prompt.

## Résultat attendu

- Vous pouvez nommer la couche précise qui était défaillante (SDK, CLI sur le `PATH`,
  CLI répondant à `--version`, configuration Snowflake présente, ou connexion/authentification)
  en utilisant les champs propres à `check_environment()`, et non par tâtonnement sur
  l'interface.
- Après la correction, le même chemin de reproduction quitte l'état de connexion, la
  zone de saisie du chat s'active, et un prompt renvoie une réponse normale en flux avec
  une carte d'outil.

## Où chercher en cas de blocage

Commencez ici, puis orientez-vous selon ce que `check_environment()` vous a indiqué :

- [`help.html#session-stuck-connecting`](../technical-guide/help.html#session-stuck-connecting)
  — le symptôme général et comment lire la sortie de débogage.
- [`help.html#coco-connection-error`](../technical-guide/help.html#coco-connection-error)
  — si `check_environment()` a atteint la CLI mais que la connexion/authentification est
  incorrecte.
- [`help.html#cli-not-found`](../technical-guide/help.html#cli-not-found) /
  [`help.html#cli-probe-failed`](../technical-guide/help.html#cli-probe-failed)
  — si `cli_path` ou `cli_version` semblait erroné.
- [`help.html#snowflake-config-not-found`](../technical-guide/help.html#snowflake-config-not-found)
  — si `snowflake_config_file` était vide.
- [`help.html#session-not-ready`](../technical-guide/help.html#session-not-ready)
  — si tous les champs de `check_environment()` semblaient corrects mais que la
  session n'atteint toujours jamais l'état prêt.
