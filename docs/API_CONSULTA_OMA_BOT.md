# API de consulta de OMA para el bot Forestal

Endpoints de sólo lectura protegidos con `Authorization: Bearer <OPENCLAW_INGEST_TOKEN>`.
No exponen costos, repuestos, mecánicos, usuarios ni otras personas asociadas.

## Consulta por referencia

`GET /api/mantenimiento/ordenes/<referencia>/`

La referencia se interpreta primero como `cab_orden_servicio.id` cuando es
numérica. Si ese ID no existe, o si la referencia no es numérica, se busca una
coincidencia exacta en `orden_servicio`.

Una coincidencia devuelve `200` con la cabecera, el equipo, los detalles
operativos y evidencia explícita de cierre. `cerrada` sólo es `true` cuando
`estado`, sin espacios laterales y sin distinguir mayúsculas, es `cerrado`.
Las tareas realizadas nunca cierran por sí solas una cabecera pendiente.

Si `orden_servicio` está vacío, `referencia_visible` es `OMA <id>`.

Sin coincidencia:

```json
{"encontrada": false, "referencia": "2044"}
```

El estado HTTP es `404`. Si el número formal coincide con más de una cabecera,
el estado es `409` y `candidatos` contiene únicamente ID, número/referencia,
fecha, estado, equipo y descripción. La API nunca selecciona uno en silencio.

## Búsqueda asistida

`GET /api/mantenimiento/ordenes/estado/`

Parámetros:

- `equipo_id`: ID interno del equipo.
- `fecha_desde`: fecha mínima inclusive, formato `YYYY-MM-DD`.
- `descripcion`: texto contenido en la descripción, sin distinguir mayúsculas.
- `limite`: opcional, 10 por defecto y 20 como máximo.

Debe indicarse al menos un filtro. Los resultados se ordenan por fecha,
creación e ID descendentes. La respuesta usa uno de estos valores:

- `resultado: "coincidencia_unica"` y el objeto completo en `orden`.
- `resultado: "candidatos"` y una lista mínima en `candidatos`.
- `resultado: "sin_coincidencias"` y una lista vacía.

Ejemplo:

```http
GET /api/mantenimiento/ordenes/estado/?equipo_id=282&fecha_desde=2026-07-01&descripcion=mangueras
Authorization: Bearer <token>
```

La autenticación ausente o inválida devuelve `403`. Ambos endpoints aceptan
exclusivamente `GET` y usan relaciones precargadas para mantener acotada la
cantidad de consultas.
