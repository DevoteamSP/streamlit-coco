# Limites

Limitations connues, énoncées comme des faits.

## Statut alpha

`pyproject.toml` classe le package comme `Development Status :: 3 -
Alpha`. La surface d'API publique (`CocoOptions`, `panel()`,
`copilot_rail()`, `app_viewer()`, et le reste de `streamlit_coco.__init__`)
peut encore changer entre versions mineures ; consultez `CHANGELOG.md` lors
d'une mise à niveau.

## Streamlit in Snowflake, Community Cloud, et SPCS ne sont pas pris en charge

Le CLI CoCo est lancé comme sous-processus local par le SDK. Cela nécessite
un hôte capable d'exécuter des sous-processus et d'atteindre une
configuration de connexion Snowflake sur disque. Streamlit Community Cloud
n'offre pas cela. Streamlit in Snowflake (SiS) et SPCS sont considérés dans
le modèle de menace comme des contextes de déploiement, mais aucun chemin
d'installation, aucun chemin de code, et aucune surface de configuration
pour l'un ou l'autre n'existe dans ce dépôt aujourd'hui — voir
[install](install.html) et [architecture](architecture.html).

## Aucun journal d'audit d'approbation persistant

La transcription, y compris les appels d'outils approuvés, refusés, ou mis
en « always allowed », ne vit que dans l'état de session Streamlit. Rien
n'enregistre qui a approuvé quoi, quand, une fois la session du navigateur
terminée. C'est l'élément ouvert **SEC-01** (voir [security](security.html))
; aucune date cible n'a été livrée.

## Aucun document dédié de recommandation de rôle à moindre privilège

[security](security.html) donne une consigne provisoire de moindre
privilège pour le rôle Snowflake connecté (ne pas utiliser
`ACCOUNTADMIN`), mais cette consigne n'est pas un livrable séparé — il
n'existe pas de document autonome qui énumère un jeu de privilèges
recommandé pour un déploiement streamlit-coco. C'est l'élément ouvert
**SEC-02**.

## Un seul processus d'aperçu `app_viewer()` par `app_dir`

`app_viewer()` suit un unique processus enfant `streamlit run` par
`app_dir` via `.preview.pid` / `.preview.port` à l'intérieur de ce
répertoire. Pointer deux appels `app_viewer()` vers le même `app_dir` en
même temps n'est pas pris en charge, et `app_dir` ne doit jamais pointer
vers l'application hôte elle-même.

## L'application enfant de l'aperçu est une origine différente — Fix-with-CoCo ne peut pas lire son DOM

L'application Streamlit prévisualisée s'exécute sur son propre port
(`127.0.0.1:8511`–`:8520`) et est intégrée dans une iframe. La page parente
ne peut pas lire le traceback rendu dans le DOM de cette iframe
(cross-origin). **Fix with CoCo** fonctionne en analysant `.preview.log`
à la recherche des marqueurs `Uncaught app exception` /
`Traceback (most recent call last):`, pas en inspectant ce que le
navigateur a rendu. Une ligne de journal horodatée ultérieure est traitée
comme « erreur effacée », ce qui peut manquer une correction qui n'a en
réalité pas résolu le traceback, ou effacer un expander pour une raison
sans rapport ; **Fix with CoCo** envoie quand même la fin du journal même
quand l'analyse passe à côté (voir
[help.html#preview-log-parse-miss](../help.html#preview-log-parse-miss)).

## CodeQL ne tourne pas en CI

`.github/workflows/security.yml` n'inclut pas de job CodeQL — une
organisation GitHub privée a besoin d'une licence GHAS pour téléverser des
résultats CodeQL, licence que cette organisation ne possède pas. Seuls
Gitleaks (secrets) et `pip-audit` (dépendances) tournent aujourd'hui. Voir
[security](security.html) et [testing-and-ci](testing-and-ci.html).
