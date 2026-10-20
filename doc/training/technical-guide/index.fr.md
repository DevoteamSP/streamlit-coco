# Guide technique

Ce guide décrit streamlit-coco 0.1.9.

streamlit-coco est une bibliothèque Python/Streamlit qui intègre le Cortex
Code Agent SDK de Snowflake (« CoCo ») dans une application Streamlit : un
Copilot en rail latéral ou en panneau plein, des points d'approbation
human-in-the-loop pour les outils destructeurs, un aperçu en direct d'une
application que CoCo vient d'écrire, une sortie structurée injectée dans vos
propres widgets, et une API headless `query()` / `CocoSession` pour les
scripts et la CI. Le statut du package est alpha (`Development Status :: 3 -
Alpha`).

Ce guide s'adresse aux personnes qui font fonctionner, maintiennent et
étendent streamlit-coco lui-même — pas à celles qui construisent une
application Streamlit par-dessus (ce lectorat veut le [Guide
utilisateur](../user-guide/index.html)).

## À qui ce guide s'adresse

| Public | Lit pour | Commence à |
|---|---|---|
| Exploiter | Installer la bibliothèque et le CLI CoCo sur un hôte, configurer une connexion Snowflake, lancer les applications d'exemple, diagnostiquer une session cassée | [install](sections/install.html) → [configuration](sections/configuration.html) → [operations](sections/operations.html) → [help](help.html) |
| Maintenir | Garder le dépôt prêt à être publié : tests, portes CI, posture de sécurité, découpage d'une version | [testing-and-ci](sections/testing-and-ci.html) → [security](sections/security.html) → [upgrade-and-release](sections/upgrade-and-release.html) |
| Étendre | Ajouter un rendu de texte, une famille de tool-card, un type App Builder, ou une nouvelle application d'exemple | [architecture](sections/architecture.html) → [extending](sections/extending.html) → [data-and-contracts](sections/data-and-contracts.html) |

Chaque public devrait lire [architecture](sections/architecture.html) en
premier ; c'est la carte partagée que les autres chapitres supposent connue.

## Sommaire

**Comprendre**
- [architecture](sections/architecture.html) — composants, plan du dépôt, flux de données, invariants
- [data-and-contracts](sections/data-and-contracts.html) — `CocoEvent`, contrats JSON Schema, artefacts de sortie, versionnage
- [limits](sections/limits.html) — limitations connues, énoncées sans détour

**Exploiter**
- [install](sections/install.html) — prérequis et étapes d'installation ordonnées, cible locale uniquement
- [configuration](sections/configuration.html) — chaque champ `CocoOptions`, variable d'environnement, et fichier de configuration
- [operations](sections/operations.html) — exécuter, planifier, surveiller, coût/latence, nettoyage
- [security](sections/security.html) — rôles et privilèges, secrets, modèle de menace, posture de sécurité CI

**Construire**
- [testing-and-ci](sections/testing-and-ci.html) — arborescence de tests, portes, ce que la CI vérifie
- [extending](sections/extending.html) — rendu de texte, dispatch par famille d'outil, types App Builder, nouvelles applications d'exemple
- [upgrade-and-release](sections/upgrade-and-release.html) — versionnage, processus de publication, désinstallation

**Réponses**
- [help](help.html) — dépannage indexé par symptôme

## Non couvert

- **Module Skills** — aucun `.cortex/skills/*/SKILL.md` à la racine du dépôt. Les propres fichiers `types/*/SKILL.md` d'App Builder sont des skills de consigne CoCo internes à l'exemple, documentés dans [extending](sections/extending.html) plutôt que dans un chapitre de type `reference-skills`.
- **Objets Snowflake** — la bibliothèque ne crée ni ne possède aucun DDL Snowflake. Toute exécution SQL passe par l'outil SQL propre à l'agent, protégé par approbation, en utilisant ce que le rôle connecté peut faire ; il n'y a pas de chapitre `reference-procedures`.
- **Native App** — aucun `manifest.yml` / `snowflake.yml` dans ce dépôt. Non livré.
- **Modes de déploiement** — une seule cible est livrée aujourd'hui : locale (Streamlit, le CLI CoCo, et la configuration Snowflake sur le même hôte). Streamlit in Snowflake (SiS) et SPCS relèvent uniquement du modèle de menace et de la feuille de route ; ils ne sont pas implémentés, donc [install](sections/install.html) n'a qu'une seule cible, pas un chapitre `modes`.
- **Catalogue de contrôles** — aucun fichier de règles ni grille de notation dans ce dépôt.
- **Infrastructure as code** — aucun fichier `*.tf` dans ce dépôt.
