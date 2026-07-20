# Cargas de combustible recibidas — contrato API

Este contrato es exclusivo de Forestal Paraguay y del grupo Choferes FGPY.
No escribe en `produccion.CargaCombustible` ni en la tabla `cargacomb`.
`forestal_bot.WhatsAppMessage` conserva el mensaje, remitente, fotografías,
transcripciones, análisis y JSON originales.

## Autenticación y alcance

- Base: `/api/bot/fuel-reports/`
- Bot: `Authorization: Bearer <OPENCLAW_INGEST_TOKEN>`.
- Dashboard: JWT de un usuario autenticado.
- Valores obligatorios al crear:
  - `organization_key`: `forestal-paraguay`
  - `origin_group_key`: `choferes-fgpy`
- Las escrituras para `forestal-garuhape` y otros grupos son rechazadas.
- Solo el token del bot crea reportes. Solo un usuario JWT confirma, corrige o
  rechaza.

El umbral de confianza se configura con
`FUEL_FIELD_CONFIDENCE_THRESHOLD` (predeterminado `0.80`). El máximo de cada
archivo se configura con `FUEL_EVIDENCE_MAX_BYTES` (predeterminado 10 MiB).
`FGPY_IDENTITY_HASH_KEY` debe configurarse con una clave privada independiente
en el entorno. No debe reutilizar `OPENCLAW_INGEST_TOKEN`; si falta, se rechaza
de forma segura cualquier intento de almacenar un identificador de remitente.

## Crear o recuperar

`POST /api/bot/fuel-reports/`

JSON:

```json
{
  "organization_key": "forestal-paraguay",
  "origin_group_key": "choferes-fgpy",
  "idempotency_key": "choferes-fgpy:2026-07-20:msg-123",
  "event_at": "2026-07-20T10:31:00-03:00",
  "vehicle": "54a07f3b-84c4-49e7-b981-a250d603676b",
  "driver": "568641cb-b9df-457c-b9f8-b3c78a505bf5",
  "liters": "100.00",
  "odometer_total": "12500.00",
  "odometer_partial": null,
  "station": "Estación",
  "receipt_number": "0001-00001234",
  "fuel_type": "Diésel",
  "amount": "950000.00",
  "currency": "PYG",
  "unit_price": "9500.0000",
  "overall_confidence": "0.9200",
  "field_confidence": {
    "vehicle": 0.95,
    "driver": 0.84,
    "liters": 0.98,
    "odometer_total": 0.82,
    "event_at": 0.90,
    "station": 0.75,
    "receipt_number": 0.91,
    "amount": 0.90,
    "unit_price": 0.88
  },
  "original_extraction": {
    "liters_raw": "100 L",
    "odometer_raw": "12500"
  },
  "inconsistencies": [],
  "source_messages": [
    {"message_id": 101, "role": "receipt", "position": 0},
    {"message_id": 102, "role": "dashboard", "position": 1}
  ]
}
```

`vehicle`, `driver`, `liters`, `odometer_total`, `odometer_partial`,
`event_at`, `amount`, `unit_price` y las confianzas pueden ser nulos o
parciales. `vehicle` debe ser un UUID de `forestal_bot_fgpy_vehicle` y `driver`,
un UUID de `forestal_bot_fgpy_driver`. Este flujo no consulta `moviles`,
`personal` ni `cargacomb`, y no resuelve identidades por semejanza textual.

## Catálogos exclusivos FGPY

- `GET|POST /api/bot/fgpy-vehicles/`
- `PATCH /api/bot/fgpy-vehicles/{uuid}/`
- `GET|POST /api/bot/fgpy-drivers/`
- `PATCH /api/bot/fgpy-drivers/{uuid}/`

El bot crea propuestas `pending` con `proposal_key` idempotente y puede
vincular `initial_source_message`. No puede confirmar, aprender aliases ni
fusionar entradas. Un usuario JWT puede crear, corregir, confirmar o desactivar.
La patente original y el nombre informado siempre se conservan. El identificador
de remitente WhatsApp del chofer se conserva solamente como HMAC-SHA256 para
correlación y nunca aparece en las respuestas del dashboard. La misma propuesta
devuelve `200`; reutilizar la clave con otra identidad o mensaje devuelve `409`,
incluso cuando dos solicitudes intentan crearla simultáneamente.

Respuesta: `201` al crear. Repetir la misma clave y los mismos mensajes
devuelve el mismo UUID con `200`, sin actualizar correcciones humanas. Reusar
la clave con otro conjunto de mensajes devuelve `409`.

### Multipart con evidencias

Los mismos campos se envían como partes de formulario. Estos campos contienen
JSON:

- `source_messages`
- `field_confidence`
- `original_extraction`
- `inconsistencies`
- `evidence_types`: lista paralela (`receipt`, `dashboard`, `combined`, `other`)
- `evidence_message_ids`: lista paralela opcional de IDs fuente

Se pueden repetir partes `evidence_files`. Se aceptan JPEG, PNG, WebP y PDF
verificados por firma binaria. El servidor renombra, calcula SHA-256 y nunca
expone la ruta interna. La descarga usa la URL autenticada incluida en
`evidence[].download_url`.

## Consultar y listar

- `GET /api/bot/fuel-reports/{uuid}/`
- `GET /api/bot/fuel-reports/`

Filtros: `organization_key`, `origin_group_key`, `vehicle`, `driver`, `date`
(`YYYY-MM-DD`), `status`, `pending_review`, `page` y `page_size` (máximo 100).
La lista usa el formato paginado DRF: `count`, `next`, `previous`, `results`.

La respuesta incluye las relaciones legibles, mensajes fuente (consultados
desde `WhatsAppMessage`), evidencias y revisiones. No copia esos contenidos al
reporte.

## Corregir, confirmar o rechazar

`PATCH /api/bot/fuel-reports/{uuid}/`

Corrección:

```json
{
  "action": "correct",
  "reason": "Lectura verificada contra tablero",
  "changes": {
    "vehicle": "54a07f3b-84c4-49e7-b981-a250d603676b",
    "driver": "568641cb-b9df-457c-b9f8-b3c78a505bf5",
    "liters": "102.00",
    "odometer_total": "12504.00"
  }
}
```

Confirmación sin cambios:

```json
{"action": "confirm", "reason": ""}
```

Rechazo:

```json
{"action": "reject", "reason": "La imagen no corresponde a una carga"}
```

Cada campo modificado y cada transición de estado crea
`FuelReportRevision`. La extracción automática original no se modifica.
No se permite confirmar si falta vehículo, litros u odómetro total, ni si
alguno conserva una alerta de baja confianza.

## Reglas objetivas

Los códigos admitidos son:

`missing_vehicle`, `missing_liters`, `missing_odometer`,
`low_confidence_vehicle`, `low_confidence_liters`,
`low_confidence_odometer`, `odometer_regression`, `duplicate_receipt`,
`duplicate_evidence`, `possible_duplicate_fuel_event`,
`event_date_mismatch`, `possible_capacity_exceeded`.

Faltantes, confianza baja, regresión de odómetro, comprobantes/evidencias
repetidos o posibles duplicados dejan el reporte en `requires_review`. No
atribuyen fraude ni responsabilidad. La capacidad de tanque no se evalúa sin
un dato real; el bot puede proponer el código para revisión, pero el backend no
inventa esa capacidad.
