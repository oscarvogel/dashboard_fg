# Operator Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make operator identity consistently use `cod_operador_id` and `personal.Nombre` without changing production data or physical schema.

**Architecture:** Add a state-only Django FK, expose canonical operator fields through serializers, and replace text-based filters/distinct keys with ID-based operations. Preserve legacy response fields and use eager loading to avoid N+1 queries.

**Tech Stack:** Django 5.1, DRF 3.15, MySQL 8, Vue 3, SQLite tests.

---

### Task 1: Model and serializer contract

**Files:** `backend/produccion/models.py`, `backend/produccion/serializers.py`, `backend/produccion/test_operator_identity.py`

- [ ] Write failing tests asserting the FK metadata, legacy field preservation, canonical ID/name fields, null-safe output, and constant serializer query count.
- [ ] Run the focused test module and verify RED because `cod_operador` is absent.
- [ ] Add the FK with `db_constraint=False`, `DO_NOTHING`, and real-schema nullability; add serializer fields and eager loading.
- [ ] Re-run focused tests and confirm GREEN.

### Task 2: State-only migration

**Files:** `backend/produccion/migrations/0011_registroproduccion_cod_operador_state.py`

- [ ] Add a migration test using `sqlmigrate` expectations.
- [ ] Implement `SeparateDatabaseAndState` with an empty `database_operations` list and an `AddField` state operation.
- [ ] Verify `sqlmigrate` emits no SQL and production inspection reports the migration pending before deploy.

### Task 3: Operator endpoints and dashboard

**Files:** `backend/produccion/views.py`, `backend/produccion/test_operator_identity.py`

- [ ] Write failing API tests for ID filtering, canonical response name, object filters, duplicate legacy aliases collapsing to one person, null/orphan handling, rankings/deduplication, and old fields remaining present.
- [ ] Replace all operator identity filters, distinct lists, grouping keys, and display lookups in production dashboard paths with `cod_operador_id` / `cod_operador__nombre`.
- [ ] Add `select_related("cod_operador")` everywhere operator display is accessed and confirm query-count tests remain constant.

### Task 4: Dashboard selector compatibility

**Files:** `dashboard-frontend/src/views/DashboardView.vue`

- [ ] Add or adapt frontend tests if present; otherwise validate through a production build.
- [ ] Render operator objects with `:key="op.id"`, `:value="op.id"`, and `{{ op.nombre }}` while keeping the existing request parameter name.
- [ ] Build the Vue application and verify no other consumers assume filter strings.

### Task 5: Full validation and publication

- [ ] Run all 73+ Django tests, `manage.py check`, `makemigrations --check --dry-run`, state-only `sqlmigrate`, compileall, frontend build, and Git whitespace checks.
- [ ] Request independent code review and resolve critical/important findings.
- [ ] Commit, push, and open a draft PR based on `codex/tarea-endpoints-consulta-combustible`.

### Task 6: Production deployment

- [ ] Confirm the verified SQL dump backup and create timestamped file backups before replacement.
- [ ] Upload only scoped backend/frontend artifacts, inspect migration plan, apply the state-only migration, and prove no physical DDL occurred.
- [ ] Restart only `produccion_api.service`, verify logs, and smoke authenticated filters/dashboard/operator endpoints plus unauthenticated behavior.
- [ ] Verify a real `PROCE-Nº3` response identifies one operator by `personal.Nombre`, without printing credentials or tokens.
