# API de ingesta de WhatsApp para OpenClaw

Esta API recibe mensajes de WhatsApp ya capturados por OpenClaw y permite consultar los mensajes sincronizados recientemente.

## Autenticacion

Ambos endpoints requieren el encabezado HTTP:

```http
Authorization: Bearer <token>
```

El backend compara ese valor con la variable de entorno `OPENCLAW_INGEST_TOKEN`. Si la variable no esta configurada, falta el encabezado o el token no coincide, la API responde `403 Forbidden`.

## Crear o reconocer un mensaje

```http
POST /api/forestal-bot/whatsapp/messages/
Content-Type: application/json
Authorization: Bearer <token>
```

Los campos obligatorios son:

- `account_id`: identificador de la cuenta de WhatsApp.
- `group_jid`: JID del grupo.
- `message_id`: identificador del mensaje en el proveedor.
- `timestamp`: fecha y hora ISO 8601 del mensaje; debe incluir `Z` o un offset UTC explicito, por ejemplo `-03:00`. Un timestamp naive, sin zona ni offset, responde `400 Bad Request`.

La identidad idempotente del mensaje es la combinacion de `account_id`, `group_jid` y `message_id`. Un reenvio de esa misma identidad devuelve el registro existente y no sobrescribe su contenido.

### Payload completo para un mensaje de texto

```json
{
  "source": "openclaw",
  "provider": "whatsapp-web",
  "account_id": "account-1",
  "group_jid": "120363000000000000@g.us",
  "message_id": "message-1",
  "group_name": "Operaciones Forestales",
  "sender_id": "5491112345678",
  "sender_e164": "+5491112345678",
  "sender_name": "Operador Uno",
  "timestamp": "2026-07-10T10:15:30-03:00",
  "body": "Equipo detenido por mantenimiento",
  "message_type": "text",
  "media_type": "",
  "media_path": "",
  "gated_out": false,
  "would_process_agent": true,
  "skip_reason": ""
}
```

### Payload para un mensaje con media y sin `body`

`body` es opcional y, si se omite, se almacena como cadena vacia.

```json
{
  "source": "openclaw",
  "provider": "whatsapp-web",
  "account_id": "account-1",
  "group_jid": "120363000000000000@g.us",
  "message_id": "message-image-1",
  "group_name": "Operaciones Forestales",
  "sender_id": "5491112345678",
  "sender_e164": "+5491112345678",
  "sender_name": "Operador Uno",
  "timestamp": "2026-07-10T10:16:00-03:00",
  "message_type": "image",
  "media_type": "image/jpeg",
  "media_path": "spool/image.jpg",
  "gated_out": false,
  "would_process_agent": true,
  "skip_reason": ""
}
```

### Respuesta de creacion

Un mensaje nuevo responde `201 Created` con `created: true`:

```json
{
  "created": true,
  "message": {
    "id": 1,
    "source": "openclaw",
    "provider": "whatsapp-web",
    "account_id": "account-1",
    "group_jid": "120363000000000000@g.us",
    "message_id": "message-1",
    "group_name": "Operaciones Forestales",
    "sender_id": "5491112345678",
    "sender_e164": "+5491112345678",
    "sender_name": "Operador Uno",
    "timestamp": "2026-07-10T10:15:30-03:00",
    "body": "Equipo detenido por mantenimiento",
    "message_type": "text",
    "media_type": "",
    "media_path": "",
    "gated_out": false,
    "would_process_agent": true,
    "skip_reason": "",
    "raw_json": {
      "source": "openclaw",
      "provider": "whatsapp-web",
      "account_id": "account-1",
      "group_jid": "120363000000000000@g.us",
      "message_id": "message-1",
      "group_name": "Operaciones Forestales",
      "sender_id": "5491112345678",
      "sender_e164": "+5491112345678",
      "sender_name": "Operador Uno",
      "timestamp": "2026-07-10T10:15:30-03:00",
      "body": "Equipo detenido por mantenimiento",
      "message_type": "text",
      "media_type": "",
      "media_path": "",
      "gated_out": false,
      "would_process_agent": true,
      "skip_reason": ""
    },
    "synced_at": "2026-07-10T10:15:31-03:00",
    "created_at": "2026-07-10T10:15:31-03:00"
  }
}
```

### Respuesta de duplicado

Si la identidad ya existe, responde `200 OK` con `created: false` y el mensaje existente:

```json
{
  "created": false,
  "message": {
    "id": 1,
    "source": "openclaw",
    "provider": "whatsapp-web",
    "account_id": "account-1",
    "group_jid": "120363000000000000@g.us",
    "message_id": "message-1",
    "group_name": "Operaciones Forestales",
    "sender_id": "5491112345678",
    "sender_e164": "+5491112345678",
    "sender_name": "Operador Uno",
    "timestamp": "2026-07-10T10:15:30-03:00",
    "body": "Equipo detenido por mantenimiento",
    "message_type": "text",
    "media_type": "",
    "media_path": "",
    "gated_out": false,
    "would_process_agent": true,
    "skip_reason": "",
    "raw_json": {
      "source": "openclaw",
      "provider": "whatsapp-web",
      "account_id": "account-1",
      "group_jid": "120363000000000000@g.us",
      "message_id": "message-1",
      "group_name": "Operaciones Forestales",
      "sender_id": "5491112345678",
      "sender_e164": "+5491112345678",
      "sender_name": "Operador Uno",
      "timestamp": "2026-07-10T10:15:30-03:00",
      "body": "Equipo detenido por mantenimiento",
      "message_type": "text",
      "media_type": "",
      "media_path": "",
      "gated_out": false,
      "would_process_agent": true,
      "skip_reason": ""
    },
    "synced_at": "2026-07-10T10:15:31-03:00",
    "created_at": "2026-07-10T10:15:31-03:00"
  }
}
```

Un payload invalido responde `400 Bad Request`; por ejemplo, si falta alguno de los cuatro campos obligatorios o un campo tiene un tipo/formato invalido.

## Consultar mensajes recientes

```http
GET /api/forestal-bot/whatsapp/messages/recent/?group_jid=120363000000000000@g.us&since=2026-07-10T10:00:00-03:00&limit=100
Authorization: Bearer <token>
```

Los filtros son opcionales:

- `group_jid`: coincidencia exacta del JID del grupo.
- `since`: incluye mensajes cuyo `timestamp` sea igual o posterior a una fecha ISO 8601.
- `limit`: entero positivo; el valor predeterminado es `100` y el maximo efectivo es `500`.

La respuesta `200 OK` es un arreglo JSON de mensajes, ordenado desde el `timestamp` mas reciente. Un `since` invalido o un `limit` no entero, cero o negativo responde `400 Bad Request`. La falta de un token valido responde `403 Forbidden`.

## Responsabilidades del flujo

El JSONL local es el spool confiable: OpenClaw escribe cada mensaje alli primero y luego intenta sincronizarlo con esta API. Por eso, una falla temporal de la API no debe hacer perder el evento que ya quedo persistido localmente.

OpenClaw consume este contrato de API, pero no lo disena ni lo modifica. Los cambios del contrato pertenecen a este backend; esta documentacion no contiene instrucciones para cambiar OpenClaw.
