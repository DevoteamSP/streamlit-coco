# Límites

Limitaciones conocidas, expuestas como hechos.

## Estado alpha

`pyproject.toml` clasifica el paquete como `Development Status :: 3 -
Alpha`. La superficie de API pública (`CocoOptions`, `panel()`,
`copilot_rail()`, `app_viewer()`, y el resto de
`streamlit_coco.__init__`) todavía puede cambiar entre versiones menores;
revisa `CHANGELOG.md` al actualizar.

## Streamlit in Snowflake, Community Cloud, y SPCS no están soportados

El CLI de CoCo se lanza como un subproceso local por el SDK. Eso requiere
un host que pueda ejecutar subprocesos y alcanzar una configuración de
conexión de Snowflake en disco. Streamlit Community Cloud no ofrece eso.
Streamlit in Snowflake (SiS) y SPCS se consideran en el modelo de
amenazas como contextos de despliegue, pero no existe ninguna ruta de
instalación, ningún camino de código, ni ninguna superficie de
configuración para ninguno de los dos en este repositorio hoy — ver
[install](install.html) y [architecture](architecture.html).

## Sin registro de auditoría de aprobaciones persistido

La transcripción, incluyendo qué llamadas a herramienta se aprobaron,
denegaron, o "always allowed", vive solo en el estado de sesión de
Streamlit. Nada registra quién aprobó qué, cuándo, una vez que termina la
sesión del navegador. Este es el elemento abierto **SEC-01** (ver
[security](security.html)); no se ha lanzado ninguna fecha objetivo.

## Sin documento dedicado de recomendación de rol de mínimo privilegio

[security](security.html) da orientación provisional de mínimo privilegio
para el rol de Snowflake conectado (no usar `ACCOUNTADMIN`), pero esa
orientación no es un entregable separado — no hay ningún documento
independiente que enumere un conjunto de grants recomendado para un
despliegue de streamlit-coco. Este es el elemento abierto **SEC-02**.

## Un proceso de vista previa de `app_viewer()` por `app_dir`

`app_viewer()` rastrea un único proceso hijo `streamlit run` por
`app_dir` vía `.preview.pid` / `.preview.port` dentro de ese directorio.
Apuntar dos llamadas de `app_viewer()` al mismo `app_dir` a la vez no
está soportado, y `app_dir` nunca debe apuntar a la propia app
anfitriona.

## La app de vista previa hija es otro origen — Fix-with-CoCo no puede leer su DOM

La app Streamlit previsualizada se ejecuta en su propio puerto
(`127.0.0.1:8511`–`:8520`) y se incrusta en un iframe. La página padre no
puede leer el traceback renderizado en el DOM de ese iframe
(cross-origin). **Fix with CoCo** funciona raspando `.preview.log` en
busca de los marcadores `Uncaught app exception` /
`Traceback (most recent call last):`, no inspeccionando lo que renderizó
el navegador. Una línea de log posterior con marca de tiempo se trata
como "error cleared", lo que puede pasar por alto una corrección que en
realidad no resolvió el traceback, o borrar un expander por un motivo no
relacionado; **Fix with CoCo** sigue enviando el tail del log incluso
cuando el parseo falla (ver
[help.html#preview-log-parse-miss](../help.html#preview-log-parse-miss)).

## CodeQL no se ejecuta en CI

`.github/workflows/security.yml` no incluye ningún trabajo de CodeQL —
una organización privada de GitHub necesita una licencia GHAS para subir
resultados de CodeQL, licencia que esta organización no tiene. Hoy solo
se ejecutan Gitleaks (secretos) y `pip-audit` (dependencias). Ver
[security](security.html) y [testing-and-ci](testing-and-ci.html).
