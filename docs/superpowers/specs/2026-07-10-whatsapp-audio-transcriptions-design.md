# Persistencia y pantalla de transcripciones de audio WhatsApp

## Objetivo

Ampliar `forestal_bot` para almacenar transcripciones producidas localmente por OpenClaw y ofrecer al dueño una pantalla dedicada de mensajes WhatsApp. `dashboard_fg` no descargará, abrirá ni procesará audios.

## Backend y modelo

`WhatsAppMessage` incorporará `transcription`, `transcription_status`, `transcription_error` y `transcribed_at`. Los estados admitidos serán vacío, `pending`, `processing`, `completed` y `failed`. La API limitará `transcription` a 20.000 caracteres y `transcription_error` a 1.000 caracteres.

La migración agregará únicamente esas cuatro columnas a `forestal_bot_whatsappmessage`, con valores compatibles para registros existentes. No modificará mensajes ni otras tablas.

## Actualización idempotente

El primer POST conservará la creación actual y responderá 201. Un POST repetido resolverá la misma identidad y responderá 200 sin crear otro mensaje.

Para un mensaje existente sólo podrán cambiar los cuatro campos de transcripción:

- `pending` o `processing` actualizarán únicamente el estado mientras no exista una transcripción completada.
- `failed` guardará el error acotado y limpiará `transcribed_at`, pero no reemplazará una transcripción completada.
- `completed` con texto no vacío guardará la primera transcripción, establecerá `transcribed_at=timezone.now()` y limpiará el error.
- Una transcripción completada y no vacía será inmutable para la ingesta automática.

Nunca se reescribirán `body`, `raw_json`, remitente, grupo, timestamp, datos multimedia ni otros campos originales. `media_path` continuará siendo metadata opaca.

## API y seguridad

POST y GET recent devolverán los cuatro campos nuevos. El Bearer actual seguirá siendo obligatorio y un request sin token devolverá 403. La API no registrará el token ni abrirá `media_path`.

## Pantalla dedicada

Se creará una vista Vue protegida `/mensajes-whatsapp`, accesible como “Mensajes WhatsApp” desde la navegación desktop y móvil. Consumirá GET recent y mostrará tarjetas o filas responsivas con:

- `group_display_name` como nombre principal del grupo;
- remitente (`sender_name`, con fallback técnico sólo cuando falte);
- fecha y hora;
- indicador de audio;
- transcripción cuando el estado sea `completed`;
- “Transcribiendo…” para `pending` o `processing`;
- “No se pudo transcribir” para `failed`;
- cuerpo para mensajes no audio.

La pantalla nunca mostrará `media_path` como enlace ni expondrá JID como etiqueta principal. Tendrá estados de carga, error y lista vacía, y actualización manual. La autenticación de usuario del dashboard seguirá usando su JWT; para evitar exponer `OPENCLAW_INGEST_TOKEN` en el navegador, se agregará una ruta de lectura del dueño protegida por la autenticación Django/DRF existente, separada de GET recent para OpenClaw.

## Pruebas y despliegue

Los tests cubrirán migración, validación, pending, completed, failed, inmutabilidad, compatibilidad, serialización y seguridad. El frontend tendrá build y validación visual real con capturas.

El despliegue requerirá backup timestampado, migración, reinicio, logs y una prueba productiva pending → completed con un único `message_id`. No se modificará OpenClaw ni ninguna Mac.
