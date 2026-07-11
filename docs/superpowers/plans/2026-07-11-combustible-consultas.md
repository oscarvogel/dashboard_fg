# Fuel Query Endpoints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add, validate, document, and deploy three authenticated read-only fuel analytics endpoints without changing the production schema or existing endpoint responses.

**Architecture:** Put request validation and Decimal-based aggregation in a focused `combustible_services.py` module. The three DRF `APIView` classes remain thin adapters, use the existing `CargaCombustible.equipo_id` / `RegistroProduccion.cod_equipo_id` relationship, and execute independent aggregate queries so fuel and production rows cannot multiply each other through joins.

**Tech Stack:** Django 5.1, Django REST Framework 3.15, Django ORM, SimpleJWT, MySQL production, SQLite isolated tests.

---

### Task 1: Lock down request validation and calculation rules

**Files:**
- Create: `backend/produccion/test_combustible_consultas.py`
- Create: `backend/produccion/combustible_services.py`

- [ ] Write serializer/service tests for required `inicio` and `fin`, strict ISO dates, inverted ranges, `MAX_RANGE_DAYS = 366`, positive integer `un_id`/`movil_id`, and `meses_atras` defaulting to 6.
- [ ] Run `py -3.12 backend/manage.py test produccion.tests.test_combustible_consultas --settings=produccion_api.test_settings -v 2` and confirm the tests fail because the validation service does not exist.
- [ ] Implement `parse_consulta_params(query_params, include_history=False)` using DRF serializers, plus configurable constants `MAX_RANGE_DAYS`, `DEFAULT_MESES_ATRAS`, `SEMAFORO_VERDE_MAX_PCT = Decimal("5")`, and `SEMAFORO_AMARILLO_MAX_PCT = Decimal("15")`.
- [ ] Re-run the focused tests and confirm they pass.

### Task 2: Implement per-equipment fuel and production aggregation

**Files:**
- Modify: `backend/produccion/test_combustible_consultas.py`
- Modify: `backend/produccion/combustible_services.py`

- [ ] Add failing tests for egresos only, a production-only equipment, zero/negative hour records, multiple loads without multiplication, `un_id`/`movil_id`, totals, warnings, and a bounded query count.
- [ ] Confirm RED with the focused Django test command.
- [ ] Implement separate ORM aggregates keyed by real equipment IDs. Fuel is `Sum(litros)` over `tipo_mov="E"`; valid hours are the sum of each row's `hr_fin - hr_inicio` only when `hr_fin > hr_inicio`; zero/negative intervals are excluded and reported. Use `Decimal` until response rendering and load equipment/unit labels in one query.
- [ ] Confirm GREEN and refactor shared mapping/rounding helpers without changing behavior.

### Task 3: Expose `GET /api/combustible-equipo-lh/`

**Files:**
- Modify: `backend/produccion/test_combustible_consultas.py`
- Modify: `backend/produccion/views.py`
- Modify: `backend/produccion/urls.py`

- [ ] Add failing API tests for JWT-authenticated success, unauthenticated 401, invalid requests 400, filters, response fields, and production-only equipment behavior.
- [ ] Add `CombustibleEquipoLHView` with `IsAuthenticated`, delegate to the service, and register the route.
- [ ] Run the focused suite and confirm all endpoint tests pass.

### Task 4: Expose historical comparison

**Files:**
- Modify: `backend/produccion/test_combustible_consultas.py`
- Modify: `backend/produccion/combustible_services.py`
- Modify: `backend/produccion/views.py`
- Modify: `backend/produccion/urls.py`

- [ ] Add failing tests for equivalent periods shifted with `relativedelta(months=meses_atras)`, missing history, zero historical hours/base, absolute and percentage differences, configurable green/yellow/red thresholds, filters, and query bounds.
- [ ] Implement `comparar_equipo_vs_historico`: percentage is `(actual_lh - historico_lh) / historico_lh * 100`; do not compute it for null/zero history; use `verde <= +5%`, `amarillo <= +15%`, `rojo > +15%`, otherwise `sin_datos`.
- [ ] Add `CombustibleEquipoVsHistoricoView`, register `/api/combustible-equipo-vs-historico/`, and confirm GREEN.

### Task 5: Detect fuel without compatible production

**Files:**
- Modify: `backend/produccion/test_combustible_consultas.py`
- Modify: `backend/produccion/combustible_services.py`
- Modify: `backend/produccion/views.py`
- Modify: `backend/produccion/urls.py`

- [ ] Add failing tests for same local `DateField` match, fuel without production, multiple same-day loads grouped once, production on an adjacent day, filters, and query bounds.
- [ ] Implement grouped egresos by `fecha` and `equipo_id`, compare against a set of `(fecha, cod_equipo_id)` production keys, and return review-only wording. Report orphan/null equipment IDs separately in `data_quality` if legacy rows exist.
- [ ] Add `CombustibleSinProduccionView`, register `/api/combustible-sin-produccion/`, and confirm GREEN.

### Task 6: Document the API and operational limitations

**Files:**
- Create: `docs/COMBUSTIBLE_CONSULTAS_API.md`
- Modify: `README.md`

- [ ] Document all parameters, 200 examples, formulas, thresholds as initial configurable values, 400/401/403/404 behavior, 366-day maximum, DateField/local-date behavior, and the limitation for next-day/cross-shift production.
- [ ] Explain that zero/negative intervals are excluded, no percentage is produced from null/zero history, and findings are review signals—not evidence of fraud or definitive error.
- [ ] Run `git diff --check`.

### Task 7: Full local validation and migration inspection

**Files:**
- Inspect only: all modified files and Django migration state

- [ ] Run `py -3.12 backend/manage.py test produccion --settings=produccion_api.test_settings -v 2`.
- [ ] Run `py -3.12 backend/manage.py check --settings=produccion_api.test_settings`.
- [ ] Run `py -3.12 backend/manage.py makemigrations --check --dry-run --settings=produccion_api.test_settings` and confirm no migration is required.
- [ ] Run `py -3.12 -m compileall backend/produccion backend/produccion_api` and both `git diff --check` / `git diff --cached --check` as applicable.
- [ ] Review `git diff origin/main...HEAD` requirement by requirement and do not deploy if any validation fails.

### Task 8: Publish a draft PR

**Files:**
- Stage only the scoped backend tests/code/docs.

- [ ] Commit the validated change with an explicit fuel-query message.
- [ ] Push `codex/tarea-endpoints-consulta-combustible`.
- [ ] Open a draft PR describing formulas, validations, no migration, evidence, scope exclusions, and deployment risk.

### Task 9: Back up and deploy only the backend

**Production target:** `dattaweb:/var/www/fg/produccion_api`; service `produccion_api.service`; API listener `api.fgsa.ar:8088`.

- [ ] Inspect live paths/service and create a timestamped server-side backup of every file to be replaced before copying anything.
- [ ] Upload only the changed backend Python files; do not touch Nginx, Kobo, the frontend, or production data.
- [ ] Run production `manage.py check` and `showmigrations --plan` in inspection mode; apply no migrations because this design changes no models.
- [ ] Restart only `produccion_api.service`, verify its status and recent logs.
- [ ] Obtain authentication without printing the token, call all three endpoints with a small representative date range, record HTTP status and sanitized response shape, then call one endpoint without authentication and confirm 401/403.
- [ ] If any smoke fails, restore the timestamped files, restart only `produccion_api.service`, and report the rollback evidence.

### Task 10: Final completion audit

- [ ] Match each numbered requirement in the supplied scope to tests, source, documentation, local command output, and production smoke evidence.
- [ ] Report modified files, exact formulas, test counts, migration result, production HTTP codes, sanitized examples, limitations, commit/branch/PR, and final `OK` or `FALLA` verdict.
