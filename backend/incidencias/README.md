# API de incidencias operativas

Registro persistente para el bot Forestal. Todos los endpoints usan
`Authorization: Bearer <OPENCLAW_INGEST_TOKEN>` y fechas ISO 8601 con zona
horaria.

El alcance organizacional aceptado es `forestal-paraguay`; una organización
distinta se rechaza con `400`. Las incidencias conservan además
`grupo_origen_key` y `grupo_origen_nombre` para que seguimiento y cierre no
mezclen grupos operativos.

## Endpoints

- `POST/GET /api/incidencias/equipos/`: crea o consulta incidencias de equipos.
- `POST /api/incidencias/equipos/<id>/eventos/`: agrega una transicion inmutable.
- `POST /api/incidencias/equipos/<id>/cerrar/`: registra el primer retorno operativo y cierra.
- `POST/GET /api/incidencias/personas/`: crea o consulta incidencias de personal.
- `POST /api/incidencias/personas/<id>/cerrar/`: cierra una incidencia de personal confirmada.
- `GET /api/incidencias/dashboard/`: consulta autenticada para el dashboard.
- `GET /api/incidencias/horas-paradas/?inicio=<ISO>&fin=<ISO>&equipo_id=<id>`.
- `GET /api/incidencias/por-persona/?inicio=YYYY-MM-DD&fin=YYYY-MM-DD`.
- `GET /api/incidencias/resumen-mensual/?periodo=YYYY-MM`.
- `GET /api/incidencias/resolver/?tipo=equipo|persona&q=<texto>`.

El resolver responde un objeto estable con `estado`: `sin_coincidencias`,
`coincidencia_unica` o `requiere_confirmacion`. En todos los casos incluye
`resultados`; para la coincidencia única también incluye `resultado`.

Las listas aceptan filtros por periodo, ID real, tipo y estado. Cada alta o
cambio proveniente de WhatsApp debe enviar un `source_message_id`; la base
reproduce idempotentemente el recurso existente para IDs repetidos. Las horas paradas se reconstruyen desde eventos
confirmados y se unen por equipo, de modo que incidencias superpuestas no suman
dos veces el mismo intervalo.

Las incidencias nuevas de equipos y personal requieren `grupo_origen_key` y
`grupo_origen_nombre`. Estos campos permiten seguimiento en el grupo correcto,
filtros e informes sin depender de texto libre.
