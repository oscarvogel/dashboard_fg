# Dashboard Forestal Garuhape (Django + Vue.js)

# Dashboard Forestal Garuhapé

Proyecto fullstack para gestión y visualización de producción forestal.

**Stack principal**
- Backend: Django 5.x + Django REST Framework
- Base de datos: MySQL (con PyMySQL)
- Autenticación: JWT (`djangorestframework-simplejwt`)
- Filtrado: `django-filter`
- Frontend: Vue 3 + Vite
- Estilos: Tailwind CSS
- Gráficos: Chart.js + vue-chartjs

## Estructura del repositorio
- `backend/`: Django REST API (app `produccion`, `mantenimiento`, configuración `produccion_api`)
- `dashboard-frontend/`: Aplicación Vue 3 (Vite + Tailwind)

## Funcionalidades
- API REST para registros de producción, cargas de combustible, reportes y filtros.
- Dashboard con gráficos y tabla de registros (gráfico usa dataset completo, tabla paginada).
- Endpoints relevantes:
	- `POST /api/login-empleado/` → login (devuelve tokens JWT)
	- `GET /api/produccion-dashboard/` → datos para dashboard (paginado + `registros_grafico`)
	- `GET /api/filtros/` → valores para filtros dinámicos (operaciones, unidades, equipos, operadores)
	- `GET /api/cargas-combustible/`, `/api/filtros-combustible/`, etc.
- Comandos custom: `send_kpi_report`, `reporte_diario`, `migrate_empleados`, entre otros.

## Requisitos
- Python 3.10+ (virtualenv recomendado)
- Node 16+ / npm
- MySQL accesible y configurado en `.env`

## Instalación y ejecución (desarrollo)

1) Backend (Windows / PowerShell)

```powershell
cd backend
H:/venv/ecommerce/Scripts/Activate.ps1  # o tu entorno virtual: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Configura archivo .env (puedes copiar .env.example si existe)
py manage.py migrate   # si procede
py manage.py runserver 0.0.0.0:8000
```

2) Frontend (desde la raíz del repo)

```bash
cd dashboard-frontend
npm install
npm run dev
```

3) Acceder
- Backend: http://127.0.0.1:8000/api/
- Frontend (Vite): por defecto en http://localhost:5173 (o según la salida de `npm run dev`)

## Variables de entorno importantes (`backend/.env`)
- `SECRET_KEY` - Django secret
- `DATABASE_URL` - URL de conexión a MySQL (ej: mysql://user:pass@host:3306/dbname)
- `DEBUG` - True/False
- Email: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- `KPI_REPORT_TO` - destinatarios por defecto para reportes

## Notas sobre paginación y gráficos
- El endpoint `/api/produccion-dashboard/` devuelve:
	- `results`: lista paginada (por defecto `page_size=10`), usada por la tabla
	- `registros_grafico`: dataset completo (sin paginar) optimizado para dibujar series temporales
- Si necesitas cambiar el tamaño de página por defecto edita `produccion_api/BaseViewSet.py::StandarPagination.page_size` o utiliza el parámetro `page_size` en las peticiones.

## Comandos útiles
- Ejecutar tareas programadas / reportes:
	- `py manage.py send_kpi_report --start-date 2025-11-01 --end-date 2025-11-30`
- Shell Django:
	- `py manage.py shell`

## Deploy / Producción
- Revisar `ALLOWED_HOSTS`, configuración de base de datos y `DEBUG=False`.
- Usar Gunicorn / Daphne + Nginx o contenedores según tu infraestructura.

## Contribuir
- Abrir PR con cambios claros y tests si aplica.

---
Actualizado: instrucciones de instalación, ejecución y resumen técnico.
