# Paginación de cargas de combustible

## Objetivo

Corregir `GET /api/cargas-combustible/` para que entregue páginas reales, conserve la autenticación y la forma compatible de `results` y `totales`, y calcule los totales sobre el conjunto filtrado completo.

## Contrato HTTP

- `start_date` y `end_date` son obligatorios en formato `YYYY-MM-DD`; fechas inválidas o un rango invertido responden `400`.
- `page` es entero positivo, por defecto `1`; un valor no entero o menor o igual a cero responde `400`.
- `page_size` es entero positivo, por defecto `50`; un valor no entero o menor o igual a cero responde `400`. Los valores mayores a `200` se limitan a `200`.
- Una página posterior a la última responde `200`, con `results: []`, y conserva los metadatos y totales del conjunto filtrado.
- `un_id`, `movil_id` y `lugar_id` son identificadores enteros. Un valor no entero responde `400`; en particular, `movil_id` nunca acepta patentes ni alias.
- `patente` es un parámetro separado. Se normaliza con `trim` y se compara exactamente, sin distinguir mayúsculas y minúsculas, contra `Equipo.patente`. Una patente inexistente produce un conjunto vacío.
- La resolución de alias queda fuera de este endpoint y debe realizarse previamente mediante el catálogo de equipos.
- El endpoint permanece protegido por `IsAuthenticated`; sin autenticación responde `401` o `403`, según el autenticador configurado.

## Flujo de datos

La vista validará primero los parámetros. Luego construirá el queryset por rango de fechas, aplicará los filtros opcionales y mantendrá `select_related` para equipo, unidad de negocio y lugar de carga. El queryset filtrado se ordenará obligatoriamente por `fecha` e `id`.

Antes de extraer la página se calcularán `count` y los totales de ingreso y egreso sobre todo el queryset filtrado. Después se calculará `total_pages` y se extraerá la ventana solicitada. Este corte explícito permite que una página fuera de rango sea una respuesta válida y vacía.

## Respuesta

La respuesta exitosa tendrá esta forma:

```json
{
  "count": 1013,
  "total_pages": 21,
  "current_page": 1,
  "page_size": 50,
  "results": [],
  "totales": {
    "Ingreso": 0,
    "Egreso": 0
  }
}
```

`results` conserva el serializer actual. `totales` conserva las claves `Ingreso` y `Egreso` en todas las páginas.

## Pruebas y consultas

Las pruebas del endpoint cubrirán autenticación, parámetros inválidos, filtros por cada identificador y patente, límite de tamaño, página fuera de rango, totales globales y estables, orden determinista, ausencia de duplicados entre páginas y unión exacta de todas las páginas. También comprobarán que la serialización paginada mantiene `select_related` y evita N+1.

La validación productiva será de solo lectura para `2026-06-01` a `2026-07-11`: comprobará el total actual, tamaños de página, hashes distintos para las primeras tres páginas y unicidad/exhaustividad al recorrer todas las páginas. No se imprimirán credenciales.

## Alcance

No se modificarán OpenClaw, el frontend, modelos ni migraciones. El cambio queda limitado a la vista, sus pruebas y la documentación del contrato.
