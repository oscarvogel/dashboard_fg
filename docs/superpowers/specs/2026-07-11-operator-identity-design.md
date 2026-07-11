# Operator Identity Design

## Objective

Use `tablero_produccion.cod_operador` as the only operator identity and `personal.Nombre` as the display name, while retaining the legacy `tablero_produccion.operador` text for compatibility and diagnostics.

## Confirmed production schema

- `tablero_produccion.cod_operador`: `INT NOT NULL DEFAULT 1`.
- `cod_operador` has no index and no physical foreign-key constraint.
- `personal.idPersonal`: `INT UNSIGNED NOT NULL AUTO_INCREMENT`, primary key.
- `personal.Nombre`: `VARCHAR(80) NOT NULL`.

The ORM relation therefore uses `null=False`, `blank=False`, `db_constraint=False`, and `on_delete=DO_NOTHING`. No physical database column, index, or constraint will be created or renamed.

## ORM and migration

`RegistroProduccion.cod_operador` becomes a `ForeignKey` to `Empleado` with `db_column="cod_operador"`. A `SeparateDatabaseAndState` migration records the relationship in Django state while `database_operations` remains empty. The existing `operador` field stays unchanged and is documented as legacy text.

## API behavior

`RegistroProduccionSerializer` retains `operador` and adds:

- `operador_id`, sourced from `cod_operador_id`.
- `operador_nombre`, sourced from `cod_operador.nombre`.
- `operador_texto_legacy`, sourced from `operador` for diagnosis.

Querysets that serialize or display operators use `select_related("cod_operador")`. Orphan or missing relations serialize with null ID/name without fuzzy matching.

`ProduccionOperadorView` accepts the existing `operador` parameter for compatibility plus the explicit `operador_id`; both are interpreted as an integer ID and filter `cod_operador_id` only. Dashboard filtering changes from legacy text matching to operator ID equality.

Operator filters return `{ "id": idPersonal, "nombre": personal.Nombre }`. Rankings, distinct lists, and machine/front/operator deduplication key by `cod_operador_id`, never legacy text.

## Frontend compatibility

The dashboard operator selector consumes objects, displays `nombre`, and sends `id`. Existing record field `operador` remains available, so report columns and older consumers do not break.

## Testing and deployment

Tests cover differing legacy strings for one operator, the confirmed ANZUATE aliases, missing/orphan relations, serializer fields, ID filtering, ID-based ranking/deduplication, existing response fields, and constant query counts. Deployment copies files after a timestamped file backup, applies the state-only migration with no SQL, restarts only `produccion_api.service`, builds/publishes frontend only if the selector change requires it, and smokes authenticated production endpoints without printing credentials.

## Branch dependency

This work is stacked on `codex/tarea-endpoints-consulta-combustible` because PR #31 is already running in production. Its PR must initially target that branch; after #31 merges, the operator PR can be rebased or retargeted to `main`.
