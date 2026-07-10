# Catálogo de grupos WhatsApp para `forestal_bot`

## Objetivo

Agregar un catálogo administrable de grupos WhatsApp que permita mostrar nombres comprensibles sin romper el contrato actual de ingestión y consulta de mensajes.

## Alcance

- Crear `WhatsAppGroup` con identidad única por `account_id` y `jid`.
- Relacionar opcionalmente `WhatsAppMessage.group` con el catálogo.
- Conservar `group_jid` y `group_name` en los mensajes.
- Sincronizar prudentemente el catálogo durante cada POST idempotente.
- Migrar y relacionar mensajes existentes sin inventar nombres comerciales.
- Exponer administración API autenticada y Django Admin.
- Incluir datos amigables del grupo en `GET recent`.
- Desplegar con backup, migración, reinicio y pruebas productivas verificables.

Quedan fuera de alcance OpenClaw, la Mac, Tailscale, cambios destructivos de MySQL y cualquier asignación de nombres comerciales no comprobada.

## Modelo de datos

`WhatsAppGroup` tendrá `id`, `account_id`, `jid`, `name`, `description`, `active`, `created_at` y `updated_at`. Tendrá una restricción única sobre `(account_id, jid)` e índices para `jid`, `(account_id, active)` y `name`.

`WhatsAppMessage.group` será una clave foránea nullable con `on_delete=SET_NULL`. Esta política preserva mensajes históricos si un administrador elimina un grupo y evita que una operación de catálogo bloquee la trazabilidad de mensajes. Los campos históricos `group_jid` y `group_name` continuarán sin cambios.

## Política de sincronización

En cada POST se resolverá el grupo dentro de la misma transacción usando `(account_id, group_jid)`:

1. Si existe, se vincula el mensaje.
2. Si llega un `group_name` no vacío, se usa al crear el grupo.
3. Un nombre entrante sólo reemplaza un nombre vacío o el marcador exacto `Grupo sin identificar`; no sobrescribe nombres administrados.
4. Si el grupo no existe y no llega nombre, se crea con `Grupo sin identificar`.
5. La identidad del mensaje continúa siendo `(account_id, group_jid, message_id)`; un POST duplicado no crea otro mensaje ni otro grupo.

El marcador neutral garantiza una relación completa y evita exponer el JID en pantallas del dueño, sin atribuir un nombre comercial falso. El JID seguirá disponible en administración y respuestas técnicas.

## Migración de datos

Una migración Django creará un grupo por cada combinación distinta no vacía de `account_id` y `group_jid`, elegirá un `group_name` histórico no vacío cuando exista y usará `Grupo sin identificar` en los demás casos. Luego asociará todos los mensajes coincidentes.

La migración será idempotente a nivel lógico mediante la restricción única y `get_or_create`/`update` acotados. No eliminará ni reescribirá campos históricos.

Antes de aplicarla en producción se consultarán y mostrarán los JID reales con sus cantidades. Después se asignará explícitamente `Grupo de prueba` a `120363426378425507@g.us`. No se asignará `Mantenimiento` sin evidencia del JID correcto.

## API

Se agregarán rutas protegidas por `OpenClawBearerPermission`:

- `GET /api/forestal-bot/whatsapp/groups/`
- `POST /api/forestal-bot/whatsapp/groups/`
- `PATCH /api/forestal-bot/whatsapp/groups/<id>/`

El listado aceptará filtros exactos `active` y `account_id`. La creación y actualización validarán la unicidad por cuenta y JID y devolverán errores 400 comprensibles ante conflictos.

`GET recent` conservará `group_jid` y agregará:

```json
{
  "group": {"id": 1, "jid": "...@g.us", "name": "Grupo de prueba"},
  "group_display_name": "Grupo de prueba"
}
```

La prioridad será `group.name`, luego `message.group_name`, y finalmente `message.group_jid`. Las superficies destinadas al dueño consumirán `group_display_name`; el JID quedará reservado para administración o detalle técnico.

## Administración

Si Django Admin está habilitado, `WhatsAppGroup` se registrará con columnas `name`, `jid`, `account_id`, `active` y `updated_at`; búsqueda por `name` y `jid`; y filtros por `active` y `account_id`.

## Errores y concurrencia

La ingestión mantendrá `transaction.atomic`, `get_or_create` y recuperación de `IntegrityError` para conservar idempotencia bajo concurrencia. La restricción de base será la última defensa contra duplicados. Los endpoints sin token conservarán respuesta 403.

## Pruebas

Se aplicará TDD para cubrir creación y unicidad de grupos, vínculo durante POST, duplicados, actualización prudente de nombres, compatibilidad sin `group_name`, serialización amigable, seguridad y filtros CRUD. La migración se probará con `MigrationExecutor` o el patrón de migraciones ya existente, verificando que conserva y relaciona mensajes previos.

Antes de desplegar se ejecutarán `manage.py check`, `makemigrations --check`, tests completos de `forestal_bot`, tests generales relevantes y verificaciones Git. Cualquier falla detendrá el despliegue.

## Despliegue y aceptación

El despliegue usará el procedimiento existente hacia `/var/www/fg/produccion_api`: backup con timestamp, copia controlada, migración con el entorno virtual correcto, reinicio de `produccion_api`, comprobación de systemd y logs, y pruebas HTTP autenticadas leyendo el token desde el entorno sin imprimirlo.

La aceptación exige evidencia de tabla MySQL, relación de mensajes existentes, nombre inicial correcto, POST 201/duplicado 200, GET recent con `group_display_name`, rechazo 403 sin token, servicio activo y ausencia de errores nuevos.
