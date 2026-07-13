# API de incidencias operativas

Registro persistente para el bot de Forestal Garuhape. Todos los endpoints usan
`Authorization: Bearer <OPENCLAW_INGEST_TOKEN>` y fechas ISO 8601 con zona
horaria.

## Endpoints

- `POST/GET /api/incidencias/equipos/`: crea o consulta incidencias de equipos.
- `POST /api/incidencias/equipos/<id>/eventos/`: agrega una transicion inmutable.
- `POST /api/incidencias/equipos/<id>/cerrar/`: registra el primer retorno operativo y cierra.
- `POST/GET /api/incidencias/personas/`: crea o consulta incidencias de personal.
- `GET /api/incidencias/horas-paradas/?inicio=<ISO>&fin=<ISO>&equipo_id=<id>`.
- `GET /api/incidencias/por-persona/?inicio=YYYY-MM-DD&fin=YYYY-MM-DD`.
- `GET /api/incidencias/resumen-mensual/?periodo=YYYY-MM`.
- `GET /api/incidencias/resolver/?tipo=equipo|persona&q=<texto>`.

Las listas aceptan filtros por periodo, ID real, tipo y estado. Cada alta o
cambio proveniente de WhatsApp debe enviar un `source_message_id`; la base
rechaza IDs repetidos. Las horas paradas se reconstruyen desde eventos
confirmados y se unen por equipo, de modo que incidencias superpuestas no suman
dos veces el mismo intervalo.
