# WhatsApp Image Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persistir análisis de imágenes producido por OpenClaw y mostrarlo de forma segura en la pantalla dedicada del dueño.

**Architecture:** La ingesta Bearer conservará la identidad actual y actualizará exclusivamente cuatro campos de análisis en duplicados. La API JWT y la vista Vue existente se ampliarán sin exponer JID, `media_path` ni imágenes privadas.

**Tech Stack:** Django 5.1, DRF, MySQL, Vue 3, Axios, Tailwind.

---

### Task 1: Modelo y migración

**Files:** `backend/forestal_bot/models.py`, `serializers.py`, `migrations/0006_*.py`, tests de modelo/migración.

- [ ] Escribir tests fallidos para defaults, choices, límites 10.000/500 y compatibilidad desde `0005`.
- [ ] Confirmar RED.
- [ ] Agregar campos, choices, validadores y migración aditiva.
- [ ] Confirmar GREEN y que la migración sólo agregue cuatro columnas.
- [ ] Commit.

### Task 2: Actualización idempotente

**Files:** `backend/forestal_bot/views.py`, `serializers.py`, `tests/test_api.py`.

- [ ] Escribir tests fallidos pending→completed, failed, inmutabilidad, límites, seguridad, campos originales y 403.
- [ ] Confirmar RED.
- [ ] Implementar actualización transaccional independiente de la transcripción de audio.
- [ ] Confirmar GREEN y commit.

### Task 3: API JWT y pantalla

**Files:** serializer del dueño, `MensajesWhatsApp.vue`, documentación/evidencia visual.

- [ ] Probar que la API JWT devuelve campos de imagen sin `media_path` ni JID.
- [ ] Mostrar distintivo Imagen, descripción, pending/processing, failed y advertencia técnica.
- [ ] Ejecutar build y validación visual desktop/móvil con metadata ficticia.
- [ ] Guardar capturas y reporte; commit.

### Task 4: Publicación y producción

- [ ] Actualizar README con payloads y política de seguridad/no sobrescritura.
- [ ] Ejecutar checks Django, migraciones, tests, compileall, build y checks Git.
- [ ] Push y PR draft contra `main`, vinculado con #29.
- [ ] Crear backups backend/frontend, revisar `migrate --plan`, migrar y reiniciar.
- [ ] Probar metadata pending 201 → completed 200, recent, fila única, 403, servicio y logs.
- [ ] Auditar requisitos y entregar evidencia final.
