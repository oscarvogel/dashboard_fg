# R10 WhatsApp Ingest API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an authenticated, idempotent Django/DRF API that centrally persists OpenClaw WhatsApp messages and exposes a recent-message audit endpoint.

**Architecture:** A new isolated `forestal_bot` Django app owns the managed message model, serializer, Bearer permission, API views, URLs, migration, tests, and integration README. The project only registers the app and its route; the existing frontend, `produccion`, `mantenimiento`, OpenClaw, and legacy models remain unchanged.

**Tech Stack:** Python 3.12, Django 5.1, Django REST Framework 3.15, Django test runner, SQLite for local tests, MySQL-compatible Django migrations.

---

### Task 1: Scaffold the app and define the persistence contract

**Files:**
- Create: `backend/forestal_bot/__init__.py`
- Create: `backend/forestal_bot/apps.py`
- Create: `backend/forestal_bot/models.py`
- Create: `backend/forestal_bot/migrations/__init__.py`
- Create: `backend/forestal_bot/tests/__init__.py`
- Create: `backend/forestal_bot/tests/test_models.py`
- Modify: `backend/produccion_api/settings.py`
- Create: `backend/forestal_bot/migrations/0001_initial.py` with `makemigrations`

- [ ] **Step 1: Write the failing model tests**

```python
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from forestal_bot.models import WhatsAppMessage


class WhatsAppMessageModelTests(TestCase):
    def payload(self, **overrides):
        values = {
            "account_id": "forestal",
            "group_jid": "120363@example.g.us",
            "message_id": "wamid-1",
            "timestamp": timezone.now(),
            "message_type": "text",
            "body": "Equipo detenido",
            "raw_json": {"message_id": "wamid-1"},
        }
        values.update(overrides)
        return values

    def test_media_message_allows_blank_body(self):
        message = WhatsAppMessage.objects.create(
            **self.payload(message_type="image", body="", media_type="image/jpeg")
        )
        self.assertEqual(message.body, "")

    def test_identity_tuple_is_unique(self):
        WhatsAppMessage.objects.create(**self.payload())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WhatsAppMessage.objects.create(**self.payload(body="duplicate"))
        self.assertEqual(WhatsAppMessage.objects.count(), 1)
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run from the repository root:

```powershell
$env:SECRET_KEY='r10-test-key'
$env:DATABASE_URL='sqlite:///r10-tests.sqlite3'
.\.venv\Scripts\python.exe backend\manage.py test forestal_bot.tests.test_models -v 2
```

Expected: failure because `forestal_bot` does not exist or is not installed.

- [ ] **Step 3: Create the minimal app and model**

`backend/forestal_bot/apps.py`:

```python
from django.apps import AppConfig


class ForestalBotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forestal_bot"
```

`backend/forestal_bot/models.py`:

```python
from django.db import models


class WhatsAppMessage(models.Model):
    source = models.CharField(max_length=50, blank=True, default="")
    provider = models.CharField(max_length=50, blank=True, default="")
    account_id = models.CharField(max_length=255)
    group_jid = models.CharField(max_length=255)
    group_name = models.CharField(max_length=255, blank=True, default="")
    message_id = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    sender_id = models.CharField(max_length=255, blank=True, default="")
    sender_e164 = models.CharField(max_length=50, blank=True, default="")
    sender_name = models.CharField(max_length=255, blank=True, default="")
    message_type = models.CharField(max_length=50, blank=True, default="text")
    body = models.TextField(blank=True, default="")
    media_type = models.CharField(max_length=100, blank=True, default="")
    media_path = models.TextField(blank=True, default="")
    gated_out = models.BooleanField(default=False)
    would_process_agent = models.BooleanField(default=False)
    skip_reason = models.CharField(max_length=255, blank=True, default="")
    raw_json = models.JSONField(default=dict)
    synced_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["account_id", "group_jid", "message_id"],
                name="forestal_bot_whatsapp_message_identity_uniq",
            )
        ]
```

Add `"forestal_bot",` after `"mantenimiento",` in `INSTALLED_APPS`. Create empty package files and generate the migration:

```powershell
$env:SECRET_KEY='r10-test-key'
$env:DATABASE_URL='sqlite:///r10-tests.sqlite3'
.\.venv\Scripts\python.exe backend\manage.py makemigrations forestal_bot
```

- [ ] **Step 4: Run the model tests and confirm GREEN**

Run the command from Step 2. Expected: 2 tests pass.

- [ ] **Step 5: Commit the persistence layer**

```powershell
git add backend/forestal_bot backend/produccion_api/settings.py
git commit -m "feat(forestal-bot): add WhatsApp message model"
```

### Task 2: Add dedicated Bearer authentication and POST ingestion

**Files:**
- Create: `backend/forestal_bot/permissions.py`
- Create: `backend/forestal_bot/serializers.py`
- Create: `backend/forestal_bot/views.py`
- Create: `backend/forestal_bot/urls.py`
- Create: `backend/forestal_bot/tests/test_api.py`
- Modify: `backend/produccion_api/urls.py`

- [ ] **Step 1: Write failing API authentication and creation tests**

Create a DRF `APITestCase` with `@override_settings(OPENCLAW_INGEST_TOKEN="test-openclaw-token")`, `self.url = reverse("forestal_bot:whatsapp-message-list")`, a valid payload containing the four required fields, and these assertions:

```python
def test_post_without_token_is_rejected(self):
    response = self.client.post(self.url, self.payload(), format="json")
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

def test_post_with_invalid_token_is_rejected(self):
    self.client.credentials(HTTP_AUTHORIZATION="Bearer wrong")
    response = self.client.post(self.url, self.payload(), format="json")
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

def test_post_with_valid_token_creates_message(self):
    self.authenticate()
    payload = self.payload()
    response = self.client.post(self.url, payload, format="json")
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertTrue(response.data["created"])
    message = WhatsAppMessage.objects.get()
    self.assertEqual(message.raw_json, payload)

def test_post_requires_identity_and_timestamp(self):
    self.authenticate()
    response = self.client.post(self.url, {}, format="json")
    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertEqual(set(response.data), {"account_id", "group_jid", "message_id", "timestamp"})
```

- [ ] **Step 2: Run the new API tests and confirm RED**

```powershell
.\.venv\Scripts\python.exe backend\manage.py test forestal_bot.tests.test_api -v 2
```

Expected: URL reversal/import failure because permission, serializer, views, and URLs do not exist.

- [ ] **Step 3: Implement Bearer permission, serializer, route, and POST view**

`permissions.py` reads `settings.OPENCLAW_INGEST_TOKEN`, requires exactly two authorization parts with scheme `Bearer`, and uses `secrets.compare_digest`.

`serializers.py` defines a `ModelSerializer` exposing every model field while marking `id`, `raw_json`, `synced_at`, and `created_at` read-only.

`views.py` defines `WhatsAppMessageCreateView(APIView)` with:

```python
authentication_classes = []
permission_classes = [OpenClawBearerPermission]

def post(self, request):
    raw_json = dict(request.data)
    serializer = WhatsAppMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data
    identity = {
        "account_id": validated["account_id"],
        "group_jid": validated["group_jid"],
        "message_id": validated["message_id"],
    }
    defaults = {**validated, "raw_json": raw_json}
    for key in identity:
        defaults.pop(key, None)
    try:
        with transaction.atomic():
            message, created = WhatsAppMessage.objects.get_or_create(
                **identity, defaults=defaults
            )
    except IntegrityError:
        message = WhatsAppMessage.objects.get(**identity)
        created = False
    output = WhatsAppMessageSerializer(message).data
    return Response(
        {"created": created, "message": output},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )
```

Register `whatsapp/messages/` as `whatsapp-message-list` in namespaced app URLs and add this exact project route:

```python
path("api/forestal-bot/", include("forestal_bot.urls")),
```

- [ ] **Step 4: Run API and model tests and confirm GREEN**

```powershell
.\.venv\Scripts\python.exe backend\manage.py test forestal_bot.tests -v 2
```

Expected: authentication, validation, creation, and model tests pass.

- [ ] **Step 5: Commit the authenticated POST endpoint**

```powershell
git add backend/forestal_bot backend/produccion_api/urls.py
git commit -m "feat(forestal-bot): add authenticated WhatsApp ingest"
```

### Task 3: Complete idempotency and media behavior

**Files:**
- Modify: `backend/forestal_bot/tests/test_api.py`
- Modify if required by failing tests: `backend/forestal_bot/serializers.py`
- Modify if required by failing tests: `backend/forestal_bot/views.py`

- [ ] **Step 1: Add failing duplicate and media tests**

```python
def test_duplicate_post_returns_existing_message_without_overwrite(self):
    self.authenticate()
    original = self.payload(body="first")
    duplicate = self.payload(body="second")
    first = self.client.post(self.url, original, format="json")
    second = self.client.post(self.url, duplicate, format="json")
    self.assertEqual(first.status_code, status.HTTP_201_CREATED)
    self.assertEqual(second.status_code, status.HTTP_200_OK)
    self.assertFalse(second.data["created"])
    self.assertEqual(WhatsAppMessage.objects.count(), 1)
    self.assertEqual(WhatsAppMessage.objects.get().body, "first")

def test_media_message_without_body_is_accepted(self):
    self.authenticate()
    payload = self.payload(message_type="image", media_type="image/jpeg", media_path="spool/image.jpg")
    payload.pop("body", None)
    response = self.client.post(self.url, payload, format="json")
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    self.assertEqual(WhatsAppMessage.objects.get().body, "")
```

- [ ] **Step 2: Run the two tests and confirm RED if behavior is incomplete**

Run each test with its dotted test name. The media test must fail if the serializer currently requires `body`; the duplicate test must prove status and non-overwrite behavior.

- [ ] **Step 3: Apply only the minimal serializer/view correction required**

Ensure `body` is `required=False, allow_blank=True, default=""` and duplicates serialize the existing row without updating it.

- [ ] **Step 4: Run all `forestal_bot` tests and confirm GREEN**

```powershell
.\.venv\Scripts\python.exe backend\manage.py test forestal_bot.tests -v 2
```

- [ ] **Step 5: Commit idempotency behavior**

```powershell
git add backend/forestal_bot
git commit -m "test(forestal-bot): cover idempotent media ingest"
```

### Task 4: Add the recent-message audit endpoint

**Files:**
- Modify: `backend/forestal_bot/views.py`
- Modify: `backend/forestal_bot/urls.py`
- Modify: `backend/forestal_bot/tests/test_api.py`

- [ ] **Step 1: Write failing GET recent tests**

Add tests that create messages in two groups at distinct timestamps, authenticate, and assert:

```python
response = self.client.get(reverse("forestal_bot:whatsapp-message-recent"))
self.assertEqual(response.status_code, status.HTTP_200_OK)
self.assertEqual([row["message_id"] for row in response.data], ["newest", "oldest"])
```

Also test exact `group_jid`, ISO-8601 `since`, `limit=1`, invalid `since`, invalid/non-positive `limit`, and GET without a token. Each behavior is a separate test.

- [ ] **Step 2: Run recent tests and confirm RED**

Expected: reverse failure because `whatsapp-message-recent` does not exist.

- [ ] **Step 3: Implement the recent view and URL**

Create `WhatsAppMessageRecentView(APIView)` with the same empty authentication classes and Bearer permission. Start with `WhatsAppMessage.objects.order_by("-timestamp", "-created_at")`, apply an exact group filter, validate `since` through `serializers.DateTimeField()`, parse `limit` as a positive integer, cap it with `min(limit, 500)`, and return the sliced serializer data.

Register:

```python
path(
    "whatsapp/messages/recent/",
    WhatsAppMessageRecentView.as_view(),
    name="whatsapp-message-recent",
),
```

- [ ] **Step 4: Run all app tests and confirm GREEN**

```powershell
.\.venv\Scripts\python.exe backend\manage.py test forestal_bot.tests -v 2
```

- [ ] **Step 5: Commit the audit endpoint**

```powershell
git add backend/forestal_bot
git commit -m "feat(forestal-bot): add recent message audit API"
```

### Task 5: Document the OpenClaw integration contract

**Files:**
- Create: `backend/forestal_bot/README.md`

- [ ] **Step 1: Write the integration README**

Document POST and GET URLs, `Authorization: Bearer <token>`, `OPENCLAW_INGEST_TOKEN`, all GET filters and limits, a complete text payload, a media payload without `body`, HTTP 201 and duplicate HTTP 200 responses, and these explicit statements:

```text
El JSONL local es el spool confiable y se escribe primero; la API central se sincroniza después.
OpenClaw consume este contrato de API, pero no lo diseña ni modifica.
```

- [ ] **Step 2: Verify documentation content mechanically**

```powershell
rg -n "POST|GET|Authorization|OPENCLAW_INGEST_TOKEN|JSONL|OpenClaw|created.*true|created.*false" backend\forestal_bot\README.md
```

Expected: every required topic has at least one match.

- [ ] **Step 3: Commit documentation**

```powershell
git add backend/forestal_bot/README.md
git commit -m "docs(forestal-bot): document OpenClaw integration"
```

### Task 6: Verify scope and publish the draft PR

**Files:**
- Review all files changed from `origin/main`

- [ ] **Step 1: Verify migrations and project configuration**

```powershell
$env:SECRET_KEY='r10-test-key'
$env:DATABASE_URL='sqlite:///r10-tests.sqlite3'
.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe backend\manage.py check
```

Expected: no pending migrations; check has no errors. The existing missing `backend/static` warning may remain documented.

- [ ] **Step 2: Run focused and complete test suites freshly**

```powershell
.\.venv\Scripts\python.exe backend\manage.py test forestal_bot.tests -v 2
.\.venv\Scripts\python.exe backend\manage.py test -v 2
```

Expected: every discovered test passes.

- [ ] **Step 3: Audit scope and diff hygiene**

```powershell
git diff --check origin/main...HEAD
git diff --name-status origin/main...HEAD
git status --short --branch
```

Expected: no frontend, OpenClaw, `produccion`, or `mantenimiento` files; only design/plan docs, `backend/forestal_bot`, and the two project registration files.

- [ ] **Step 4: Request code review and address Critical/Important findings**

Review `origin/main...HEAD` against issues #14-#20, rerun focused tests after corrections, and commit any required fixes.

- [ ] **Step 5: Push and create the draft PR**

```powershell
git push -u origin codex/r10-whatsapp-ingest
```

Create a draft PR to `main` titled `feat: add R10 WhatsApp persistence API`. Its body must summarize behavior, tests, spool architecture, and include:

```text
Closes #14
Closes #15
Closes #16
Closes #17
Closes #18
Closes #19
Closes #20
```

- [ ] **Step 6: Verify the remote PR**

```powershell
gh pr view --json url,isDraft,headRefName,baseRefName,title,body
```

Expected: draft is true, head is `codex/r10-whatsapp-ingest`, base is `main`, and all seven closing references are present.
