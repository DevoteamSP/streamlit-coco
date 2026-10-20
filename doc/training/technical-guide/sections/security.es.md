# Seguridad

Fuente: `doc/security/threat-model.md` (v1.0, 2026-07-28),
`doc/security/findings-report.md` (2026-07-28, versión auditada 0.1.0),
`.github/workflows/security.yml`.

## Roles y grants

streamlit-coco no gestiona grants de Snowflake ni incluye ninguna
definición de rol recomendada. Lo que realmente hace con el rol
conectado:

- La librería delega toda la autenticación de Snowflake al CLI/SDK de
  CoCo y a la configuración de conexión de Snowflake a nivel de sistema
  operativo. Nunca evalúa ni restringe lo que puede hacer el rol
  conectado.
- Cada sentencia SQL que ejecuta el agente pasa por la propia herramienta
  SQL del agente, protegida por el flujo de aprobación descrito abajo.
  **Los permisos SQL efectivos en una sesión son exactamente los grants
  del rol conectado** — la puerta de aprobación controla si una sentencia
  se ejecuta, no qué puede tocar una vez aprobada.
- **Recomendación (mínimo privilegio): conecta con un rol limitado a los
  esquemas y el warehouse que la sesión realmente necesita, no
  `ACCOUNTADMIN`.** Un rol con `ACCOUNTADMIN` o un grant amplio
  equivalente como `MANAGE WAREHOUSES` (que puede modificar y operar
  cada warehouse de la cuenta, no solo el que usa una demo) significa que
  un `DROP` o `DELETE` aprobado en una sesión puede alcanzar objetos
  fuera del alcance previsto. Esta guía no nombra un rol o conjunto de
  grants específico porque ninguno está incluido en el repositorio —
  conecta las apps de demo/ejemplo con un rol que posea solo la base de
  datos, el esquema, y el warehouse que el ejemplo necesita.

Un documento dedicado de recomendación de rol de mínimo privilegio aún no
existe (rastreado como SEC-02, abierto — ver abajo y
[limits](limits.html)).

## Gestión de secretos

- Las credenciales de Snowflake (PAT, par de claves, o SSO) viven en la
  configuración de Snowflake a nivel de sistema operativo
  (`~/.snowflake/connections.toml` o el `config.toml` heredado) o en un
  keyring del sistema operativo, nunca en el código de esta librería ni
  en el estado de sesión de Streamlit.
- La librería nunca registra ni almacena credenciales por sí misma; la
  autenticación se delega enteramente al CLI/SDK de CoCo.
- `.gitignore` cubre `.env`, `*.secret`, `*.key`, y `client_*.yaml`.
- No confirmes un archivo de conexiones de Snowflake ni ninguno de los
  patrones anteriores en el repositorio. No hay ningún almacén de
  secretos en el repositorio que configurar.

## Datos gestionados

| Datos | Sensibilidad | Dónde viven |
|---|---|---|
| Prompts de usuario y transcripciones del agente | Media–Alta | Estado de sesión de Streamlit, en memoria |
| Resultados SQL renderizados en la interfaz | Media–Alta | En memoria; pueden contener PII según la consulta que ejecutó el agente |
| Credenciales de Snowflake | Alta | Keyring del sistema operativo / `~/.snowflake/` — nunca en el repositorio ni en el estado de la librería |
| Flujo NDJSON de la sesión de CoCo | Media | Socket local / transporte del SDK (objetivo de despliegue local: sin salto de red) |

Si los resultados SQL mostrados a un determinado visor contienen datos
que ese visor no debería ver es responsabilidad de la app conectada
(políticas de row-access, o no compartir una sesión entre usuarios) — la
librería no filtra los resultados de las consultas.

## Resumen del modelo de amenazas

De `doc/security/threat-model.md` §4:

- **La inyección de prompt dispara herramientas peligrosas — Severidad
  alta.** Mitigado por puertas de aprobación: `PermissionManager`
  intercepta antes de la ejecución, y el usuario debe aprobar
  explícitamente. El modelo de amenazas recomienda además conectar con un
  rol de mínimo privilegio, no `ACCOUNTADMIN` (ver Roles y grants
  arriba).
- **Escalada de "Always allow" — Severidad media.** Mitigado por el
  alcance: "always allow" es solo por herramienta, por sesión, mantenido
  en `PermissionManager.always_allowed_tools`, y se borra al reiniciar la
  sesión o al reiniciar el proceso (ver Revocación abajo).
  `AskUserQuestion` y `ExitPlanMode` nunca exponen una opción "Always
  allow".
- **Repudio — sin registro persistido de acciones destructivas aprobadas
  — Severidad media, abierto.** La transcripción existe solo en el
  estado de sesión de Streamlit; nada se escribe en almacenamiento
  duradero. Rastreado como **SEC-01** (abierto, objetivo v0.2) — ver
  [limits](limits.html).
- **Divulgación de información vía secretos en transcripción/logs —
  Severidad media.** Mitigado: la librería no registra credenciales, y
  el SDK las redacta de su salida.
- **Elevación de privilegios vía una dependencia comprometida — cadena de
  suministro.** Mitigado por `pip-audit` en CI y el escaneo de Gitleaks
  sobre el repositorio (ver postura de seguridad de CI abajo);
  `uv.lock` está confirmado para builds reproducibles.

## Revocación

"Always allow" para una herramienta tiene el alcance de la instancia
`CocoSession` en ejecución. Se borra automáticamente en:

- `session.reset()`
- `session.close()` (y al reiniciar el proceso)

No hay ningún almacén de política "always allow" persistente, y ninguna
acción de interfaz para revocar el "always allow" de una sola herramienta
sin reiniciar toda la sesión.

## Postura de seguridad de CI (actual)

CI ejecuta dos scanners, no tres:

- **Gitleaks** (binario CLI, no `gitleaks-action@v2`) — escaneo de
  secretos en cada pull request, cada push a `main`, y semanalmente
  (lunes 06:00 UTC).
- **`pip-audit --skip-editable`** — escaneo de vulnerabilidades de
  dependencias en los mismos disparadores.

**CodeQL no se está ejecutando.** `doc/security/findings-report.md`
sigue listando CodeQL como "CI-only (GitHub Actions)", pero
`.github/workflows/security.yml` se modificó en `0.1.5` para eliminar el
trabajo de CodeQL — una organización privada de GitHub necesita una
licencia GitHub Advanced Security (GHAS) para subir resultados de
CodeQL, licencia que esta organización no tiene, así que el paso de
análisis fallaría como un error de configuración. El propio comentario
del archivo del workflow lo indica explícitamente. Trata CodeQL como **no
activo** en este repositorio hoy; no cites la tabla de findings-report
como actual.

Ambos trabajos de `security.yml` también se reflejan en `ci.yml` como
pasos `continue-on-error: true` en el trabajo `test` (no bloqueantes
hasta que se establezca también una línea base limpia allí).

## Elementos abiertos y resueltos (`threat-model.md` §7)

| ID | Descripción | Estado |
|---|---|---|
| SEC-01 | Persistir un registro de auditoría de aprobaciones (quién aprobó qué, cuándo) | **Abierto**, objetivo v0.2 |
| SEC-02 | Documentar una recomendación de rol de mínimo privilegio para la cuenta de Snowflake conectada, como entregable dedicado | **Abierto**, objetivo v0.2 (la sección Roles y grants de esta página es orientación provisional, no ese entregable) |
| SEC-03 | Confirmar `uv.lock` para builds reproducibles | **Resuelto** — el lockfile está confirmado hoy |
| SEC-04 | Añadir generación de SBOM al flujo de release | **Resuelto**, lanzado en `0.1.5` — `release.yml` genera un SBOM CycloneDX (`sbom-vX.Y.Z.cdx.json`) adjunto al GitHub Release en cada tag |

## Hallazgos de la revisión manual (`findings-report.md`, versión
auditada 0.1.0)

- `pip-audit`: 0 vulnerabilidades conocidas.
- Gitleaks: 0 fugas en 11 commits escaneados.
- Revisión manual: no se encontró `shell=True`, ni credenciales
  embebidas, ni `eval()` / `exec()` en el código fuente.
