# Fuente de verdad de tarifas y facturación

Estado del relevamiento: **bloqueado para una API histórica reproducible** (issue #47).

## Definición operativa observada

El proceso vigente está implementado en
`O:/forestal/controladores/ProcesoTarifa.py::ProcesoTarifaController` y lee
`tablero_produccion` y `produccion_mensual`.

Para cada registro de `tablero_produccion` dentro del rango seleccionado:

1. identifica el período con `fecha` en formato `YYYYMM`;
2. busca `produccion_mensual` por período, `cod_un`, operación y equipo, con
   fallback sin equipo;
3. obtiene `coeficiente`, `cotizacion`, `unidad_tarifa` y tarifa mensual;
4. resuelve la tarifa base priorizando la suma de `unitario` de la misma UN,
   operación y rango; luego la tarifa mensual; finalmente `origen.precio`;
5. cuando `cotizacion != 1`, usa la cotización de dólar ingresada manualmente
   al ejecutar el proceso;
6. calcula:

   ```text
   cantidad_valorizada = tablero_produccion.produccion * coeficiente
   valor_unitario = tarifa_base * cotizacion_usada
   total_movimiento = cantidad_valorizada * valor_unitario
   ```

El reporte redondea la cantidad a 2 decimales, la cotización y el valor
unitario a 4, y el total del movimiento a 2.

## Mapeo de datos

| Concepto | Fuente | Columna / regla |
|---|---|---|
| Registro | `tablero_produccion` | `id` |
| Fecha de imputación | `tablero_produccion` | `fecha` |
| Móvil real | `tablero_produccion` | `cod_equipo` → `moviles.idmovil` |
| Unidad de negocio | `tablero_produccion` | `cod_un` |
| Operación | `tablero_produccion` | `operacion` |
| Cantidad base | `tablero_produccion` | `produccion` |
| Unidad producida | `tablero_produccion` | `unidad_produccion` |
| Tarifa por componentes | `tablero_produccion` | suma de `unitario` por UN, operación y rango |
| Tarifa mensual | `produccion_mensual` | `tarifa`, fallback cuando no hay unitarios |
| Coeficiente | `produccion_mensual` | `coeficiente` |
| Unidad facturable | `produccion_mensual` | `unidad_tarifa` |
| Indicador de conversión | `produccion_mensual` | `cotizacion`; valor distinto de 1 requiere dólar manual |
| Fallback transporte | `origen` | `precio` |

Las tablas legacy son externas a Django. Cualquier modelo que se agregue para
leerlas debe conservar `managed = False`.

## Qué persiste y qué no

El proceso actual actualiza `tablero_produccion.tarifa` con la tarifa base. No
persiste junto al movimiento:

- la cotización de dólar ingresada manualmente;
- el coeficiente mensual efectivamente aplicado;
- la unidad de tarifa resuelta;
- el valor unitario convertido;
- el total final del movimiento;
- una moneda explícita.

El esquema productivo inspeccionado no contiene la tabla `moneda` declarada en
el modelo Django. Por lo tanto, no hay una fuente confirmada para etiquetar la
moneda de cada total.

## Consecuencia para `facturacion_total`

En esta versión todavía **no puede definirse un `facturacion_total` histórico
reproducible** usando únicamente los datos persistidos. Usar
`produccion * tarifa` omitiría coeficiente y conversión; usar la cotización
actual reescribiría conceptualmente el pasado. Ambas alternativas se apartan
de la fórmula operativa y quedan prohibidas.

## Decisión necesaria para desbloquear #48–#53

El sistema operativo debe persistir un snapshot auditable por movimiento con,
como mínimo, tarifa base, coeficiente, cotización aplicada, moneda, unidad de
tarifa, cantidad valorizada, total y fecha/hora de cálculo; o debe existir una
fuente histórica equivalente confirmada. La carga de ese snapshot pertenece al
sistema operativo y no debe realizarse desde endpoints analíticos de solo
lectura.

Hasta entonces, los issues dependientes #48–#53 no deben implementar ni
publicar importes que aparenten ser facturación real.
