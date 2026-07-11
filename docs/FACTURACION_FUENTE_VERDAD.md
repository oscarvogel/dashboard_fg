# Fuente de verdad de tarifas y facturación

Estado del relevamiento: **completo** (issue #47).

`oscarvogel/forestal` se utilizó solamente como referencia funcional para
comprender la fórmula observada. El producto, sus servicios y sus endpoints se
implementan íntegramente en `dashboard_fg`, usando exclusivamente su base de
datos. No existe importación, ejecución, lectura de rutas locales ni dependencia
de despliegue entre ambos repositorios.

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

El esquema productivo no contiene la tabla singular `moneda` declarada en el
modelo Django: la tabla real se llama `monedas`. Contiene los catálogos ARS y
USD, pero no existe una FK o columna que vincule una moneda con
`tablero_produccion`, `produccion_mensual` o `tarifa_produccion`. Por lo tanto,
el catálogo no permite etiquetar la moneda de cada total.

Aunque `produccion_mensual.cotizacion` conserva valores distintos de 1 en
algunos períodos, no es un snapshot del valor aplicado: el controlador sólo lo
usa como indicador para decidir si debe reemplazarlo por el dólar ingresado
manualmente al ejecutar. El valor manual efectivo tampoco queda persistido.

## Consecuencia para `facturacion_total`

`facturacion_total` sólo contiene un importe histórico cuando todos los
componentes necesarios están persistidos y el cálculo es reproducible. Usar
`produccion * tarifa` omitiendo componentes o usar una cotización actual como
si fuera histórica está prohibido.

La ausencia de componentes no bloquea la API: produce un resultado parcial y
explicable. Una cotización aportada expresamente por el consumidor genera un
importe separado de simulación y nunca completa ni reemplaza
`facturacion_total`.

## Estados del cálculo

- `calculado`: todos los componentes y la moneda están confirmados; el total es
  histórico y reproducible.
- `parcial`: existen producción y tarifa, pero falta otro componente distinto
  de una cotización histórica requerida.
- `requiere_cotizacion`: la valorización requiere una cotización histórica que
  no está persistida.
- `simulacion`: el consumidor proporcionó expresamente una cotización; el
  resultado se devuelve sólo como `facturacion_simulada`.
- `sin_tarifa`: existe actividad pero no una tarifa base válida.
- `sin_actividad`: el móvil no tiene registros dentro del período.
- `datos_incompatibles`: las relaciones, unidades o monedas no permiten un
  cálculo coherente.

## Implementación desacoplada en `dashboard_fg`

El servicio propio de `dashboard_fg` lee `tablero_produccion`,
`produccion_mensual`, `origen` y `monedas` mediante modelos locales. Devuelve
siempre los componentes disponibles, faltantes, advertencias y cobertura. No
escribe cotizaciones, tarifas, producción ni snapshots.

Una futura persistencia de snapshot auditable podrá aumentar la cobertura de
`calculado` sin cambiar el contrato: tarifa base, coeficiente, cotización,
moneda, unidad de tarifa, cantidad valorizada, total y fecha/hora de cálculo.
