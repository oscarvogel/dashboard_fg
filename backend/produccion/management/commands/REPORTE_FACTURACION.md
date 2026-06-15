# Reporte Diario de Facturación

Este archivo describe el comando de management `reporte_facturacion`.

Uso:

```bash
python manage.py reporte_facturacion --date DD-MM-YYYY
```

Formatos de fecha aceptados: `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`

Descripción:

- Genera un HTML por unidad de negocio con formato visual verde pastel.
- **Para FT y CTL**: Suma la facturación de `PROCESO` y `CARGA` y presenta UNA línea agregada por unidad de negocio (todos los equipos juntos).
- **Para BIOMASA**: Solo considera operaciones de `CHIPEADO` y presenta el detalle por equipo.
- Calcula un `Plan` de día/mes a partir de la producción mensual (tabla `ProduccionMensual`) y lo convierte a montos usando tarifa promedio ponderada por equipo.
- Guarda el archivo `reporte_facturacion_YYYYMMDD.html` en el directorio actual y, si está configurado, lo sube por FTP (variables `FTP_HOST`, `FTP_USER`, `FTP_PASSWORD`, `FTP_DIR`).

Ejemplo:

```bash
python manage.py reporte_facturacion --date 07-02-2025
```
