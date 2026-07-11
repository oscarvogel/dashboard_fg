# Sistema seguro de aliases de equipos

## Objetivo

Permitir que OpenClaw proponga un alias detectado en mensajes o audios, que un usuario autorizado lo confirme y que la asociación quede persistida, auditada y disponible para búsquedas futuras sin romper los consumidores actuales de `Equipo.aliases`.

## Alcance y restricciones

- El trabajo se limita al backend Django de `dashboard_fg`.
- No se modifican identificadores ni filas existentes de `moviles` de forma destructiva.
- No se borran ni reemplazan aliases existentes durante la migración o el sync inicial.
- No se cargan los aliases de prueba del equipo 208 sin una autorización posterior explícita de Oscar.
- No se ejecuta `sync_equipo_aliases --apply` en producción sin mostrar primero su `--dry-run`.
- No se utiliza un LLM en el backend.

## Fuente de verdad y compatibilidad

Se crea `EquipoAlias` como fuente de verdad durable. `Equipo.aliases`, el `JSONField` existente en `moviles`, se mantiene como representación compatible y caché visible de los aliases activos.

Toda confirmación, desactivación o escritura legacy pasa por un servicio único que actualiza `EquipoAlias` y reconstruye `Equipo.aliases` dentro de una transacción. La migración no importa ni altera datos por sí sola. El comando seguro de sincronización incorpora aliases JSON preexistentes como registros con origen `importacion`, sin sobrescribir aliases manuales.

Hasta que un valor JSON sea importado, la búsqueda lo mantiene visible como fallback compatible. Cuando existe un registro relacional activo o inactivo para la misma clave normalizada, `EquipoAlias` prevalece.

## Modelo `EquipoAlias`

Campos:

- `id`: clave primaria.
- `equipo`: FK lógica a `Equipo.id`/`moviles.idmovil`, con borrado protegido en Django y `db_constraint=False` por la clave legacy `int unsigned`.
- `alias_display`: texto legible confirmado, máximo 120 caracteres.
- `alias_normalizado`: clave normalizada, máximo 120 caracteres.
- `alias_activo_key`: clave técnica nullable; replica `alias_normalizado` cuando el registro está activo y usa `NULL` cuando está inactivo.
- `activo`: desactivación lógica; nunca se borra físicamente desde la API.
- `origen`: `manual`, `openclaw`, `importacion` o `sistema`.
- `confirmado_por`: FK al usuario autenticado; nunca se acepta desde el payload.
- `confirmado_at`: fecha efectiva de la confirmación.
- `created_at` y `updated_at`: auditoría técnica.
- `metadata`: JSON opcional, validado como objeto.

Restricciones e índices:

- unicidad por `equipo + alias_normalizado` para conservar historial idempotente;
- índice por `alias_normalizado`;
- unicidad global de `alias_activo_key`; esta forma es compatible con MySQL y permite múltiples `NULL` para conservar historial inactivo;
- si un alias inactivo se confirma nuevamente para el mismo equipo, se reactiva y actualiza su auditoría;
- si un alias activo pertenece a otro equipo, se responde HTTP 409 sin cambios.

El servicio mantiene `alias_activo_key` junto con `activo`. La restricción de base de datos complementa, pero no reemplaza, la validación transaccional. Un `IntegrityError` por concurrencia se traduce a conflicto 409.

## Normalización centralizada

Un módulo de dominio único expone dos representaciones:

- `alias_display`: Unicode NFKC, trim, espacios colapsados y guiones Unicode convertidos a `-`, conservando una forma legible.
- `alias_normalizado`: parte de `alias_display`, aplica `casefold`, elimina marcas diacríticas y elimina separadores de espacios/guiones para comparación.

Ejemplos:

- `JS 220 F`, `js220f` y `JS220F` producen `js220f`.
- `JCB Nº1` produce una clave distinta de `JCB Nº2`.
- los números de modelo y ordinales nunca se eliminan.
- un valor vacío después de normalizar se rechaza.
- más de 120 caracteres se rechazan.

La misma función se usa en confirmación, PATCH legacy, búsqueda y comando sync.

## Autorización

- Todos los endpoints de equipos y aliases usan JWT y `IsAuthenticated`.
- Búsqueda y consulta de historial: cualquier usuario autenticado.
- Confirmación y PATCH legacy: `is_staff`, `is_superuser` o permiso Django `produccion.change_equipoalias`.
- Desactivación: solo `is_staff` o `is_superuser`.
- Requests sin token devuelven 401 con la autenticación JWT configurada; credenciales autenticadas sin permiso devuelven 403.

## API de búsqueda

`GET /api/equipos/?q=<texto>` conserva `limit` y `offset`, y devuelve:

- `query` y `normalized_query`;
- `total`, `limit`, `offset` y `count`;
- `results` con `id`, `patente`, `detalle`, `modelo_normalizado`, `aliases`, `match_type` y `match_score`;
- `requires_confirmation=true` cuando existen varias coincidencias razonables.

Prioridad y puntaje determinísticos:

1. patente exacta: `1.0`;
2. alias exacto: `1.0`;
3. modelo exacto: `0.95`;
4. `codigo_fg` exacto: `0.95`;
5. coincidencias parciales en patente, alias, modelo o código: `0.8`;
6. coincidencia parcial en detalle: `0.6`.

El orden final es `match_score DESC`, `patente ASC`, `id ASC`. Cada equipo aparece una sola vez con su mejor coincidencia. La consulta precarga aliases activos para evitar N+1.

## API de confirmación e historial

### Confirmar

`POST /api/equipos/aliases/confirm/`

- valida `equipo_id`, alias, origen y metadata;
- origen admite solo los valores enumerados;
- toma confirmador y fecha del request autenticado;
- creación nueva responde 201;
- confirmación ya activa en el mismo equipo responde idempotentemente 200;
- conflicto con otro equipo responde 409 con candidatos mínimos (`equipo_id`, `patente`, `detalle`);
- equipo inexistente responde 404;
- no modifica datos si hay conflicto.

### Consultar

`GET /api/equipos/<id>/aliases/` devuelve el equipo, aliases activos y un historial mínimo que incluye registros inactivos, confirmador y fechas.

### Desactivar

`POST /api/equipos/aliases/<alias_id>/deactivate/` exige administrador, marca `activo=false`, actualiza la caché JSON y es idempotente.

## PATCH legacy

`PATCH /api/equipos/<patente>/aliases/` se conserva y se documenta como deprecated.

- `add` confirma cada alias mediante el servicio central y deja auditoría.
- `replace` conserva compatibilidad, pero desactiva lógicamente los aliases omitidos y confirma los incluidos; por su capacidad destructiva lógica se limita a `is_staff` o `is_superuser`.
- cualquier conflicto aborta toda la operación de forma atómica.
- la respuesta agrega cabeceras `Deprecation: true` y `Link` hacia el endpoint de confirmación.

## Comando `sync_equipo_aliases`

El comando es seguro, repetible y conservador:

- por defecto se comporta como `--dry-run`;
- `--dry-run` y `--apply` son mutuamente excluyentes;
- `--equipo-id` limita el alcance;
- genera candidatos desde patente, `codigo_fg`, `modelo_normalizado`, detalle completo y aliases JSON existentes;
- no fragmenta automáticamente el detalle para inventar aliases cortos ambiguos;
- aliases JSON preexistentes usan origen `importacion`; candidatos derivados usan `sistema`;
- no crea equipos, no sobrescribe aliases manuales y no desactiva registros;
- muestra altas, existentes, inválidos y conflictos antes de escribir;
- omite candidatos ambiguos o en conflicto;
- `--apply` es idempotente y opera transaccionalmente por equipo.

## Migración y backup

La migración crea únicamente la nueva tabla, índices, restricciones y permisos del modelo. No altera la estructura ni los datos de `moviles`.

Antes de migrar producción se realiza un backup MySQL con timestamp y se verifica que el archivo exista y tenga tamaño mayor que cero. Luego se muestran `showmigrations`, `migrate --plan` y el SQL de la migración antes de aplicarla.

## Pruebas y evidencia

La implementación sigue TDD y cubre los 23 casos pedidos: autenticación, permisos, normalización, creación, idempotencia, conflictos, auditoría, desactivación, búsqueda por cada campo, ambigüedad, número acotado de queries, PATCH legacy y sync dry-run/apply.

Validaciones finales:

- suite focalizada de aliases;
- suite completa de `produccion` con SQLite aislado;
- `manage.py check`;
- `makemigrations --check`;
- `showmigrations` y `migrate --plan`;
- `git diff --check` y `git diff --cached --check`;
- dry-run local del comando sin cambios de datos.

## Despliegue

El despliegue sigue el mecanismo existente de copia controlada a `/var/www/fg/produccion_api`:

1. backup con timestamp;
2. copiar solo los archivos backend aprobados;
3. checks, plan y migración;
4. reiniciar solo `produccion_api.service`;
5. verificar servicio, socket y logs;
6. probar GET autenticado, confirmación con un alias temporal controlado solo si puede limpiarse lógicamente, y requests sin token, sin imprimir el JWT;
7. no confirmar los aliases `JCB`, `JS220`, `JS220F` ni `Procesador JCB` para el equipo 208 sin una nueva autorización explícita.

## Entrega

La entrega final incluirá esquema, fuente de verdad, archivos, migración, tests, códigos HTTP, seguridad, dry-run, conflictos, rama, commits, PR, estado productivo, veredicto y un resumen listo para informar a OpenClaw.
