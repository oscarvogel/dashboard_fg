# Dashboard Forestal Garuhape (Django + Vue.js)

Este proyecto combina:
- Backend: Django
- Frontend: Vue.js

## Estructura
- `backend/`: API REST con Django
- `frontend/`: Interfaz con Vue.js

## Instalación

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o venv\Scripts\activate en Windows
pip install -r requirements.txt
python manage.py runserver

### Frontend
```bash
cd frontend
npm install
npm run dev

## Reporte de KPIs por Email

Para enviar automáticamente un correo con KPIs y gráficos:

1) Definir destinatarios en `.env` (separados por coma):

```env
KPI_REPORT_TO=gerencia@tu-dominio.com,operaciones@tu-dominio.com
```

2) Ejecutar el comando (usa `KPI_REPORT_TO` si no se pasa `--to`):

```powershell
# Rango específico
python .\backend\manage.py send_kpi_report --start-date 2025-11-01 --end-date 2025-11-30

# Semana anterior (lunes a domingo)
python .\backend\manage.py send_kpi_report --period last-week

# Con filtros por UN y operación
python .\backend\manage.py send_kpi_report --start-date 2025-11-01 --end-date 2025-11-30 --un-ids 1,2 --operaciones VOLTEO,EXTRACCION
```

3) Programación (Windows Task Scheduler): crea una tarea mensual el día 1 a las 07:00 apuntando a:

```powershell
"C:\\Python311\\python.exe" "O:\\forestal\\web\\django\\produccion_api\\backend\\manage.py" send_kpi_report
```
