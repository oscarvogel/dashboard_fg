# Persistencia de análisis de imágenes WhatsApp

## Objetivo

Ampliar `forestal_bot` para almacenar descripciones de imágenes producidas por OpenClaw y mostrarlas en la pantalla dedicada de mensajes WhatsApp. `dashboard_fg` no descargará, abrirá ni analizará imágenes.

## Modelo y migración

`WhatsAppMessage` incorporará `image_description`, `image_analysis_status`, `image_analysis_error` e `image_analyzed_at`. Los estados admitidos serán vacío, `pending`, `processing`, `completed` y `failed`.

La migración `0006` será posterior a la migración de transcripciones y agregará únicamente estas cuatro columnas a `forestal_bot_whatsappmessage`. Los registros existentes recibirán cadenas vacías y fecha nula, sin reescrituras ni operaciones sobre otras aplicaciones.

## Actualización idempotente

El primer POST conservará la creación actual y responderá 201. Un POST repetido resolverá la misma identidad `(account_id, group_jid, message_id)`, responderá 200 y sólo podrá modificar campos de análisis de imagen:

- `pending` y `processing` actualizarán únicamente el estado mientras no exista una descripción completada.
- `failed` guardará un error acotado y mantendrá `image_analyzed_at` nulo.
- `completed` exigirá descripción no vacía, almacenará la primera descripción, establecerá `image_analyzed_at=timezone.now()` y limpiará el error.
- Una descripción completada y no vacía será inmutable para la ingesta automática.

Nunca se reescribirán `body`, `raw_json`, remitente, grupo, timestamp, datos multimedia, transcripción ni otros campos originales. `media_path` será metadata opaca.

## Validación y seguridad

`image_description` tendrá un máximo de 10.000 caracteres e `image_analysis_error` un máximo de 500. Los errores rechazarán marcadores de traceback, encabezados Bearer y nombres habituales de secretos. El Bearer actual seguirá siendo obligatorio y el backend no registrará contenido binario ni abrirá `media_path`.

## API y pantalla del dueño

POST y GET recent devolverán los cuatro campos nuevos. La API JWT del dueño incluirá estado, descripción, error y fecha, pero seguirá excluyendo `media_path` y JID.

La vista protegida `/mensajes-whatsapp` conservará grupo, remitente y fecha, y para imágenes mostrará:

- distintivo “Imagen”;
- descripción cuando esté `completed`;
- “Analizando imagen…” para `pending` o `processing`;
- “No se pudo analizar la imagen” para `failed`;
- advertencia de que el análisis automático es orientativo y no reemplaza una inspección técnica.

La pantalla no renderizará ni enlazará la imagen privada.

## Pruebas y despliegue

Los tests cubrirán migración, creación pending, actualización completed/failed, inmutabilidad, límites, estados inválidos, compatibilidad, serialización, seguridad y preservación de campos originales.

El despliegue requerirá backup timestampado, revisión de `migrate --plan`, migración, reinicio, logs y una prueba productiva pending → completed basada sólo en metadata ficticia. No se enviará ni analizará una imagen real.
