# Secure Equipment Aliases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar confirmación autenticada, persistente, auditable y conflict-safe de aliases de equipos, manteniendo `Equipo.aliases` como caché compatible y sin cargar aliases del equipo 208.

**Architecture:** `EquipoAlias` será la fuente de verdad relacional y un servicio transaccional concentrará normalización, confirmación, conflicto, desactivación y sincronización del JSON compatible. Las vistas DRF y el comando de gestión delegarán en ese servicio, con permisos separados para lectura, escritura y administración.

**Tech Stack:** Python 3.12, Django 5.1, Django REST Framework 3.15, SimpleJWT, SQLite para tests aislados, MySQL en producción.

---

## Mapa de archivos

- Crear `backend/produccion/equipo_aliases.py`: normalización, candidatos de búsqueda, permisos y servicios transaccionales.
- Crear `backend/produccion/test_equipo_aliases.py`: pruebas unitarias, API, concurrencia lógica, queries y compatibilidad.
- Crear `backend/produccion/migrations/0012_equipoalias.py`: tabla, índices, constraints y permiso de modelo.
- Crear `backend/produccion/management/commands/sync_equipo_aliases.py`: inventario/dry-run/apply idempotente.
- Crear `backend/produccion/test_sync_equipo_aliases.py`: pruebas del comando.
- Modificar `backend/produccion/models.py`: modelo `EquipoAlias`.
- Modificar `backend/produccion/serializers.py`: validación de payloads y serialización de auditoría.
- Modificar `backend/produccion/views.py`: búsqueda segura y endpoints de aliases.
- Modificar `backend/produccion/urls.py`: rutas nuevas y legacy.
- Modificar `backend/produccion/admin.py`: inspección segura del historial.
- Modificar `backend/README.md` o crear `docs/EQUIPO_ALIASES_API.md`: contrato, permisos, fuente de verdad, sync y ejemplos para OpenClaw.

### Task 1: Normalización centralizada

**Files:**
- Create: `backend/produccion/equipo_aliases.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED de normalización**

Crear `EquipoAliasNormalizationTests` con casos exactos:

```python
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .equipo_aliases import normalize_alias


class EquipoAliasNormalizationTests(SimpleTestCase):
    def test_equivalent_model_spellings_share_key(self):
        keys = {normalize_alias(value).normalized for value in ("JS 220 F", "js220f", "JS220F")}
        self.assertEqual(keys, {"js220f"})

    def test_preserves_distinct_ordinal_numbers(self):
        self.assertNotEqual(normalize_alias("JCB Nº1").normalized, normalize_alias("JCB Nº2").normalized)

    def test_collapses_spaces_accents_and_unicode_dashes(self):
        normalized = normalize_alias("  Procesadór\u2013 JCB  ")
        self.assertEqual(normalized.display, "Procesadór- JCB")
        self.assertEqual(normalized.normalized, "procesadorjcb")

    def test_rejects_empty_and_overlong_alias(self):
        with self.assertRaises(ValidationError):
            normalize_alias("   ")
        with self.assertRaises(ValidationError):
            normalize_alias("x" * 121)
```

- [ ] **Step 2: Ejecutar RED**

Run:

```powershell
$env:DJANGO_SETTINGS_MODULE='produccion_api.test_settings'
$env:SECRET_KEY='test-only-secret-key'
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasNormalizationTests -v 2
```

Expected: FAIL porque `produccion.equipo_aliases` no existe.

- [ ] **Step 3: Implementar lo mínimo**

Crear un dataclass `NormalizedAlias(display, normalized)`, `MAX_ALIAS_LENGTH = 120`, tabla de guiones Unicode, NFKC, trim/espacios, NFKD para quitar diacríticos, `casefold()` y eliminación exclusiva de espacios/guiones. Lanzar `ValidationError` con mensajes estables.

- [ ] **Step 4: Ejecutar GREEN**

Run: el mismo comando del Step 2.

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/produccion/equipo_aliases.py backend/produccion/test_equipo_aliases.py
git commit -m "feat(api): centralize equipment alias normalization"
```

### Task 2: Modelo relacional y migración segura

**Files:**
- Modify: `backend/produccion/models.py`
- Create: `backend/produccion/migrations/0012_equipoalias.py`
- Modify: `backend/produccion/admin.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED del modelo**

Agregar tests que creen `EquipoAlias`, verifiquen FK a `Equipo`, choices, timestamps, metadata, unique por equipo+normalizado y unique condicional global activo. Probar que el mismo alias normalizado inactivo puede existir históricamente en equipos distintos pero no puede haber dos activos.

- [ ] **Step 2: Ejecutar RED**

Run:

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasModelTests -v 2
```

Expected: FAIL por import inexistente.

- [ ] **Step 3: Implementar modelo y migración**

Definir `EquipoAlias` con `on_delete=PROTECT`, `related_name='alias_records'`, campos de la especificación, `UniqueConstraint(fields=['equipo', 'alias_normalizado'])`, `UniqueConstraint(fields=['alias_normalizado'], condition=Q(activo=True))` e índice explícito. Registrar un admin read-oriented con filtros por activo/origen y búsqueda por alias/equipo.

Generar migración:

```powershell
.\.venv\Scripts\python.exe manage.py makemigrations produccion --name equipoalias
```

Revisar que solo cree `EquipoAlias` y no altere `moviles`.

- [ ] **Step 4: Ejecutar GREEN y revisar SQL**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasModelTests -v 2
.\.venv\Scripts\python.exe manage.py sqlmigrate produccion 0012
```

Expected: tests PASS; SQL contiene creación de tabla/índices y ninguna sentencia `ALTER TABLE moviles`.

- [ ] **Step 5: Commit**

```powershell
git add backend/produccion/models.py backend/produccion/admin.py backend/produccion/migrations/0012_equipoalias.py backend/produccion/test_equipo_aliases.py
git commit -m "feat(api): add audited equipment alias model"
```

### Task 3: Servicio transaccional, conflictos y caché JSON

**Files:**
- Modify: `backend/produccion/equipo_aliases.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED del servicio**

Cubrir creación, idempotencia, reactivación, alias vacío/largo, mismo equipo, conflicto con otro equipo, auditoría de usuario/fecha, metadata, origen inválido, desactivación lógica y reconstrucción determinística de `Equipo.aliases` sin duplicados.

- [ ] **Step 2: Ejecutar RED**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasServiceTests -v 2
```

Expected: FAIL por servicios inexistentes.

- [ ] **Step 3: Implementar servicio mínimo**

Agregar:

- `AliasConflict` con candidatos mínimos;
- `confirm_equipo_alias(*, equipo, alias, origen, confirmado_por, metadata)`;
- `deactivate_equipo_alias(*, alias_record)`;
- `sync_equipo_alias_cache(equipo_id)`;
- `get_alias_conflicts(normalized, exclude_equipo_id=None)`.

Usar `transaction.atomic()`, `select_for_update()`, `IntegrityError` traducido a conflicto, `timezone.now()` y orden por `alias_display`, `id` para el JSON.

- [ ] **Step 4: Ejecutar GREEN**

Run: comando del Step 2.

Expected: tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/produccion/equipo_aliases.py backend/produccion/test_equipo_aliases.py
git commit -m "feat(api): confirm equipment aliases transactionally"
```

### Task 4: Permisos y serializers

**Files:**
- Modify: `backend/produccion/equipo_aliases.py`
- Modify: `backend/produccion/serializers.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED**

Probar `CanManageEquipoAliases`: autoriza `is_staff`, `is_superuser` o `has_perm('produccion.change_equipoalias')`; rechaza autenticado común. Probar `IsEquipoAliasAdmin`: solo staff/superuser. Validar que serializers ignoran/rechazan `confirmado_por`, exigen `equipo_id`/`alias`, limitan origen y requieren metadata objeto.

- [ ] **Step 2: Ejecutar RED**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasPermissionTests produccion.test_equipo_aliases.EquipoAliasSerializerTests -v 2
```

Expected: FAIL por clases inexistentes.

- [ ] **Step 3: Implementar permisos y serializers mínimos**

Crear permisos DRF y serializers `EquipoAliasConfirmSerializer`, `EquipoAliasSerializer` y `EquipoAliasHistorySerializer`. No exponer campos mutables de identidad/auditoría como input.

- [ ] **Step 4: Ejecutar GREEN y commit**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasPermissionTests produccion.test_equipo_aliases.EquipoAliasSerializerTests -v 2
git add backend/produccion/equipo_aliases.py backend/produccion/serializers.py backend/produccion/test_equipo_aliases.py
git commit -m "feat(api): enforce equipment alias permissions"
```

### Task 5: Endpoint de confirmación, historial y desactivación

**Files:**
- Modify: `backend/produccion/views.py`
- Modify: `backend/produccion/urls.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests API RED**

Cubrir confirm sin token 401, usuario común 403, administrador/permisado autorizado, 201, 200 idempotente, 400 vacío/largo, 404 equipo, 409 conflicto/candidatos, auditoría derivada de `request.user`, GET historial autenticado y desactivación admin/idempotente.

- [ ] **Step 2: Ejecutar RED**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasApiTests -v 2
```

Expected: FAIL por rutas 404.

- [ ] **Step 3: Implementar vistas y rutas**

Agregar `EquipoAliasConfirmView`, `EquipoAliasHistoryView` y `EquipoAliasDeactivateView`. Mapear errores a 400/404/409 y serializar confirmador como `{id, nombre}` usando `get_full_name() or username`.

- [ ] **Step 4: Ejecutar GREEN y commit**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasApiTests -v 2
git add backend/produccion/views.py backend/produccion/urls.py backend/produccion/test_equipo_aliases.py
git commit -m "feat(api): expose audited alias confirmation endpoints"
```

### Task 6: Búsqueda autenticada, ranking y N+1

**Files:**
- Modify: `backend/produccion/views.py`
- Modify: `backend/produccion/equipo_aliases.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED de búsqueda**

Cubrir GET sin token, patente, detalle, modelo, alias, equivalencia `JS 220 F`, prioridad exacta/parcial, orden estable, `match_type`, `match_score`, `requires_confirmation`, aliases activos solamente y número constante/acotado de queries con uno y varios equipos.

- [ ] **Step 2: Ejecutar RED**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoSearchApiTests -v 2
```

Expected: FAIL porque el endpoint permite anónimos y carece del contrato nuevo.

- [ ] **Step 3: Implementar ranking mínimo**

Cambiar a `IsAuthenticated`, cargar equipos con `prefetch_related(Prefetch('alias_records', queryset=EquipoAlias.objects.filter(activo=True)))`, evaluar cada campo con normalización centralizada, conservar paginación y ordenar por score/patente/id.

- [ ] **Step 4: Ejecutar GREEN y commit**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoSearchApiTests -v 2
git add backend/produccion/views.py backend/produccion/equipo_aliases.py backend/produccion/test_equipo_aliases.py
git commit -m "feat(api): rank authenticated equipment searches"
```

### Task 7: Compatibilidad del PATCH legacy

**Files:**
- Modify: `backend/produccion/views.py`
- Test: `backend/produccion/test_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED legacy**

Cubrir no token 401, común 403, `add` auditado, idempotencia, conflicto atómico, `replace` solo admin, desactivación lógica de omitidos, headers deprecados y no reemplazo físico del historial.

- [ ] **Step 2: Ejecutar RED**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasLegacyPatchTests -v 2
```

Expected: FAIL por `AllowAny` y escritura JSON directa.

- [ ] **Step 3: Refactorizar PATCH al servicio central**

Aplicar permisos, envolver lista completa en `transaction.atomic`, confirmar cada alias con origen manual y, para replace administrativo, desactivar los no incluidos. Agregar `Deprecation` y `Link`.

- [ ] **Step 4: Ejecutar GREEN y commit**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases.EquipoAliasLegacyPatchTests -v 2
git add backend/produccion/views.py backend/produccion/test_equipo_aliases.py
git commit -m "fix(api): secure legacy equipment alias patch"
```

### Task 8: Comando seguro de población inicial

**Files:**
- Create: `backend/produccion/management/commands/sync_equipo_aliases.py`
- Create: `backend/produccion/test_sync_equipo_aliases.py`

- [ ] **Step 1: Escribir tests RED del comando**

Usar `call_command` y `CapturedQueriesContext`/snapshots de filas para probar: default dry-run no modifica, `--dry-run`, `--equipo-id`, equipo inexistente, flags excluyentes, candidatos de los cinco campos, conflictos visibles y omitidos, JSON existente como importación, `--apply` idempotente y no sobrescritura/desactivación manual.

- [ ] **Step 2: Ejecutar RED**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_sync_equipo_aliases -v 2
```

Expected: FAIL por comando inexistente.

- [ ] **Step 3: Implementar comando mínimo**

Crear dataclasses de resultado, generación determinística, resumen por categorías y escritura por equipo usando el servicio. Exigir usuario de sistema para `confirmado_por`: resolver `--confirmed-by-user-id` en apply y rechazar apply sin usuario existente, de modo que nunca se invente identidad. Dry-run no requiere usuario.

- [ ] **Step 4: Ejecutar GREEN y commit**

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_sync_equipo_aliases -v 2
git add backend/produccion/management/commands/sync_equipo_aliases.py backend/produccion/test_sync_equipo_aliases.py
git commit -m "feat(api): add safe equipment alias sync command"
```

### Task 9: Documentación operativa y contrato OpenClaw

**Files:**
- Create: `docs/EQUIPO_ALIASES_API.md`

- [ ] **Step 1: Documentar contrato exacto**

Incluir JWT sin secretos, permisos, endpoints, payload/respuestas, 200/201/400/401/403/404/409, normalización, fuente de verdad, PATCH deprecated, comando dry-run/apply y prohibición vigente sobre equipo 208.

- [ ] **Step 2: Validar documentación y commit**

```powershell
rg -n "AllowAny|token real" docs/EQUIPO_ALIASES_API.md
git diff --check
git add docs/EQUIPO_ALIASES_API.md
git commit -m "docs: document equipment alias API for OpenClaw"
```

Expected: sin secretos, placeholders ni errores de whitespace.

### Task 10: Verificación integral local

**Files:**
- Review all modified files.

- [ ] **Step 1: Ejecutar suite focalizada y completa**

```powershell
$env:DJANGO_SETTINGS_MODULE='produccion_api.test_settings'
$env:SECRET_KEY='test-only-secret-key'
$env:OPENCLAW_INGEST_TOKEN='test-token'
.\.venv\Scripts\python.exe manage.py test produccion.test_equipo_aliases produccion.test_sync_equipo_aliases -v 2
.\.venv\Scripts\python.exe manage.py test produccion -v 1
```

Expected: todos PASS.

- [ ] **Step 2: Ejecutar checks de Django y migración**

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
.\.venv\Scripts\python.exe manage.py showmigrations produccion
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py sqlmigrate produccion 0012
```

Expected: check sin errores, ninguna migración faltante y plan limitado a `EquipoAlias`.

- [ ] **Step 3: Probar dry-run sobre fixture local sin escrituras**

Crear un equipo local controlado con patente `ALIAS-DRY-RUN`, capturar su ID y los conteos antes/después, y ejecutar el comando mediante `call_command` desde un test de integración. Ejecutar además el test exacto:

```powershell
.\.venv\Scripts\python.exe manage.py test produccion.test_sync_equipo_aliases.SyncEquipoAliasesCommandTests.test_dry_run_for_one_equipment_does_not_write -v 2
```

Expected: muestra candidatos; `EquipoAlias` y `Equipo.aliases` permanecen iguales.

- [ ] **Step 4: Checks Git y revisión de alcance**

```powershell
git diff --check main...HEAD
git status -sb
git diff --stat main...HEAD
git diff main...HEAD -- backend/produccion docs
```

Confirmar que no hay frontend, secretos, datos productivos ni aliases del equipo 208.

### Task 11: PR draft y revisión

**Files:**
- No source changes unless review finds a real defect.

- [ ] **Step 1: Push y abrir PR draft**

```powershell
git push -u origin codex/tarea-aliases-equipos-seguros
gh pr create --draft --base main --head codex/tarea-aliases-equipos-seguros --title "feat(api): secure audited equipment aliases" --body-file "$env:TEMP\dashboard-fg-equipo-aliases-pr.md"
```

El body incluye objetivo, cambios, tests, migración, evidencia, fuera de alcance, riesgos y `No se cargaron aliases del equipo 208`.

- [ ] **Step 2: Revisar diff y checks del PR**

Revisar cada archivo contra la especificación, esperar checks, corregir solo defectos reales con TDD y repetir Task 10. Pasar a ready únicamente con todo verde.

### Task 12: Backup y despliegue productivo seguro

**Files:**
- Runtime copy only after PR review.

- [ ] **Step 1: Inventariar producción sin mutar**

Confirmar host, `/var/www/fg/produccion_api`, servicio/socket, migraciones, esquema real de `moviles`, existencia/forma de `aliases`, distribución de `codigo_fg` y `modelo_normalizado`, usuarios/permisos y equipo 208. No imprimir secretos.

- [ ] **Step 2: Backup con timestamp**

Crear dump MySQL y tar del runtime, verificar existencia/tamaño y registrar rutas. Detener si falla.

- [ ] **Step 3: Dry-run productivo antes de aplicar**

Copiar el código a staging/runtime según el mecanismo existente, ejecutar checks, `showmigrations`, `migrate --plan` y `sync_equipo_aliases --dry-run`. Capturar conflictos y conteos. No ejecutar `--apply`.

- [ ] **Step 4: Migrar y reiniciar solo el backend**

Aplicar `0012`, reiniciar únicamente `produccion_api.service`, verificar `active`, socket y logs sin nuevos traceback.

- [ ] **Step 5: Smokes seguros**

Sin imprimir JWT: GET sin token 401; POST confirm sin token 401; GET con token 200; usuario sin permiso 403 si existe identidad controlada. La confirmación autenticada se prueba solo con un alias temporal expresamente seguro y se desactiva; si no hay identidad/dato seguro, se omite y se reporta. Nunca confirmar los cuatro aliases del equipo 208.

- [ ] **Step 6: Reporte final y handoff OpenClaw**

Informar esquema, fuente de verdad, archivos, migración, tests, HTTP, seguridad, dry-run, conflictos, rama, commits, PR, backups, deploy, logs, smokes, estado local y veredicto. Entregar bloque listo para copiar al bot con endpoint confirm, contrato de ambigüedad y regla de no inventar asociaciones.
