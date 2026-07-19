# API de pesajes de Forestal Paraguay

Contrato backend para movimientos originados normalmente en `logistica-felber`.
Todas las rutas requieren `Authorization: Bearer <OPENCLAW_INGEST_TOKEN>` y
usan como base `/api/forestal-bot/weighing-movements/`.

## Reglas del contrato

- `organization_key` sólo acepta `forestal-paraguay`.
- Cada movimiento declara `official_scale`; el backend no la infiere.
- Los pesos son enteros en kg. El neto no se persiste: siempre es `bruto - tara`.
- `declared_quantity_kg` es un control de remisión independiente.
- Una corrección conserva todas las revisiones.
- Repetir la misma `idempotency_key` y contenido no duplica datos.
- Reusar una clave de medición con otro contenido devuelve `409`.
- Los totales efectivos sólo incluyen movimientos `completo` con neto oficial positivo.

## Registrar solamente una tara

Crear el movimiento:

```http
POST /api/forestal-bot/weighing-movements/
```

```json
{
  "idempotency_key": "felber:2026-07-18:acb190",
  "organization_key": "forestal-paraguay",
  "origin_group_key": "logistica-felber",
  "operational_date": "2026-07-18",
  "plate_original": "ACB 190",
  "driver_name": "David Coronel",
  "status": "pendiente",
  "official_scale": "felber",
  "evidence": [{"type": "remision", "id": "remision-msg-10"}],
  "source_message_ids": ["remision-msg-10"]
}
```

Agregar la tara al UUID devuelto:

```http
POST /api/forestal-bot/weighing-movements/{movement_id}/measurements/
```

```json
{
  "idempotency_key": "felber:2026-07-18:acb190:felber:tara:v1",
  "scale": "felber",
  "kind": "tara",
  "weight_kg": 16020,
  "source": "foto_balanza",
  "evidence_id": "foto-ingreso-10",
  "message_id": "wa-ingreso-10",
  "measured_at": "2026-07-18T08:31:00-03:00"
}
```

El movimiento continúa `pendiente`.

## Incorporar bruto y cerrar

```json
{
  "idempotency_key": "felber:2026-07-18:acb190:felber:bruto:v1",
  "scale": "felber",
  "kind": "bruto",
  "weight_kg": 58340,
  "net_kg": 42320,
  "source": "foto_balanza",
  "evidence_id": "foto-salida-10",
  "message_id": "wa-salida-10",
  "measured_at": "2026-07-18T16:42:00-03:00"
}
```

Con báscula oficial declarada, tara y bruto positivos, el movimiento pasa de
`pendiente` a `completo`. `net_kg` es una aserción opcional: si no coincide con
el cálculo, toda la solicitud se rechaza.

Cierre explícito alternativo:

```http
POST /api/forestal-bot/weighing-movements/{movement_id}/complete/
```

```json
{"official_scale": "felber"}
```

## Patente, chofer y remisión

Repetir el `POST` del movimiento con la misma `idempotency_key`:

```json
{
  "idempotency_key": "felber:2026-07-18:acb190",
  "organization_key": "forestal-paraguay",
  "origin_group_key": "logistica-felber",
  "operational_date": "2026-07-18",
  "plate_original": "ACB 190",
  "driver_name": "David Coronel",
  "status": "pendiente",
  "declared_quantity_kg": 42330,
  "official_scale": "felber",
  "evidence": [{"type": "remision", "id": "remision-msg-10"}],
  "source_message_ids": ["remision-msg-10"]
}
```

La respuesta expone `plate_normalized: "ACB190"`. Los 42.330 kg declarados
nunca se convierten en tara, bruto o neto.

## Segunda báscula

Agregar las siguientes dos mediciones al mismo movimiento:

```json
{
  "idempotency_key": "felber:2026-07-18:acb190:fp:tara:v1",
  "scale": "forestal_paraguay",
  "kind": "tara",
  "weight_kg": 15910,
  "source": "foto_balanza",
  "evidence_id": "foto-fp-ingreso-10",
  "message_id": "wa-fp-ingreso-10",
  "measured_at": "2026-07-18T09:02:00-03:00"
}
```

```json
{
  "idempotency_key": "felber:2026-07-18:acb190:fp:bruto:v1",
  "scale": "forestal_paraguay",
  "kind": "bruto",
  "weight_kg": 57380,
  "source": "foto_balanza",
  "evidence_id": "foto-fp-salida-10",
  "message_id": "wa-fp-salida-10",
  "measured_at": "2026-07-18T17:05:00-03:00"
}
```

Fragmento relevante del detalle:

```json
{
  "calculated_nets_kg": {
    "felber": 42320,
    "forestal_paraguay": 41470
  },
  "comparisons_kg": {
    "felber_minus_forestal_paraguay": {
      "tara": 110,
      "bruto": 960,
      "neto": 850
    }
  },
  "declared_vs_official_net_kg": 10
}
```

Las diferencias son comparativas; no atribuyen descalibración.

## Idempotencia y corrección

Repetir exactamente una medición devuelve `200`, `"replayed": true` y no
crea una revisión. Para corregirla, usar una clave nueva sobre la misma
combinación movimiento/báscula/tipo:

```json
{
  "idempotency_key": "felber:2026-07-18:acb190:felber:tara:correction-1",
  "scale": "felber",
  "kind": "tara",
  "weight_kg": 16010,
  "source": "correccion_manual",
  "evidence_id": "control-usuario-25",
  "message_id": "",
  "measured_at": "2026-07-18T08:31:00-03:00",
  "correction_reason": "Lectura verificada contra ticket"
}
```

La respuesta incluye `revisions` con lectura original y corregida.

## Consultas

```http
GET /api/forestal-bot/weighing-movements/{movement_id}/
GET /api/forestal-bot/weighing-movements/?organization_key=forestal-paraguay&date_from=2026-07-01&date_to=2026-07-31&plate=ACB190&driver=David&status=completo&origin_group_key=logistica-felber
GET /api/forestal-bot/weighing-movements/summary/?period=daily&date_from=2026-07-18&date_to=2026-07-18
```

Para semana o mes usar `period=weekly` o `period=monthly`. Cada bloque incluye
conteos por estado, `effective_net_kg`, `effective_net_tonnes`, totales por
báscula, diferencias acumuladas e IDs incluidos/excluidos.
