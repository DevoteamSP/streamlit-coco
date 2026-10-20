# Guide de démo

Une démo scriptée de 10 minutes : accroche d'ouverture, démonstration en
direct, clôture. Public : décideurs techniques, ingénieurs data, praticiens
Snowflake.

## Checklist des prérequis techniques (avant la démo)

- [ ] Compte Snowflake avec accès à Cortex Code, connexion configurée
- [ ] `cortex --version` réussit
- [ ] `make install` exécuté, `make check` passe
- [ ] Une base de données Snowflake avec des tables d'exemple disponibles
      (par ex. `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)
- [ ] Fenêtres de terminal et de navigateur disposées côte à côte
- [ ] Répétition effectuée une fois, chronométrée, dans les dernières 24
      heures

## Accroche d'ouverture (30 sec — le problème)

> « Câbler un agent CoCo dans une application Streamlit vous-même signifie
> construire la gestion de session à travers les reruns, le rendu en
> streaming, l'affichage des cartes d'outils et les portes de sécurité à
> partir de zéro. `streamlit-coco` vous donne tout cela en quelques lignes
> de Python. Laissez-moi vous montrer. »

## Démonstration en direct (7 min — étape par étape avec points de discussion)

### Étape 1 — Première impression (2 min)

1. Montrez `examples/chat_app.py` — soulignez que c'est un fichier court et
   lisible, construit à partir de quatre appels : `check_environment()`,
   `render_start_gate()`, `get_or_create_session()`, `panel()` +
   `chat_input_bar()`.
2. Lancez `make chat`.
3. Le navigateur s'ouvre → montrez l'UI du panneau (porte de démarrage,
   puis l'historique de conversation vide et la ligne de statut une fois
   démarré).
4. Tapez : *« What tables are available in SNOWFLAKE_SAMPLE_DATA.TPCH_SF1? »*
5. Observez le rendu en temps réel de l'historique de conversation en
   streaming ; soulignez la carte d'outil qui apparaît (Glob/SQL).

> Point de discussion : « Un fichier Python court. Une UI d'agent complète
> avec streaming, visibilité des outils, et gestion de session prises en
> charge pour vous. »

### Étape 2 — Portes d'approbation (3 min)

1. Tapez : *« Show me the top 5 customers by total order amount. Write the
   SQL and run it. »*
2. L'agent propose du SQL → la bannière d'approbation se déclenche.
   Parcourez le SQL complet affiché, cliquez sur **Approve once** → les
   résultats apparaissent.
3. Tapez : *« Now create a summary table called TOP_CUSTOMERS in my
   schema. »*
4. La porte d'approbation se déclenche à nouveau — cette fois cliquez sur
   **Deny** avec une raison (« let's not create tables in the demo »).
   L'agent reconnaît le refus et suggère une alternative.

> Point de discussion : « Chaque action destructive — SQL, écritures de
> fichiers, commandes bash — requiert une approbation humaine explicite,
> configurée par outil dans `CocoOptions.require_approval_for`. »

### Étape 3 — Sortie structurée (1,5 min)

1. Passez à `make structured` (`examples/structured_output.py`).
2. Montrez `output_schema` dans le code.
3. Tapez : *« Give me a breakdown of orders by status. »*
4. L'agent renvoie du JSON structuré → l'application le rend comme un
   graphique, pas comme du texte brut.

> Point de discussion : « La sortie de l'agent peut circuler directement
> vers vos propres widgets via un callback `on_structured_output` — sans
> parsing JSON manuel. »

### Marge (0,5 min)

Arrivez à la clôture depuis où que vous soyez dans l'étape 3. S'il reste du
temps dans la salle après la clôture scriptée, deux choses valent la peine
d'être montrées mais ne font **pas** partie du script chronométré de 10
minutes :

- `make headless` (`examples/headless_pipeline.py`) — la même API `query()`
  sans import Streamlit, pour la CI et les jobs par lots.
- `make bi-semantic` ou `make backlog` — `copilot_rail()`, montrant CoCo
  comme une colonne à droite dans une application produit plutôt qu'un chat
  plein écran.

## Clôture (2,5 min — récapitulatif de valeur + appel à l'action)

Points de synthèse à afficher à l'écran ou à énoncer verbalement :

- `pip install "streamlit-coco[sdk]"` — une application fonctionnelle en
  quelques lignes
- Portes d'approbation activées par défaut pour les outils destructifs
- Une seule bibliothèque couvre le panneau interactif, la sortie structurée
  et l'usage headless
- Open source (Apache-2.0), conçu pour Snowflake

**Appel à l'action** : « Essayez-la sur votre propre compte Snowflake cette
semaine — le quickstart du README vous mène rapidement à une application
fonctionnelle. Contactez l'asset owner si vous rencontrez des problèmes de
configuration. »

## Questions fréquentes (FAQ)

| Question | Réponse |
| --- | --- |
| Est-ce que ça fonctionne avec Streamlit in Snowflake (SiS) ? | Pas encore livré aujourd'hui. Le déploiement local (CLI + Streamlit + configuration Snowflake sur le même hôte) est la seule topologie livrée ; SiS/SPCS ne sont que dans le périmètre du modèle de menace. |
| Quel LLM utilise-t-elle ? | Celui qu'utilise Cortex Code en interne — aucune configuration de modèle dans cette bibliothèque au-delà de `CocoOptions.model`. |
| Puis-je personnaliser quels outils nécessitent une approbation ? | Oui — `allowed_tools` / `require_approval_for` dans `CocoOptions`, par outil. |
| Est-ce prêt pour la production ? | Alpha (`0.1.9`) — l'API peut encore évoluer. |
| Quelle est la différence avec l'utilisation directe de la CLI CoCo ? | Cette bibliothèque gère la plomberie spécifique à Streamlit : état de session compatible avec les reruns, rendu en streaming, cartes d'outils et UI d'approbation — la CLI seule n'a rien de tout cela. |
| Qu'en est-il du téléversement de fichiers ? | `upload_to_cwd()` / `cwd_uploader()` / `chat_input_bar(accept_file=...)` téléversent dans le répertoire de travail de l'agent ; voir `make cwd-upload`. |
| Qu'est-ce que `copilot_rail()` ? | Un Copilot en rail latéral autour de `panel()` — connexion, jobs en file d'attente, et un popover Display config (limites de messages/caractères) pour un historique de conversation compact. Voir `make bi-semantic` / `make backlog`. |
| Y a-t-il un journal d'audit des approbations ? | Pas persisté aujourd'hui — « Always allow » est limité à la session et s'efface à la réinitialisation. |

## Nettoyage

```bash
# Stop the running app (Ctrl+C)
# No tables/artifacts were created if the CREATE TABLE approval was denied as scripted
```
