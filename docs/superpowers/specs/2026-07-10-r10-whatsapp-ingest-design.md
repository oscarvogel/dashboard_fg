# R10 WhatsApp Ingest API Design

## Goal

Add a small Django REST Framework API that persists WhatsApp messages captured by OpenClaw in a central database while keeping OpenClaw's local JSONL as the reliable first-write spool.

This design covers milestone `R10 - API persistencia WhatsApp OpenClaw` and issues #14 through #20. It does not create service orders, classify messages with AI, produce daily summaries, modify OpenClaw, or change existing `produccion` and `mantenimiento` behavior.

## Architecture

The backend receives normalized OpenClaw payloads through a new, isolated Django app named `forestal_bot`. The app owns its model, migration, serializer, machine-to-machine permission, views, URLs, tests, and integration README. The only changes outside that app are registering it in `INSTALLED_APPS` and including its URL namespace under `/api/forestal-bot/`.

OpenClaw writes each event to its local JSONL first. A later synchronization attempt sends the event to this API. The API is therefore a central synchronized destination, not the primary capture mechanism and not the designer of OpenClaw behavior.

## Data Model

`WhatsAppMessage` is a managed Django model in the new `forestal_bot` app. It does not inherit from or alter legacy `managed=False` models.

Fields:

- `source`, `provider`, `account_id`, `group_jid`, `group_name`, `message_id`, `sender_id`, `sender_e164`, `sender_name`, `message_type`, `media_type`, `media_path`, and `skip_reason`: string metadata. Required identity fields are enforced by the serializer; optional metadata accepts blank values.
- `timestamp`: required timezone-aware event time.
- `body`: optional text, allowing media-only messages.
- `gated_out` and `would_process_agent`: booleans defaulting to `False`.
- `raw_json`: JSON copy of the complete request payload received by the POST endpoint.
- `synced_at`: ingestion timestamp assigned when the central record is created.
- `created_at`: database record creation timestamp.

A database `UniqueConstraint` on `(account_id, group_jid, message_id)` provides the final idempotency guarantee, including concurrent ingestion attempts.

## Authentication

Both endpoints use a dedicated DRF permission and explicitly bypass the project's human JWT authentication classes. The permission accepts only this header shape:

`Authorization: Bearer <token>`

The expected token comes from `OPENCLAW_INGEST_TOKEN`. Missing configuration, a missing or malformed header, or a mismatched token denies access. Token comparison uses `secrets.compare_digest`.

## POST Ingestion

`POST /api/forestal-bot/whatsapp/messages/` validates these minimum fields:

- `account_id`
- `group_jid`
- `message_id`
- `timestamp`

The serializer permits text messages and media-only messages with an empty or absent `body`. The view copies the full incoming JSON object to `raw_json`, validates normalized fields, and performs an atomic idempotent insert keyed by the unique identity tuple.

Responses:

- New record: HTTP 201 with `created: true` and serialized message data.
- Existing record: HTTP 200 with `created: false` and the existing serialized message data. A duplicate never overwrites the original persisted payload.
- Invalid payload: HTTP 400 with DRF field errors.
- Missing or invalid Bearer token: HTTP 403 from the dedicated permission.

## Recent Audit Endpoint

`GET /api/forestal-bot/whatsapp/messages/recent/` uses the same Bearer permission and supports:

- `group_jid`: exact group filter.
- `since`: ISO-8601 timestamp; invalid values return HTTP 400.
- `limit`: positive integer, default 100, capped at 500; invalid values return HTTP 400.

Results are ordered by `timestamp` descending and then `created_at` descending. The response is a JSON list of serialized messages.

## Error Handling and Concurrency

Serializer validation handles missing required fields and invalid timestamps. Query-parameter validation is explicit and returns stable HTTP 400 responses. The POST path uses a transaction plus the database uniqueness constraint; if two requests race, the loser reloads the existing row and returns the duplicate response rather than creating a second record.

## Testing

The new app's API tests use DRF's test client, SQLite through the test runner, and an overridden `OPENCLAW_INGEST_TOKEN`. They cover:

- Missing and invalid token rejection.
- Successful authenticated creation.
- Duplicate POST returning HTTP 200 without another row.
- Media payload without `body`.
- Required-field validation.
- Recent ordering and limiting.
- Recent filtering by `group_jid` and `since`.
- Direct database uniqueness enforcement.

Project checks and the complete Django test suite run after the focused tests. No frontend dependency, build, or file is part of R10.

## Documentation and Delivery

`backend/forestal_bot/README.md` documents both endpoints, the Bearer header, `OPENCLAW_INGEST_TOKEN`, request and response examples, the JSONL-first architecture, and the rule that OpenClaw consumes rather than designs this API.

The implementation is delivered on `codex/r10-whatsapp-ingest` as a draft pull request to `main`. Its description closes issues #14, #15, #16, #17, #18, #19, and #20.
