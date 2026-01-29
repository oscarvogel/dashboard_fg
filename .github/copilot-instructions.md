# GitHub Copilot Instructions

## Project Context
- **Architecture**: Decoupled Monorepo. Django REST Framework backend serving a Vue 3 (Vite) frontend.
- **Backend Root**: `backend/`
- **Frontend Root**: `dashboard-frontend/`

## Backend Guidelines (Django + DRF)

### Architecture & Patterns
- **Base ViewSet**: Inherit from `BaseAppModelViewSet` (in `produccion_api.BaseViewSet`) instead of standard DRF ViewSets. It includes `StandarPagination` and `DebugSerializerErrorsMixin`.
  ```python
  from produccion_api.BaseViewSet import BaseAppModelViewSet
  class MyViewSet(BaseAppModelViewSet):
      ...
  ```
- **Database Models**: 
  - Many models map to existing legacy tables. Use `managed = False` and explicit `db_table`.
  - Always define `verbose_name` and `verbose_name_plural`.
  - Use `pymysql` as the MySQL driver (configured in `settings.py`).
- **Management Commands**: Custom commands reside in `backend/produccion/management/commands/` (e.g., `send_kpi_report.py`).

### Development
- **Environment**: Uses `python-dotenv` and `dj_database_url`.
- **Formatting**: `DATE_FORMAT = 'd/m/Y'`, `TIME_ZONE = 'America/Argentina/Buenos_Aires'`.

## Frontend Guidelines (Vue 3 + Vite)

### Architecture & Patterns
- **Framework**: Vue 3 with Composition API (`<script setup>`).
- **Styling**: Tailwind CSS v4.
- **API Communication**: 
  - Use `src/services/api.js` for all HTTP requests. 
  - This service handles base URLs (Production vs Dev) and JWT Auth headers automatically.
  - Do not hardcode API URLs in components.
- **State Management**: Local component state preferred or Composables (`src/composables/`) for shared logic (e.g., `useAuth.js`).

### Charts & Visualization
- Uses `chart.js` and `vue-chartjs`.
- See `src/components/` for reusable chart wrappers (`BarChart.vue`, `PieChart.vue`).

## Critical Workflows

### Running the App
- **Backend**: 
  - Standard: `python manage.py runserver` (inside `backend/`).
  - Shortcut: `.\run_django.ps1` (Check script for venv path).
- **Frontend**: `npm run dev` (inside `dashboard-frontend/`).
- **KPI Reports**: Run via `python manage.py send_kpi_report`.

### Database & Migrations
- Since many models are `managed = False`, migrations often apply only to specific new tables (like `Empleado` user extensions). Check `migrations/` before running `makemigrations`.

## Common Pitfalls
- **CORS**: Configured in `settings.py`. Ensure localhost/production IPs are in `ALLOWED_HOSTS` and CORS whitelist.
- **Auth**: Frontend handles 401 errors by redirecting to login. Ensure tokens are stored in `localStorage` as `access_token`.