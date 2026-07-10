# WhatsApp Audio Transcriptions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persistir actualizaciones de transcripción locales y ofrecer una pantalla JWT dedicada al dueño.

**Architecture:** La ingesta Bearer conserva la creación idempotente y añade una ruta controlada para actualizar sólo campos de transcripción en duplicados. Una API de lectura separada usa JWT y alimenta una vista Vue dedicada sin exponer el token de OpenClaw ni `media_path`.

**Tech Stack:** Django 5.1, DRF, MySQL, Vue 3, Axios, Tailwind.

---

### Task 1: Modelo, validación y migración

**Files:** `backend/forestal_bot/models.py`, `serializers.py`, `migrations/0005_*.py`, `tests/test_models.py`, `tests/test_migrations.py`

- [ ] Agregar tests fallidos para defaults, choices, límites 20.000/1.000 y supervivencia de mensajes desde `0004`.
- [ ] Confirmar RED ejecutando tests específicos.
- [ ] Agregar campos, choices y validadores DRF; generar migración aditiva.
- [ ] Confirmar GREEN y revisar que la migración sólo agregue cuatro columnas.
- [ ] Commit del modelo y migración.

### Task 2: Actualización idempotente de transcripciones

**Files:** `backend/forestal_bot/views.py`, `serializers.py`, `tests/test_api.py`

- [ ] Agregar tests fallidos pending→completed, failed, protección de completed, raw/body invariantes, compatibilidad y 403.
- [ ] Confirmar RED.
- [ ] Implementar actualización transaccional exclusivamente de los cuatro campos de transcripción.
- [ ] Exigir texto no vacío para completed; limpiar error y establecer `timezone.now()`.
- [ ] Confirmar GREEN y commit.

### Task 3: API JWT y pantalla dedicada

**Files:** `backend/forestal_bot/views.py`, `urls.py`, `tests/test_api.py`, `dashboard-frontend/src/views/MensajesWhatsApp.vue`, `router/index.js`, `components/NavBar.vue`

- [ ] Agregar test fallido para lectura sin JWT y con JWT.
- [ ] Crear `GET /api/forestal-bot/whatsapp/owner/messages/` con `IsAuthenticated`, filtros y serialización sin `media_path`.
- [ ] Crear vista protegida `/mensajes-whatsapp` con grupo, remitente, fecha, indicador de audio y estados completed/pending/processing/failed.
- [ ] Agregar navegación desktop y móvil, carga/error/vacío y actualización manual.
- [ ] Ejecutar tests y build frontend; corregir sólo fallas del alcance.
- [ ] Validar visualmente y guardar screenshots/reporte si el entorno permite abrir la UI.
- [ ] Commit backend/frontend.

### Task 4: Documentación, publicación y despliegue

**Files:** `backend/forestal_bot/README.md`, documentación visual si aplica.

- [ ] Documentar pending→completed/failed, límites, no sobrescritura y separación OpenClaw/backend.
- [ ] Ejecutar `check`, `makemigrations --check`, tests `forestal_bot`, tests relevantes, build, compileall y checks Git.
- [ ] Push y PR draft contra `main`, vinculado con #27.
- [ ] Inventariar producción, crear backup timestampado, copiar archivos, revisar `migrate --plan`, migrar y reiniciar.
- [ ] Probar HTTP pending 201 → completed 200 con un único ID, GET recent, owner API JWT si hay credencial segura y 403 sin token.
- [ ] Confirmar tabla/columnas, un único mensaje, servicio activo y logs limpios.
- [ ] Entregar evidencia y mensaje end-to-end para el bot.
