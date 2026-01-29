# Instrucciones para el Reporte Diario de Producción

Este documento detalla el uso del comando de gestión de Django desarrollado para generar, enviar por correo y subir vía FTP el reporte diario de producción y consumo.

## 1. Configuración Previa

Asegúrese de que el archivo `backend/.env` contenga las siguientes variables configuradas correctamente:

### Configuración de Correo
Destinatarios por defecto para el reporte diario. Se pueden separar múltiples correos por comas.
```env
DAILY_REPORT_TO=correo1@ejemplo.com,correo2@ejemplo.com
# Si DAILY_REPORT_TO no existe, el sistema intentará usar KPI_REPORT_TO
```

### Configuración de FTP
Datos de conexión para subir el archivo HTML generado.
```env
FTP_HOST=vps-3177145-x.dattaweb.com
FTP_USER=su_usuario
FTP_PASSWORD=su_contraseña
FTP_DIR=/public_html/reportes
```

## 2. Uso del Comando

El comando se ejecuta desde la terminal, ubicándose en la carpeta raíz del proyecto donde se encuentra el entorno virtual (o activando el entorno antes).

**Comando base:**
```powershell
python backend/manage.py reporte_diario
```

### Opciones Disponibles

1.  **Generar reporte de ayer (Por defecto)**
    Si no se especifica ninguna opción, el sistema genera el reporte correspondiente al día anterior a la fecha actual.
    ```powershell
    python backend/manage.py reporte_diario
    ```

2.  **Generar reporte de una fecha específica (`--date`)**
    Utilice el formato `YYYY-MM-DD`.
    ```powershell
    python backend/manage.py reporte_diario --date 2026-01-20
    ```

3.  **Enviar a un correo específico (`--email`)**
    Sobrescribe los destinatarios configurados en el `.env`. Útil para pruebas o envíos puntuales.
    ```powershell
    python backend/manage.py reporte_diario --email destinatario@prueba.com
    ```
    También funciona combinado con la fecha:
    ```powershell
    python backend/manage.py reporte_diario --date 2026-01-20 --email destinatario@prueba.com
    ```

## 3. Comportamiento del Sistema

Al ejecutar el comando, el sistema realiza secuencialmente:

1.  **Cálculo de Datos**:
    *   **Proceso**: Filtra operaciones "PROCESO". Calcula M3, Horas, y ratios de consumo.
    *   **Chipeado**: Filtra operaciones "CHIPEADO" (y variantes). Calcula TN, Horas, y ratios.
    *   **Otros y Viales**: Suma combustible total y calcula consumo medio (L/Hr) basado en los últimos 30 días.
    *   **Horas No Operativas**: Lista equipos con incidencias en el día o acumuladas en el mes.

2.  **Generación de Archivo**:
    *   Crea un archivo HTML con tablas formateadas.
    *   Nombre del archivo: `reporte_YYYYMMDD.html`.

3.  **Subida FTP**:
    *   Se conecta al servidor FTP configurado.
    *   Sube el archivo HTML al directorio especificado en `FTP_DIR`.
    *   Si fallan las credenciales, muestra un aviso en consola pero continúa con el envío de correo.

4.  **Envío de Correo**:
    *   Envía un email con el asunto "Reporte Diario Producción - DD/MM/YYYY".
    *   El archivo HTML se adjunta al correo y también se renderiza en el cuerpo (dependiendo del cliente de correo).
    *   Si no hay destinatarios configurados ni pasados por argumento, guarda el archivo HTML localmente para inspección.

## 4. Automatización

Para ejecutar esto automáticamente todos los días, puede configurar una Tarea Programada en Windows o un Cron en Linux.

**Ejemplo para Tarea Programada (Windows):**
*   **Programa/Script**: `H:\venv\ecommerce\Scripts\python.exe` (Ruta a su Python del entorno virtual)
*   **Argumentos**: `O:\forestal\web\django\produccion_api\backend\manage.py reporte_diario`
*   **Iniciar en**: `O:\forestal\web\django\produccion_api`
