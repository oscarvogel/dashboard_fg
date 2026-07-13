# API de ingesta de WhatsApp para OpenClaw

Esta API recibe mensajes de WhatsApp ya capturados por OpenClaw, mantiene un catalogo administrable de grupos y permite consultar los mensajes sincronizados recientemente.

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

Cada mensaje se vincula al catalogo por `account_id + group_jid`. Si el payload trae un `group_name` no vacio, se usa para crear el grupo o reemplazar solamente el marcador `Grupo sin identificar`; un nombre administrado nunca se sobrescribe automaticamente. Si `group_name` se omite, el payload sigue siendo compatible y se crea el grupo con ese marcador neutral.

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

Cada mensaje conserva `group_jid` y `group_name` y agrega:

```json
{
  "group": {
    "id": 1,
    "jid": "120363426378425507@g.us",
    "name": "Grupo de prueba"
  },
  "group_display_name": "Grupo de prueba"
}
```

`group_display_name` prioriza el nombre del catalogo, luego el `group_name` historico y finalmente `group_jid`. Las pantallas del dueno deben usar `group_display_name`; el JID queda para administracion o diagnostico tecnico.

## Transcripciones locales de audio

OpenClaw puede enviar primero el audio como pendiente y repetir el mismo POST cuando Whisper termina localmente. `dashboard_fg` no descarga ni abre `media_path`, no ejecuta Whisper y no envia el audio a proveedores externos.

Primer POST:

```json
{
  "account_id": "default",
  "group_jid": "120363426378425507@g.us",
  "message_id": "ID-REAL-DEL-MENSAJE",
  "timestamp": "2026-07-10T17:30:00-03:00",
  "body": "",
  "message_type": "audio/ogg",
  "media_type": "audio/ogg",
  "media_path": "/ruta/local/del/audio.ogg",
  "transcription_status": "pending"
}
```

Responde `201 Created`. El segundo POST conserva la misma identidad:

```json
{
  "account_id": "default",
  "group_jid": "120363426378425507@g.us",
  "message_id": "ID-REAL-DEL-MENSAJE",
  "timestamp": "2026-07-10T17:30:00-03:00",
  "body": "",
  "message_type": "audio/ogg",
  "media_type": "audio/ogg",
  "media_path": "/ruta/local/del/audio.ogg",
  "transcription": "Texto transcripto localmente por Whisper.",
  "transcription_status": "completed"
}
```

Responde `200 OK` con `created: false`, completa `transcribed_at` y limpia `transcription_error`. Sólo se actualizan los campos de transcripcion: el payload y contenido originales permanecen intactos.

Para un fallo se usa `transcription_status: "failed"` y una descripcion tecnica breve en `transcription_error`. Los estados admitidos son vacio, `pending`, `processing`, `completed` y `failed`. La transcripcion se limita a 20.000 caracteres y el error a 1.000; no se aceptan trazas ni marcadores de secretos.

Una transcripcion completada y no vacia nunca se sobrescribe mediante ingesta. Una futura correccion manual debe usar un endpoint administrativo diferente.

La pantalla JWT del dueno consume `GET /api/forestal-bot/whatsapp/owner/messages/`. Esta ruta no devuelve `media_path` ni `group_jid`; el token de OpenClaw no se expone al navegador.

## Análisis de imágenes realizado por OpenClaw

OpenClaw puede enviar primero metadata de una imagen con `image_analysis_status: "pending"` y repetir el mismo POST cuando finaliza su análisis. `dashboard_fg` sólo persiste el resultado: no descarga, abre ni analiza `media_path` y no registra contenido binario.

Primer POST:

```json
{
  "account_id": "default",
  "group_jid": "120363426378425507@g.us",
  "message_id": "ID-REAL",
  "timestamp": "2026-07-10T18:00:00-03:00",
  "body": "",
  "message_type": "image/jpeg",
  "media_type": "image/jpeg",
  "media_path": "/ruta/local/no-publica/imagen.jpg",
  "image_analysis_status": "pending"
}
```

Actualización con la misma identidad:

```json
{
  "account_id": "default",
  "group_jid": "120363426378425507@g.us",
  "message_id": "ID-REAL",
  "timestamp": "2026-07-10T18:00:00-03:00",
  "body": "",
  "message_type": "image/jpeg",
  "media_type": "image/jpeg",
  "media_path": "/ruta/local/no-publica/imagen.jpg",
  "image_description": "Se observa una manguera hidraulica con una fisura longitudinal.",
  "image_analysis_status": "completed"
}
```

El primer POST responde 201 y el segundo 200 con `created: false`. Sólo se actualizan los cuatro campos de análisis; `raw_json`, cuerpo, remitente, grupo, timestamp y metadata originales permanecen intactos. `completed` establece `image_analyzed_at`, limpia el error y no puede sobrescribirse posteriormente por ingesta.

Los estados admitidos son vacío, `pending`, `processing`, `completed` y `failed`. `image_description` se limita a 10.000 caracteres e `image_analysis_error` a 500; no se aceptan trazas ni marcadores de secretos.

La descripción automática es orientativa y no reemplaza una inspección técnica profesional.

## Administrar grupos

Todos los endpoints usan el mismo encabezado Bearer:

```http
GET /api/forestal-bot/whatsapp/groups/?account_id=account-1&active=true
POST /api/forestal-bot/whatsapp/groups/
PATCH /api/forestal-bot/whatsapp/groups/1/
Authorization: Bearer <token>
```

El POST requiere `account_id`, `jid` y `name`; acepta `description` y `active`. No se permite repetir un `jid` dentro de la misma cuenta. GET permite filtrar exactamente por `account_id` y `active`. PATCH permite modificar parcialmente un grupo existente.

## Responsabilidades del flujo

El JSONL local es el spool confiable: OpenClaw escribe cada mensaje alli primero y luego intenta sincronizarlo con esta API. Por eso, una falla temporal de la API no debe hacer perder el evento que ya quedo persistido localmente.

OpenClaw consume este contrato de API, pero no lo disena ni lo modifica. Los cambios del contrato pertenecen a este backend; esta documentacion no contiene instrucciones para cambiar OpenClaw.

## Resumenes operativos diarios

El historial centralizado de los resumenes enviados se registra con el mismo
Bearer token de OpenClaw:

```http
POST /api/forestal-bot/daily-summaries/
Authorization: Bearer <token>
Content-Type: application/json
```

Ejemplo sanitizado:

```json
{
  "idempotency_key": "2026-07-13:consolidated",
  "operational_date": "2026-07-13",
  "generated_at": "2026-07-13T21:00:00-03:00",
  "status": "sent",
  "consolidated_text": "Resumen operativo diario...",
  "spoken_script": "Guion utilizado para el audio...",
  "total_groups": 1,
  "total_messages": 4,
  "generator_version": "daily-operational-v1",
  "source": "openclaw",
  "groups": [
    {
      "group_key": "mantenimiento",
      "group_name": "Mantenimiento",
      "message_count": 4,
      "summary_text": "Se informaron novedades de mantenimiento.",
      "no_updates": false,
      "position": 0
    }
  ],
  "deliveries": [
    {
      "channel": "whatsapp",
      "recipient_name": "jose",
      "status": "sent",
      "attempted_at": "2026-07-13T21:02:00-03:00",
      "delivered_at": "2026-07-13T21:02:01-03:00",
      "error": "",
      "external_id": ""
    }
  ]
}
```

`idempotency_key` es unica. El primer POST responde `201` con `created: true`;
un reintento responde `200` con `created: false` y actualiza la misma ejecucion.
Las secciones por grupo se reemplazan por el estado completo recibido y las
entregas se actualizan por `channel + recipient_name`. Si una actualizacion no
incluye entregas ya registradas, estas se conservan.

Los totales deben coincidir con las secciones: `total_groups` debe ser igual a
la cantidad de grupos y `total_messages` a la suma de `message_count`.

La consulta usa las mismas credenciales:

```http
GET /api/forestal-bot/daily-summaries/?date_from=2026-07-01&date_to=2026-07-31&group_key=mantenimiento&status=sent&channel=whatsapp&limit=100
GET /api/forestal-bot/daily-summaries/1/
Authorization: Bearer <token>
```

Los filtros son opcionales. `limit` debe ser positivo, vale `100` por defecto y
se limita a `500`. No se guardan telefonos, correos, JIDs, tokens, rutas locales,
audio ni HTML. `recipient_name` debe ser solamente una referencia logica. Los
errores se limitan a 1.000 caracteres y rechazan trazas o marcadores de secretos.
