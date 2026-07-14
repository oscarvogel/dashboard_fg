# Fuel Load Pagination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `GET /api/cargas-combustible/` return deterministic, validated pages while preserving global filtered totals and response compatibility.

**Architecture:** Keep the authenticated `APIView` and build one filtered, `select_related` queryset ordered by `fecha, id`. Validate query parameters at the boundary, aggregate and count before slicing, then serialize only the requested slice; explicit slicing naturally supports empty out-of-range pages.

**Tech Stack:** Django, Django REST Framework, SQLite-isolated Django tests, JWT authentication.

---

### Task 1: Add endpoint regression coverage

**Files:**
- Create: `backend/produccion/test_cargas_combustible_pagination.py`

- [ ] **Step 1: Write failing authentication, validation, and response-contract tests**

Create fixtures for two units, two equipment rows, two load locations, and enough loads across shared dates to exercise stable pagination. Test missing authentication, invalid/inverted dates, invalid integer filters, invalid `page`/`page_size`, capped size, empty out-of-range pages, and compatibility keys.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m pytest backend/produccion/test_cargas_combustible_pagination.py -q`

Expected: failures because the endpoint lacks pagination metadata, validation, and page slicing.

- [ ] **Step 3: Add failing pagination, filtering, totals, stable ordering, and query-count tests**

Cover different first/second page IDs, exact union with no duplicates, requested size, identical full-range totals on every page, `un_id`, `movil_id`, exact case-insensitive trimmed `patente`, `lugar_id`, nonexistent patente, same-date ID ordering, and bounded queries proving `select_related` is retained.

- [ ] **Step 4: Run the focused tests and preserve the expected RED evidence**

Run: `python -m pytest backend/produccion/test_cargas_combustible_pagination.py -q`

Expected: endpoint-behavior assertion failures, not fixture or environment errors.

### Task 2: Implement deterministic validated pagination

**Files:**
- Modify: `backend/produccion/views.py`

- [ ] **Step 1: Add minimal boundary validation**

Parse dates and reject inverted ranges. Parse positive integers for `page`, `page_size`, `un_id`, `movil_id`, and `lugar_id`; default page values and cap `page_size` at 200. Normalize `patente` with `strip()` and filter using `equipo__patente__iexact`.

- [ ] **Step 2: Aggregate before slicing and serialize one page**

Apply all filters, retain `select_related`, order by `fecha, id`, calculate `count` and grouped totals, derive `total_pages`, slice using `(page - 1) * page_size`, and return all required metadata plus `results` and `totales`.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run: `python -m pytest backend/produccion/test_cargas_combustible_pagination.py -q`

Expected: all focused tests pass.

- [ ] **Step 4: Refactor only duplicated validation while keeping tests green**

Keep any helper local and focused; do not alter unrelated endpoints or introduce global pagination.

### Task 3: Document and verify the contract

**Files:**
- Modify: `docs/COMBUSTIBLE_CONSULTAS_API.md`

- [ ] **Step 1: Document the existing endpoint contract**

Add parameters, cap behavior, exact patente matching, error codes, deterministic ordering, empty out-of-range behavior, and a shortened response example.

- [ ] **Step 2: Run repository checks**

Run:

```powershell
git diff --check
python -m pytest backend/produccion/test_cargas_combustible_pagination.py backend/produccion/test_combustible_consultas.py -q
python -m compileall backend/produccion
```

Expected: zero failures and exit code 0 for every command.

- [ ] **Step 3: Run the broader backend suite supported by the isolated settings**

Run the project test command discovered from current CI/configuration and record any environment-specific omissions explicitly.

### Task 4: Publish and validate read-only production behavior

**Files:**
- No source file changes expected.

- [ ] **Step 1: Review scope and commit implementation**

Inspect `git status -sb`, `git diff`, and stage only the view, endpoint tests, and documentation. Commit with a focused fix message.

- [ ] **Step 2: Push and open a draft PR**

Push `codex/tarea-paginacion-cargas-combustible` and open a draft PR containing objective, root cause, files, checks, compatibility, scope exclusions, and no-migration confirmation.

- [ ] **Step 3: Deploy through the repository's established production-safe flow**

Back up the live file, copy only the validated backend change, restart the service only if required by the existing deployment pattern, and verify both service and public endpoint health. Do not touch OpenClaw.

- [ ] **Step 4: Validate production without exposing credentials**

Using credentials sourced from the server environment without printing them, query `2026-06-01` through `2026-07-11` with `page_size=50`; confirm current count, page sizes, distinct hashes for pages 1-3, and exactly `count` unique IDs across every page.
