# Sécurité

Source : `doc/security/threat-model.md` (v1.0, 2026-07-28),
`doc/security/findings-report.md` (2026-07-28, version auditée 0.1.0),
`.github/workflows/security.yml`.

## Rôles et privilèges

streamlit-coco ne gère aucun privilège Snowflake et ne livre aucune
définition de rôle recommandée. Ce qu'elle fait réellement avec le rôle
connecté :

- La bibliothèque délègue toute l'authentification Snowflake au CLI/SDK
  CoCo et à la configuration de connexion Snowflake au niveau du système
  d'exploitation. Elle n'évalue ni ne restreint jamais ce que le rôle
  connecté peut faire.
- Chaque instruction SQL exécutée par l'agent passe par l'outil SQL propre
  de l'agent, protégé par le flux d'approbation décrit ci-dessous. **Les
  permissions SQL effectives dans une session sont exactement les
  privilèges du rôle connecté** — le point d'approbation contrôle si une
  instruction s'exécute, pas ce qu'elle est autorisée à toucher une fois
  approuvée.
- **Recommandation (moindre privilège) : connectez-vous avec un rôle
  limité aux schémas et à l'entrepôt dont la session a réellement besoin,
  pas `ACCOUNTADMIN`.** Un rôle avec `ACCOUNTADMIN` ou un privilège large
  équivalent comme `MANAGE WAREHOUSES` (qui peut modifier et exploiter
  tous les entrepôts du compte, pas seulement celui qu'une démo utilise)
  signifie qu'un `DROP` ou `DELETE` approuvé dans une session peut
  atteindre des objets hors du périmètre prévu. Ce guide ne nomme pas de
  rôle ni de jeu de privilèges spécifique parce qu'aucun n'est versionné
  dans le dépôt — connectez les applications de démo/exemple avec un rôle
  qui ne possède que la base de données, le schéma et l'entrepôt dont
  l'exemple a besoin.

Un document de recommandation de rôle à moindre privilège dédié n'existe pas
encore (suivi comme SEC-02, ouvert — voir ci-dessous et
[limits](limits.html)).

## Gestion des secrets

- Les identifiants Snowflake (PAT, key-pair, ou SSO) vivent dans la
  configuration Snowflake au niveau du système d'exploitation
  (`~/.snowflake/connections.toml` ou l'ancien `config.toml`) ou dans un
  trousseau (keyring) du système, jamais dans le code de cette
  bibliothèque ni dans l'état de session Streamlit.
- La bibliothèque ne journalise ni ne stocke jamais elle-même les
  identifiants ; l'authentification est entièrement déléguée au CLI/SDK
  CoCo.
- `.gitignore` couvre `.env`, `*.secret`, `*.key`, et `client_*.yaml`.
- Ne commitez pas un fichier de connexions Snowflake ni aucun des motifs
  ci-dessus dans le dépôt. Il n'y a pas de coffre-fort à secrets dans le
  dépôt à configurer.

## Données traitées

| Donnée | Sensibilité | Où elle vit |
|---|---|---|
| Invites utilisateur et transcriptions d'agent | Moyenne–Haute | État de session Streamlit, en mémoire |
| Résultats SQL affichés dans l'UI | Moyenne–Haute | En mémoire ; peut contenir des données personnelles selon la requête exécutée par l'agent |
| Identifiants Snowflake | Haute | Trousseau système / `~/.snowflake/` — jamais dans le dépôt ni dans l'état de la bibliothèque |
| Flux NDJSON de session CoCo | Moyenne | Socket local / transport SDK (cible de déploiement locale : pas de saut réseau) |

La question de savoir si les résultats SQL affichés à un spectateur donné
contiennent des données que ce spectateur ne devrait pas voir relève de la
responsabilité de l'application connectée (politiques d'accès en ligne, ou
ne pas partager une session entre plusieurs utilisateurs) — la bibliothèque
ne filtre pas les résultats de requêtes.

## Résumé du modèle de menace

Extrait de `doc/security/threat-model.md` §4 :

- **L'injection d'invite déclenche des outils dangereux — Sévérité
  élevée.** Atténué par les points d'approbation : `PermissionManager`
  intercepte avant l'exécution, et l'utilisateur doit approuver
  explicitement. Le modèle de menace recommande en outre de se connecter
  avec un rôle à moindre privilège, pas `ACCOUNTADMIN` (voir Rôles et
  privilèges ci-dessus).
- **Escalade via « Always allow » — Sévérité moyenne.** Atténué par la
  portée : « always allow » est par outil, par session uniquement, détenu
  dans `PermissionManager.always_allowed_tools`, et s'efface à la
  réinitialisation de session ou au redémarrage du processus (voir
  Révocation ci-dessous). `AskUserQuestion` et `ExitPlanMode` n'exposent
  jamais d'option « Always allow ».
- **Répudiation — aucun journal persistant des actions destructrices
  approuvées — Sévérité moyenne, ouvert.** La transcription n'existe que
  dans l'état de session Streamlit ; rien n'est écrit dans un stockage
  durable. Suivi comme **SEC-01** (ouvert, cible v0.2) — voir
  [limits](limits.html).
- **Divulgation d'information via des secrets dans la transcription/les
  journaux — Sévérité moyenne.** Atténué : la bibliothèque ne journalise
  pas les identifiants, et le SDK les masque de sa sortie.
- **Élévation de privilège via une dépendance compromise — chaîne
  d'approvisionnement.** Atténué par `pip-audit` en CI et le scan Gitleaks
  du dépôt (voir la posture de sécurité CI ci-dessous) ; `uv.lock` est
  commité pour des builds reproductibles.

## Révocation

« Always allow » pour un outil est limité à l'instance `CocoSession` en
cours d'exécution. Il s'efface automatiquement lors de :

- `session.reset()`
- `session.close()` (et redémarrage du processus)

Il n'existe pas de magasin de politique « always allow » persistant, et
aucune action UI pour révoquer le « always allow » d'un seul outil sans
réinitialiser toute la session.

## Posture de sécurité CI (actuelle)

La CI exécute deux scanners, pas trois :

- **Gitleaks** (binaire CLI, pas `gitleaks-action@v2`) — scan de secrets
  sur chaque pull request, chaque push vers `main`, et chaque semaine
  (lundi 06:00 UTC).
- **`pip-audit --skip-editable`** — scan de vulnérabilités de dépendances
  sur les mêmes déclencheurs.

**CodeQL ne tourne pas.** `doc/security/findings-report.md` liste encore
CodeQL comme « CI-only (GitHub Actions) », mais `.github/workflows/security.yml`
a été modifié en `0.1.5` pour retirer le job CodeQL — une organisation
GitHub privée a besoin d'une licence GitHub Advanced Security (GHAS) pour
téléverser des résultats CodeQL, licence que cette organisation ne possède
pas, donc l'étape d'analyse échouerait comme une erreur de configuration.
Le commentaire du fichier de workflow lui-même l'indique explicitement.
Considérez CodeQL comme **non actif** dans ce dépôt aujourd'hui ; ne citez
pas le tableau du findings-report comme étant à jour.

Les deux jobs de `security.yml` sont aussi reproduits dans `ci.yml` comme
des étapes `continue-on-error: true` sur le job `test` (non bloquant tant
qu'une base saine n'y est pas également établie).

## Éléments ouverts et résolus (`threat-model.md` §7)

| ID | Description | Statut |
|---|---|---|
| SEC-01 | Persister un journal d'audit des approbations (qui a approuvé quoi, quand) | **Ouvert**, cible v0.2 |
| SEC-02 | Documenter une recommandation de rôle à moindre privilège pour le compte Snowflake connecté, comme livrable dédié | **Ouvert**, cible v0.2 (la section Rôles et privilèges de cette page est une consigne provisoire, pas ce livrable) |
| SEC-03 | Commiter `uv.lock` pour des builds reproductibles | **Résolu** — le lockfile est commité aujourd'hui |
| SEC-04 | Ajouter la génération de SBOM au workflow de release | **Résolu**, livré en `0.1.5` — `release.yml` génère un SBOM CycloneDX (`sbom-vX.Y.Z.cdx.json`) attaché à la GitHub Release à chaque tag |

## Résultats de revue manuelle (`findings-report.md`, version auditée 0.1.0)

- `pip-audit` : 0 vulnérabilité connue.
- Gitleaks : 0 fuite sur 11 commits scannés.
- Revue manuelle : aucun `shell=True`, aucun identifiant en dur, aucun
  `eval()` / `exec()` trouvé dans la source.
