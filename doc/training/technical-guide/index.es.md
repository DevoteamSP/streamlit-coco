# Guía Técnica

Esta guía describe streamlit-coco 0.1.9.

streamlit-coco es una librería Python/Streamlit que incrusta el Cortex
Code Agent SDK de Snowflake ("CoCo") en una app Streamlit: un Copilot en
rail lateral o en panel completo, puertas de aprobación human-in-the-loop
para herramientas destructivas, una vista previa en vivo de una app que
CoCo acaba de escribir, salida estructurada hacia tus propios widgets, y
una API headless `query()` / `CocoSession` para scripts y CI. El estado
del paquete es alpha (`Development Status :: 3 - Alpha`).

Esta guía es para quienes ejecutan, mantienen y extienden streamlit-coco
en sí — no para alguien que construye una app Streamlit sobre ella (ese
lector quiere la [Guía de usuario](../user-guide/index.html)).

## Para quién es

| Audiencia | Lee para | Empieza en |
|---|---|---|
| Operar | Instalar la librería y el CLI de CoCo en un host, configurar una conexión de Snowflake, ejecutar las apps de ejemplo, diagnosticar una sesión rota | [install](sections/install.html) → [configuration](sections/configuration.html) → [operations](sections/operations.html) → [help](help.html) |
| Mantener | Mantener el repositorio publicable: tests, puertas de CI, postura de seguridad, cortar un release | [testing-and-ci](sections/testing-and-ci.html) → [security](sections/security.html) → [upgrade-and-release](sections/upgrade-and-release.html) |
| Extender | Añadir un renderizador de texto, una familia de tarjeta de herramienta, un type de App Builder, o una nueva app de ejemplo | [architecture](sections/architecture.html) → [extending](sections/extending.html) → [data-and-contracts](sections/data-and-contracts.html) |

Toda audiencia debería leer primero [architecture](sections/architecture.html);
es el mapa compartido que asumen los demás capítulos.

## Contenidos

**Entender**
- [architecture](sections/architecture.html) — componentes, mapa del repositorio, flujo de datos, invariantes
- [data-and-contracts](sections/data-and-contracts.html) — `CocoEvent`, contratos JSON Schema, artefactos de salida, versionado
- [limits](sections/limits.html) — limitaciones conocidas, expuestas con claridad

**Ejecutar**
- [install](sections/install.html) — prerrequisitos y pasos de instalación ordenados, solo objetivo local
- [configuration](sections/configuration.html) — cada campo de `CocoOptions`, variable de entorno, y archivo de configuración
- [operations](sections/operations.html) — ejecutar, programar, monitorizar, coste/latencia, limpieza
- [security](sections/security.html) — roles y grants, secretos, modelo de amenazas, postura de seguridad de CI

**Construir**
- [testing-and-ci](sections/testing-and-ci.html) — árbol de tests, puertas, qué comprueba CI
- [extending](sections/extending.html) — renderizador de texto, despacho de familia de herramienta, types de App Builder, nuevas apps de ejemplo
- [upgrade-and-release](sections/upgrade-and-release.html) — versionado, el proceso de publicación, desinstalación

**Respuestas**
- [help](help.html) — resolución de problemas indexada por síntoma

## No cubierto

- **Módulo de Skills** — no hay `.cortex/skills/*/SKILL.md` en la raíz del repositorio. Los propios archivos `types/*/SKILL.md` de App Builder son skills de orientación de CoCo internas al ejemplo, documentadas en [extending](sections/extending.html) en lugar de un capítulo estilo `reference-skills`.
- **Objetos de Snowflake** — la librería no crea ni posee ningún DDL de Snowflake. Toda la ejecución SQL ocurre a través de la propia herramienta SQL del agente, protegida por aprobación, usando lo que el rol conectado pueda hacer; no hay capítulo `reference-procedures`.
- **Native App** — no hay `manifest.yml` / `snowflake.yml` en este repositorio. No está lanzado.
- **Modos de despliegue** — solo se lanza hoy un objetivo: local (Streamlit, el CLI de CoCo, y la configuración de Snowflake en el mismo host). Streamlit in Snowflake (SiS) y SPCS son solo alcance del modelo de amenazas y de la hoja de ruta; no están implementados, así que [install](sections/install.html) tiene un solo objetivo, no un capítulo `modes`.
- **Catálogo de controles** — no hay archivos de reglas ni rúbrica de puntuación en este repositorio.
- **Infraestructura como código** — no hay archivos `*.tf` en este repositorio.
