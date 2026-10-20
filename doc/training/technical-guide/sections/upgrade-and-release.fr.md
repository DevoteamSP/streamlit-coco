# Mise à niveau et release

## Versions

streamlit-coco suit semver. La version actuelle est **0.1.9** (alpha —
`Development Status :: 3 - Alpha` dans `pyproject.toml`). Il n'existe pas de
fichier de notes de migration séparé de `CHANGELOG.md` ; l'impact d'une
mise à niveau pour une version donnée est ce que l'entrée `CHANGELOG.md` de
cette version indique sous Added / Changed / Fixed / Security.

## Processus de publication

Deux dépôts GitHub sont impliqués :

| Dépôt | Rôle |
|---|---|
| `DevoteamSP/streamlit-coco-dev` | Développement (privé, travail en cours, agents, expérimentations) |
| `lletourmy/streamlit-coco` | Surface de release publique **temporaire** — les tags poussés ici déclenchent la publication PyPI |

Le nom du projet PyPI est toujours `streamlit-coco`, quel que soit le dépôt
GitHub qui le publie actuellement.

**Avertissement sur le publisher temporaire :** `DevoteamSP` n'est pas
encore validé comme PyPI Trusted Publisher, donc `RELEASE_REMOTE`, la porte
de publication PyPI de `release.yml`
(`github.repository == 'lletourmy/streamlit-coco'`), et les URL publiées du
package pointent actuellement vers `lletourmy/streamlit-coco`. Quand
`DevoteamSP` sera validé, tout cela basculera vers
`DevoteamSP/streamlit-coco` — c'est une bascule ponctuelle, pas une étape
répétée à chaque release.

### Étapes de release, dans l'ordre

1. **Préparer dans `-dev`.** Créez le kit de release pour la version
   (`doc/releases/X.Y.Z/`, `doc-dev/releases/X.Y.Z/` à partir des dossiers
   `_template/`), puis lancez `make test-all` et les checklists UI
   manuelles sous `doc/features/`.
2. **Incrémentez `version` dans `pyproject.toml`.**
3. **Nettoyez et mettez à jour `CHANGELOG.md`** — déplacez
   `[Unreleased]` vers `## [X.Y.Z] — YYYY-MM-DD`, retirez les
   sous-sections vides, gardez un bloc Added/Changed/Fixed/Security clair.
4. **Nettoyez et mettez à jour `doc/roadmap.md`** — ligne de statut,
   Now / Next, retirez les éléments livrés du plan actif.
5. **Mettez à jour `doc/prd.md`** (et `doc/api.md` si l'API publique a
   changé).
6. **Ajoutez des captures d'écran** sous
   `doc/releases/X.Y.Z/screenshots/` ; rédigez les brouillons de
   communication sous `doc-dev/releases/X.Y.Z/` (jamais synchronisés
   publiquement).
7. **Fusionnez vers `main`** sur `streamlit-coco-dev`.
8. **Synchronisez l'arbre public :**
   ```bash
   DRY_RUN=1 make sync-release                       # aperçu
   COMMIT=1 PUSH=1 MESSAGE="Release X.Y.Z" make sync-release   # écrire + pousser
   ```
   Clone cible par défaut : `../streamlit-coco`. Remote par défaut :
   `https://github.com/lletourmy/streamlit-coco.git`. Les deux sont
   surchargeables avec `RELEASE_REPO=` / `RELEASE_REMOTE=`. Exclus de
   l'arbre de synchronisation publique : `.cursor/`, `.agents/`,
   `.claude/`, `doc-dev/`, `apps/`, les caches locaux, `dist/`, et le
   script de synchronisation lui-même (également exclu du build sdist via
   `[tool.hatch.build.targets.sdist].exclude` de `pyproject.toml`).
9. **Taguez sur `lletourmy/streamlit-coco`, pas sur `-dev` :**
   ```bash
   cd ../streamlit-coco
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin vX.Y.Z
   ```
10. Le workflow GitHub Release (`release.yml`) ensuite :
    - crée une GitHub Release avec des notes extraites de
      `CHANGELOG.md` ;
    - construit le sdist + wheel (`uv build`) ;
    - génère un SBOM CycloneDX (`sbom-vX.Y.Z.cdx.json`) et l'attache à
      la Release ;
    - publie sur PyPI — **sauté pour les tags `-rc` / `-beta` /
      `-alpha`.**
11. **Vérifiez :**
    ```bash
    pip install "streamlit-coco[sdk]==X.Y.Z"
    ```

### Repli de publication manuelle / locale

Depuis un arbre synchronisé propre (ou `-dev` si inévitable) :

```bash
make build      # uv build -> dist/
make publish    # uv publish — nécessite des identifiants si le Trusted Publisher n'est pas disponible
```

Préférez le chemin CI par tag sur `lletourmy/streamlit-coco` à ce repli.

## Désinstallation

streamlit-coco est une bibliothèque, pas un service — il n'y a pas de
procédure de démontage séparée au-delà de retirer le package :

```bash
pip uninstall streamlit-coco
# ou
uv remove streamlit-coco
```

Retirer le package ne touche à rien de ce qu'il a écrit à l'exécution (voir
[operations](operations.html) Nettoyage) — ces artefacts sont nettoyés
séparément si besoin.

## Procédure de release

C'est le même flux que **Processus de publication** ci-dessus ; il n'existe
pas de runbook de release séparé à maintenir synchronisé. Découper une
release signifie compléter les étapes numérotées de cette section, dans
l'ordre.
