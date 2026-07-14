# API de consultas de combustible

Los tres endpoints son `GET`, de solo lectura y requieren el mismo JWT Bearer que el resto de la API. No modifican las respuestas de endpoints existentes ni requieren cambios de esquema.

## `GET /api/cargas-combustible/`

Devuelve el detalle paginado de cargas y conserva los totales de ingreso y egreso calculados sobre todo el conjunto filtrado.

- `start_date=YYYY-MM-DD` y `end_date=YYYY-MM-DD`: obligatorios e inclusivos. Un formato inválido o un rango invertido devuelve `400`.
- `page`: entero positivo, default `1`. Un valor inválido o menor o igual a cero devuelve `400`.
- `page_size`: entero positivo, default `50`. Un valor mayor a `200` se limita a `200`; un valor inválido o menor o igual a cero devuelve `400`.
- `un_id`, `movil_id` y `lugar_id`: identificadores enteros positivos opcionales. `movil_id` representa exclusivamente `Equipo.id`/`idmovil`; un texto devuelve `400`.
- `patente`: parámetro independiente, normalizado con trim y comparado de forma exacta sin distinguir mayúsculas y minúsculas contra `Equipo.patente`. No hace búsqueda parcial ni resuelve aliases.

Los filtros se aplican antes de contar, totalizar y paginar. El orden es determinista por `fecha` y luego `id`. Una página posterior a la última devuelve `200` con `results: []` y conserva `count`, `total_pages`, `current_page`, `page_size` y `totales`.

```json
{
  "count": 1013,
  "total_pages": 21,
  "current_page": 1,
  "page_size": 50,
  "results": [],
  "totales": {"Ingreso": 0, "Egreso": 0}
}
```

Los errores de parámetros responden `400`; una petición sin JWT válido responde `401` o `403`, según el autenticador y los permisos configurados.

## Parámetros comunes

- `inicio=YYYY-MM-DD` y `fin=YYYY-MM-DD`: obligatorios, inclusivos.
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
GET /api/combustible-equipo-lh/?inicio=2026-07-01&fin=2026-07-07&un_id=1
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
GET /api/combustible-equipo-vs-historico/?inicio=2026-07-01&fin=2026-07-07&meses_atras=6
```

La respuesta contiene `periodo_actual`, `periodo_historico`, litros, horas, L/h de ambos períodos, diferencias, semáforo y advertencias por equipo.

## `GET /api/combustible-sin-produccion/`

Agrupa los egresos por `(fecha local, equipo_id)` y devuelve aquellos sin una fila de `tablero_produccion` con la misma `(fecha, cod_equipo_id)`. Varias cargas del mismo equipo y día producen un solo hallazgo.

```http
GET /api/combustible-sin-produccion/?inicio=2026-07-01&fin=2026-07-07&movil_id=123
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

- `400 Bad Request`: parámetros faltantes o inválidos. Ejemplo: `{"fin":["Debe ser igual o posterior a inicio."]}`.
- `401 Unauthorized`: JWT ausente, vencido o inválido.
- `403 Forbidden`: usuario autenticado sin permiso, si se agregan permisos más restrictivos en el futuro.
- `404 Not Found`: ruta inexistente o recurso individual inexistente; estos endpoints agregados no buscan un recurso individual y normalmente devuelven `200` con `results: []` cuando no hay datos.
