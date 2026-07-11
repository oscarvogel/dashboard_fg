# API de facturación e indicadores para OpenClaw

Este contrato pertenece exclusivamente a `dashboard_fg`. OpenClaw no debe
acceder, importar ni ejecutar el repositorio `forestal`.

## Autenticación y seguridad

Todos los endpoints usan SimpleJWT:

```http
Authorization: Bearer <access-token>
```

Sin JWT válido responden `401`. Sólo admiten `GET`; `POST`, `PUT`, `PATCH` y
`DELETE` responden `405`. Nunca se deben registrar ni mostrar tokens.

## Parámetros comunes

- `start_date`, `end_date`: fechas `YYYY-MM-DD`, inclusivas y obligatorias.
- `movil_id`: entero positivo y obligatorio en consultas de un móvil.
- `un_id`: entero positivo opcional.
- rango máximo: 366 días.
- `cotizacion`: decimal positivo opcional; siempre produce una simulación.
- `moneda`: `ARS` o `USD`; en consultas individuales sólo acompaña una
  simulación.

Una simulación nunca completa `facturacion_total`: se devuelve separadamente
como `facturacion_simulada`.

## Definición de facturación

La fórmula independiente implementada por `dashboard_fg` es:

```text
cantidad_valorizada = produccion × coeficiente
valor_unitario = tarifa_base × cotizacion
total = cantidad_valorizada × valor_unitario
```

Fuentes locales: `tablero_produccion`, `produccion_mensual`, `origen` y
`monedas`. La fecha es `tablero_produccion.fecha`; el móvil se cruza por
`cod_equipo`. El detalle completo está en
[`FACTURACION_FUENTE_VERDAD.md`](FACTURACION_FUENTE_VERDAD.md).

Estados posibles:

- `calculado`: histórico reproducible;
- `parcial`: faltan componentes no financieros o de trazabilidad;
- `requiere_cotizacion`: no está la cotización histórica aplicada;
- `simulacion`: se usó la cotización de la consulta;
- `sin_tarifa`;
- `sin_actividad`;
- `datos_incompatibles`.

No se suman monedas ni unidades incompatibles. Los importes y cantidades se
serializan como strings decimales.

## Resolver primero el móvil

```http
GET /api/equipos/?q=CHI-3
```

La búsqueda usa ID, patente, código, descripción y aliases activos confirmados.
Cada resultado incluye `match_type`, `match_score`; la respuesta incluye
`requires_confirmation`.

- Si hay una coincidencia única confiable, usar su `id` como `movil_id`.
- Si `requires_confirmation=true`, pedir al usuario que elija.
- Nunca seleccionar silenciosamente el primer resultado.
- Nunca crear ni reactivar aliases durante una consulta analítica.

## Facturación de un móvil

```http
GET /api/indicadores/facturacion-movil/?start_date=2026-07-01&end_date=2026-07-07&movil_id=208
```

Devuelve `movil`, `periodo`, `estado_calculo`, `totales_por_moneda`,
`totales_simulados_por_moneda`, `cantidades_por_unidad`, `desglose`,
`registros`, `cobertura` y `advertencias`.

Ejemplo sanitizado incompleto:

```json
{
  "movil": {"id": 208, "patente": "MÓVIL-SANITIZADO"},
  "periodo": {"start_date": "2026-07-01", "end_date": "2026-07-07"},
  "estado_calculo": "requiere_cotizacion",
  "totales_por_moneda": [],
  "totales_simulados_por_moneda": [],
  "cobertura": {"porcentaje_calculado": "0.00", "completa": false}
}
```

Simulación explícita:

```http
GET /api/indicadores/facturacion-movil/?start_date=2026-07-01&end_date=2026-07-07&movil_id=208&cotizacion=1325.000000&moneda=ARS
```

El resultado usa `estado_calculo=simulacion`, deja el histórico en `null` y
advierte que no representa necesariamente la facturación efectiva.

## Cruce operativo

```http
GET /api/indicadores/movil-operativo/?start_date=2026-07-01&end_date=2026-07-07&movil_id=208&compare=previous_period
```

`compare` admite `none` (default) y `previous_period`. El período anterior
termina el día previo y tiene exactamente la misma cantidad de días.

Bloques: `facturacion`, `produccion`, `combustible`, `indicadores`,
`comparacion_periodo_anterior`, `calidad_datos`.

Los ratios sin numerador o denominador válido son `null` y aparecen en
`razones_no_disponibles`. Los ratios simulados usan nombres separados:

- `facturacion_simulada_por_litro`;
- `facturacion_simulada_por_hora`;
- `facturacion_simulada_por_unidad`.

### Semántica cross-UN

Sin `un_id`, producción y combustible se cruzan por `movil_id` y fecha aunque
procedan de UN diferentes. Con `un_id`, el filtro se aplica independientemente
a `tablero_produccion.cod_un` y `cargacomb.UnidadNegocio`; nunca se unen filas
por nombres.

## Ranking

```http
GET /api/indicadores/moviles-ranking/?start_date=2026-07-01&end_date=2026-07-07&metric=litros_combustible&page=1&page_size=5
```

Métricas permitidas:

- `facturacion_total`, `facturacion_por_litro`, `facturacion_por_hora`;
- `litros_combustible`, `horas_trabajadas`;
- `produccion`, `produccion_por_litro`, `litros_por_unidad_producida`;
- `cobertura`.

Las financieras exigen `moneda`. Las productivas exigen `unidad`. `order`
admite `asc|desc`; `page_size` máximo es 100. Sólo cálculos históricos
`calculado` participan en rankings financieros. Los demás aparecen en
`datos_insuficientes`. Las simulaciones no se mezclan con el ranking histórico.

## Errores

- `400`: fecha ausente/inválida, rango invertido/excesivo, ID/filtro inválido,
  métrica no permitida, moneda o unidad requerida.
- `401`: JWT ausente, vencido o inválido.
- `404`: `movil_id` inexistente en endpoints individuales.
- `405`: método distinto de GET/HEAD/OPTIONS.

Un móvil existente sin actividad devuelve `200` con `sin_actividad`; actividad
sin tarifa devuelve `sin_tarifa`. Los faltantes no se convierten en cero.

## Secuencia obligatoria de OpenClaw

1. Obtener o renovar JWT mediante la integración existente, sin mostrarlo.
2. Buscar la referencia humana en `/api/equipos/`.
3. Pedir aclaración si la respuesta es ambigua.
4. Usar exclusivamente el `movil_id` resuelto.
5. Consultar facturación, cruce operativo o ranking.
6. Mantener separadas monedas, unidades, históricos y simulaciones.
7. Informar período, estado, cobertura, faltantes y advertencias.
8. Responder en español y distinguir facturación de rentabilidad.
9. No realizar escrituras ni crear aliases durante el test.
