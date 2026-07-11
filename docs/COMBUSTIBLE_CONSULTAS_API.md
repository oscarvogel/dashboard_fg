# API de consultas de combustible

Los tres endpoints son `GET`, de solo lectura y requieren el mismo JWT Bearer que el resto de la API. No modifican las respuestas de endpoints existentes ni requieren cambios de esquema.

## Parámetros comunes

- `start_date=YYYY-MM-DD` y `end_date=YYYY-MM-DD`: parámetros recomendados, obligatorios e inclusivos.
- `inicio=YYYY-MM-DD` y `fin=YYYY-MM-DD`: aliases retrocompatibles para consumidores existentes.
- Se debe enviar un par completo. No se permite mezclar nombres incompletos, por ejemplo `start_date` con `fin`.
- Si se envían ambos pares, deben representar exactamente el mismo rango; de lo contrario la API devuelve `400`.
- `un_id`: entero positivo opcional; filtra `CargaCombustible.unidad_negocio_id` y `RegistroProduccion.cod_un_id`.
- `movil_id`: entero positivo opcional; filtra la FK real `CargaCombustible.equipo_id` / `RegistroProduccion.cod_equipo_id`.
- El rango máximo es de 366 días. Un formato inválido, rango invertido o identificador no positivo devuelve `400`.

Las fechas de ambas tablas son `DateField`, no timestamps UTC. La comparación diaria usa directamente la fecha local de negocio (`America/Argentina/Buenos_Aires`), por lo que no aplica conversiones que puedan desplazar un registro al día anterior o siguiente.

## `GET /api/combustible-equipo-lh/`

Calcula por equipo:

```text
litros_egreso = SUM(cargacomb.litros) donde tipo_mov = "E"
horas_operativas = SUM(hr_fin - hr_inicio) por registro donde hr_fin > hr_inicio
litros_por_hora = litros_egreso / horas_operativas
```

Los ingresos (`tipo_mov="I"`) quedan excluidos. Los intervalos con horas cero o negativas no se suman y generan una advertencia; si no quedan horas válidas, `litros_por_hora` es `null`. Combustible y producción se agregan en consultas separadas antes de combinarse por ID, evitando duplicaciones por joins.

Ejemplo:

```http
GET /api/combustible-equipo-lh/?start_date=2026-07-01&end_date=2026-07-07&un_id=1
Authorization: Bearer <token>
```

```json
{
  "inicio": "2026-07-01",
  "fin": "2026-07-07",
  "results": [{
    "equipo_id": 123,
    "equipo": "Tigercat 875",
    "unidad_negocio": "FULL TREE",
    "litros_egreso": 850.0,
    "horas_operativas": 42.5,
    "litros_por_hora": 20.0,
    "cantidad_cargas": 5,
    "registros_produccion": 7,
    "warnings": []
  }],
  "totales": {},
  "data_quality": {}
}
```

Los nombres `inicio` y `fin` de la respuesta se mantienen para no romper consumidores existentes.

## `GET /api/combustible-equipo-vs-historico/`

Admite además `meses_atras` (entero de 1 a 60, default 6). Compara contra el mismo rango calendario desplazado con meses naturales.

```text
diferencia_absoluta = L/h actual - L/h histórico
variacion_porcentual = diferencia_absoluta / L/h histórico * 100
```

No se calcula porcentaje si el L/h histórico es cero o nulo. Los umbrales iniciales, centralizados como constantes configurables, son:

- `verde`: variación menor o igual a +5 %.
- `amarillo`: mayor a +5 % y menor o igual a +15 %.
- `rojo`: mayor a +15 %.
- `sin_datos`: base histórica nula/cero o muestra insuficiente.

Estos valores son iniciales y no constituyen reglas definitivas de negocio.

```http
GET /api/combustible-equipo-vs-historico/?start_date=2026-07-01&end_date=2026-07-07&meses_atras=6
```

La respuesta contiene `periodo_actual`, `periodo_historico`, litros, horas, L/h de ambos períodos, diferencias, semáforo y advertencias por equipo.

## `GET /api/combustible-sin-produccion/`

Agrupa los egresos por `(fecha local, equipo_id)` y devuelve aquellos sin una fila de `tablero_produccion` con la misma `(fecha, cod_equipo_id)`. Varias cargas del mismo equipo y día producen un solo hallazgo.

```http
GET /api/combustible-sin-produccion/?start_date=2026-07-01&end_date=2026-07-07&movil_id=123
```

```json
{
  "inicio": "2026-07-01",
  "fin": "2026-07-07",
  "results": [{
    "fecha": "2026-07-01",
    "equipo_id": 123,
    "equipo": "Tigercat 875",
    "unidad_negocio": "FULL TREE",
    "litros_egreso": 150.0,
    "cantidad_cargas": 2,
    "motivo": "Egreso sin registro de producción compatible en la misma fecha; inconsistencia para revisión, no error definitivo."
  }],
  "data_quality": {
    "cargas_sin_equipo_identificado": 0,
    "cargas_con_equipo_id_huerfano": 0
  }
}
```

El hallazgo es una señal para revisión, no prueba de fraude ni de error definitivo. Si la operación registra producción al día siguiente o atraviesa medianoche, la comparación estricta por fecha puede generar un falso positivo; no se amplía automáticamente la ventana porque no existe una regla de turnos confirmada en el esquema.

## Errores

- `400 Bad Request`: parámetros faltantes o inválidos. Ejemplos:
  - rango invertido: `{"fin":["Debe ser igual o posterior a inicio."]}`;
  - nombres incompletos o mezclados: `{"date_range":["Debe enviar juntos start_date y end_date..."]}`;
  - ambos pares con rangos diferentes: `{"date_range":["start_date/end_date e inicio/fin deben representar el mismo rango..."]}`.
- `401 Unauthorized`: JWT ausente, vencido o inválido.
- `403 Forbidden`: usuario autenticado sin permiso, si se agregan permisos más restrictivos en el futuro.
- `404 Not Found`: ruta inexistente o recurso individual inexistente; estos endpoints agregados no buscan un recurso individual y normalmente devuelven `200` con `results: []` cuando no hay datos.
