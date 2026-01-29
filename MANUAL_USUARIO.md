# Manual de Usuario - Sistema Dashboard Forestal Garuhapé

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Acceso al Sistema](#acceso-al-sistema)
6. [Módulos del Sistema](#módulos-del-sistema)
7. [Guía de Uso por Módulo](#guía-de-uso-por-módulo)
8. [API REST - Endpoints](#api-rest---endpoints)
9. [Administración](#administración)
10. [Solución de Problemas](#solución-de-problemas)
11. [Soporte Técnico](#soporte-técnico)

---

## 🎯 Introducción

El **Sistema Dashboard Forestal Garuhapé** es una aplicación web diseñada para gestionar y monitorear la producción forestal, mantenimiento de equipos, control de combustible y análisis operacional.

### Características principales:

- **Gestión de Producción**: Registro y seguimiento de operaciones forestales
- **Control de Equipos**: Monitoreo de maquinaria y equipamiento
- **Gestión de Combustible**: Control de cargas y consumos
- **Análisis Operacional**: Dashboards y reportes en tiempo real
- **Mantenimiento**: Órdenes de servicio y control de repuestos
- **Autenticación segura**: Login con JWT tokens

---

## 💻 Requisitos del Sistema

### Backend (Django)
- Python 3.8 o superior
- Django 5.1.1
- MySQL/MariaDB
- pip (gestor de paquetes Python)

### Frontend (Vue.js)
- Node.js 16.x o superior
- npm 8.x o superior
- Navegador moderno (Chrome, Firefox, Edge)

### Conexión
- Acceso a Internet (para dependencias)
- Puerto 8000 disponible (Backend)
- Puerto 5173 disponible (Frontend)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────┐
│         FRONTEND (Vue.js 3)             │
│  - Interfaz de usuario                  │
│  - Dashboard interactivo                │
│  - Gráficos (Chart.js)                  │
│  - Vue Router                           │
└──────────────┬──────────────────────────┘
               │ HTTP/HTTPS
               │ REST API
┌──────────────▼──────────────────────────┐
│        BACKEND (Django 5.1)             │
│  - API REST                             │
│  - Autenticación JWT                    │
│  - Lógica de negocio                    │
│  - Django REST Framework                │
└──────────────┬──────────────────────────┘
               │ ORM
               │ MySQL
┌──────────────▼──────────────────────────┐
│      BASE DE DATOS (MySQL)              │
│  - Datos de producción                  │
│  - Usuarios y permisos                  │
│  - Equipos y mantenimiento              │
│  - Registros históricos                 │
└─────────────────────────────────────────┘
```

### Aplicaciones Django

1. **produccion**: Gestión de producción forestal y equipos
2. **mantenimiento**: Órdenes de servicio y repuestos

---

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/oscarvogel/dashboard_fg.git
cd dashboard_fg
```

### 2. Configuración del Backend

#### 2.1. Crear entorno virtual

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

#### 2.2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

#### 2.3. Configurar variables de entorno

Crear archivo `.env` en la carpeta `backend/`:

```env
# Django Settings
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
DATABASE_URL=mysql://usuario:password@localhost:3306/nombre_bd

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password
DEFAULT_FROM_EMAIL=tu-email@gmail.com
```

#### 2.4. Migrar base de datos

```powershell
python manage.py migrate
```

#### 2.5. Crear superusuario

```powershell
python manage.py createsuperuser
```

#### 2.6. Iniciar servidor

```powershell
python manage.py runserver
```

El backend estará disponible en: `http://127.0.0.1:8000`

### 3. Configuración del Frontend

#### 3.1. Instalar dependencias

```powershell
cd dashboard-frontend
npm install
```

#### 3.2. Configurar API endpoint

Editar `src/services/api.js` y verificar la URL base:

```javascript
const API_BASE_URL = 'http://127.0.0.1:8000/api';
```

#### 3.3. Iniciar servidor de desarrollo

```powershell
npm run dev
```

El frontend estará disponible en: `http://localhost:5173`

#### 3.4. Compilar para producción

```powershell
npm run build
```

Los archivos compilados se guardarán en `dist/`

---

## 🔐 Acceso al Sistema

### Inicio de Sesión

1. Abrir navegador en `http://localhost:5173`
2. Ingresar credenciales:
   - **DNI**: Número de documento del empleado
   - **Contraseña**: Contraseña asignada
3. Click en "Iniciar Sesión"

### Gestión de Tokens

El sistema utiliza **JWT (JSON Web Tokens)** para autenticación:

- **Access Token**: Válido por 60 minutos
- **Refresh Token**: Válido por 1 día

Los tokens se almacenan en `localStorage` del navegador.

### Cerrar Sesión

Click en el botón "Cerrar Sesión" en el menú de navegación.

---

## 📦 Módulos del Sistema

### 1. **Dashboard Principal**
   - Vista general de métricas
   - Indicadores clave de rendimiento (KPI)
   - Acceso rápido a módulos

### 2. **Resumen Operacional**
   - Datos diarios y acumulados mensuales
   - Horas trabajadas por máquina
   - Producción (árboles, m³, toneladas, viajes)
   - Consumo de combustible y lubricantes

### 3. **Resumen de Combustible**
   - Control de cargas por unidad de negocio
   - Detalle de ingresos y egresos
   - Filtros por equipo y fecha
   - Totales acumulados

### 4. **Reporte de Producción**
   - Producción real vs. esperada
   - Gráficos de tendencias
   - Consumo de combustible
   - Filtros dinámicos (UN, operación, equipo, operador)
   - Exportación a Excel

### 5. **Horas No Operativas**
   - Análisis de tiempos muertos
   - Motivos de paradas
   - Gráficos por categoría
   - Detalle por unidad de negocio

### 6. **Máquinas por Frente/Operador**
   - Asignación actual de equipos
   - Operadores por máquina
   - Última actualización y horas registradas

### 7. **Efectividad de Servicios**
   - (Módulo en desarrollo)
   - Órdenes de servicio
   - Tiempos de mantenimiento

### 8. **Resumen Máquinas y Componentes**
   - Consumo de cadenas, espadas, punteras, piñones
   - Rendimiento por componente
   - Últimas horas de cambio
   - M³ producidos desde último cambio
   - Control de aceite de cadena

---

## 📖 Guía de Uso por Módulo

### 🏠 Dashboard Principal

**Propósito**: Vista general del sistema y acceso rápido.

**Cómo usar**:
1. Después de iniciar sesión, verá el dashboard
2. Las tarjetas muestran acceso directo a cada módulo
3. Click en cualquier tarjeta para acceder al módulo

---

### 📊 Resumen Operacional

**Propósito**: Monitorear producción diaria y mensual por máquina.

**Cómo usar**:

1. **Seleccionar rango de fechas**:
   - `Fecha Inicio`: Primer día del mes (recomendado)
   - `Fecha Fin`: Último día del mes o fecha actual

2. **Filtros opcionales**:
   - `Unidad de Negocio`: Seleccionar UN específica
   - `Fecha específica`: Ver datos de un día puntual

3. **Interpretar datos**:

   **Tabla Diaria** (si se selecciona fecha específica):
   - Muestra producción del día por máquina
   - Horas, árboles, m³, toneladas, viajes
   - Combustible y lubricante consumido

   **Tabla Acumulado Mensual**:
   - Suma total del período seleccionado
   - Todas las métricas acumuladas por máquina

4. **Exportar datos**:
   - Click en "Exportar a Excel" para descargar reporte

---

### ⛽ Resumen de Combustible

**Propósito**: Control detallado de cargas de combustible.

**Cómo usar**:

1. **Seleccionar período**:
   - Fecha Inicio y Fecha Fin

2. **Filtrar por Unidad de Negocio**:
   - El selector muestra solo UNs con cargas en el período

3. **Filtrar por Equipo** (opcional):
   - Después de seleccionar UN, se muestran equipos disponibles

4. **Interpretar resultados**:
   - **Tarjetas superiores**:
     - Total Ingresos (litros)
     - Total Egresos (litros)
   - **Tabla detallada**:
     - Fecha, equipo, litros, tipo de movimiento
     - Lugar de carga, km/hora registrados

5. **Análisis**:
   - Compare ingresos vs. egresos
   - Identifique equipos con mayor consumo

---

### 📈 Reporte de Producción

**Propósito**: Análisis completo de producción con comparativa contra metas.

**Cómo usar**:

1. **Rango de fechas obligatorio**:
   - Inicio y Fin del período a analizar

2. **Aplicar filtros dinámicos**:
   - **Unidad de Negocio**: Una o múltiples (separadas por coma)
   - **Operación**: VOLTEO, EXTRACCION, etc.
   - **Equipo**: Filtrar por máquina específica
   - **Operador**: Buscar por nombre
   - **Acta**: Filtrar por número de acta

3. **Gráficos disponibles**:

   **a) Producción Real vs. Esperada**:
   - Línea azul: Producción acumulada real
   - Línea roja: Meta esperada acumulada
   - Puntos: Producción esperada por día

   **b) Consumo de Combustible**:
   - Barras verdes: Litros consumidos por día
   - Totales en la parte superior

4. **Tabla de registros**:
   - Detalle completo de cada registro de producción
   - Columnas: Fecha, UN, Operación, Equipo, Operador, etc.
   - Paginación automática

5. **Exportar a Excel**:
   - Click en botón "Exportar a Excel"
   - Se descarga archivo con todos los datos filtrados

**Interpretación**:
- Si la línea azul está por debajo de la roja → Producción bajo meta
- Si la línea azul supera la roja → Producción sobre meta

---

### ⏸️ Horas No Operativas

**Propósito**: Analizar tiempos muertos y sus causas.

**Cómo usar**:

1. **Seleccionar período**: Fecha inicio y fin

2. **Filtro opcional**:
   - Unidad de Negocio específica

3. **Gráfico de barras**:
   - Muestra motivos ordenados por horas acumuladas
   - Altura de barra = cantidad de horas no operativas

4. **Tabla detallada**:
   - UN, Fecha, Horas no operativas
   - Motivo específico
   - Observaciones adicionales

5. **Análisis**:
   - Identificar motivos recurrentes
   - Tomar decisiones para reducir tiempos muertos
   - Planificar mantenimientos preventivos

**Motivos comunes**:
- Falta de combustible
- Mantenimiento correctivo
- Condiciones climáticas
- Falta de personal
- Espera de carga

---

### 🚜 Máquinas por Frente/Operador

**Propósito**: Vista rápida de asignaciones actuales.

**Cómo usar**:

1. **Seleccionar rango de fechas**

2. **Filtro opcional**:
   - Código de Unidad de Negocio

3. **Tabla de resultados**:
   - **Equipo**: Patente de la máquina
   - **Detalle**: Descripción del equipo
   - **Frente**: Unidad de negocio asignada
   - **Operador**: Nombre del operador actual
   - **Última Fecha**: Última actividad registrada
   - **Última Hr Fin**: Última hora registrada

4. **Uso práctico**:
   - Verificar ubicación actual de equipos
   - Contactar operadores específicos
   - Planificar movimientos de maquinaria

---

### 🔧 Resumen Máquinas y Componentes

**Propósito**: Control de desgaste y rendimiento de componentes.

**Cómo usar**:

1. **Seleccionar período**: Fecha inicio y fin

2. **Filtros opcionales**:
   - Unidad de Negocio
   - Tipo de Operación

3. **Tabla de datos**:
   
   **Columnas principales**:
   - **Máquina**: Descripción del equipo
   - **UN**: Unidad de negocio
   - **Cadenas utilizadas**: Cantidad total en el período
   - **Última Hr**: Última hora registrada
   - **Horas trabajadas**: Total de horas operativas
   - **Total m³**: Producción acumulada
   - **Rendimiento/Cadena**: m³ por cada cadena (eficiencia)
   - **Total Aceite**: Litros de aceite de cadena consumidos

   **Columnas de componentes**:
   - **m³ desde cambio Espada**
   - **m³ desde cambio Puntera**
   - **m³ desde cambio Piñón**
   - **Última Hr Cambio Espada/Puntera/Piñón/Giro Piñón**

4. **Totales generales**:
   - Total m³ producidos
   - Total aceite de cadena
   - Total cadenas utilizadas
   - Rendimiento promedio

5. **Análisis**:
   - **Rendimiento bajo por cadena** → Revisar operación o calidad
   - **Alto consumo de aceite** → Posible fuga o ajuste necesario
   - **Muchos m³ desde último cambio** → Programar cambio preventivo

6. **Exportar a Excel**:
   - Botón disponible para descarga

**Recomendaciones**:
- Revisar componentes cada 1000 m³ (varía según equipo)
- Programar cambios preventivos antes de fallas
- Comparar rendimientos entre máquinas similares

---

## 🔌 API REST - Endpoints

### Autenticación

#### Login
```
POST /api/login/
```

**Body**:
```json
{
  "dni": "12345678",
  "password": "contraseña"
}
```

**Respuesta**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "operador": {
    "id": 1,
    "nombre": "Juan Pérez",
    "dni": "12345678"
  }
}
```

### Producción

#### Dashboard de Producción
```
GET /api/produccion/dashboard/?start_date=2025-01-01&end_date=2025-01-31
```

**Parámetros opcionales**:
- `cod_un`: ID de unidad de negocio (puede ser múltiple: "1,2,3")
- `operacion`: Tipo de operación (puede ser múltiple: "VOLTEO,EXTRACCION")
- `detalle_equipo`: Filtrar por equipo
- `operador`: Filtrar por operador
- `acta`: Filtrar por acta

**Respuesta**:
```json
{
  "results": [...],
  "produccion_esperada_acumulada": 15000.50,
  "produccion_esperada_por_dia": {
    "2025-01-01": 500.25,
    "2025-01-02": 500.25
  },
  "unidad_produccion": "m3",
  "consumo_combustible_total": 5000.00,
  "consumo_combustible_por_dia": {
    "2025-01-01": 200.00
  },
  "filtros": {
    "operaciones": ["VOLTEO", "EXTRACCION"],
    "unidades": ["COSECHA CTL"],
    "equipos": [...],
    "operadores": [...],
    "actas": [...]
  }
}
```

#### Filtros Dinámicos
```
GET /api/produccion/filtros/?start_date=2025-01-01&end_date=2025-01-31
```

#### Resumen Operacional
```
GET /api/produccion/resumen-operacional/?start_date=2025-01-01&end_date=2025-01-31
```

**Parámetros opcionales**:
- `un`: ID de unidad de negocio
- `fecha`: Fecha específica para datos diarios (YYYY-MM-DD)

#### Horas No Operativas
```
GET /api/produccion/horas-no-operativas/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31
```

**Parámetros opcionales**:
- `un`: ID de unidad de negocio

#### Máquinas por Frente
```
GET /api/produccion/maquinas-frente-operador/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31
```

**Parámetros opcionales**:
- `cod_un`: ID de unidad de negocio

#### Resumen Máquinas y Componentes
```
GET /api/produccion/resumen-maquinas-componentes/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31
```

**Parámetros opcionales**:
- `cod_un`: IDs de unidades de negocio (múltiples: "1,2,3")
- `operacion`: Tipos de operación (múltiples: "VOLTEO,EXTRACCION")

### Combustible

#### Filtros de Combustible
```
GET /api/produccion/filtros-combustible/?start_date=2025-01-01&end_date=2025-01-31
```

#### Equipos por UN
```
GET /api/produccion/equipos-por-un/?un_id=1&start_date=2025-01-01&end_date=2025-01-31
```

#### Cargas de Combustible
```
GET /api/produccion/cargas-combustible/?start_date=2025-01-01&end_date=2025-01-31
```

**Parámetros opcionales**:
- `un_id`: ID de unidad de negocio
- `movil_id`: ID de equipo

### Empleados

#### Listar Empleados
```
GET /api/empleados/
```

#### Buscar Empleados
```
GET /api/empleados/?search=Juan
```

#### Registros de Empleado
```
GET /api/registros-empleado/?id=1&fecha_inicio=2025-01-01&fecha_fin=2025-01-31
```

### Headers de Autenticación

Para todas las rutas protegidas, incluir:
```
Authorization: Bearer {access_token}
```

---

## 🔧 Administración

### Panel de Administración Django

Acceder a: `http://127.0.0.1:8000/admin`

**Modelos disponibles**:

#### App: Producción
- UnidadNegocio
- TipoMovil
- Equipo (Móviles)
- Empleado (Personal)
- LugarCarga
- Panioles
- RegistroProduccion
- CargaCombustible
- ProduccionMensual
- Moneda

#### App: Mantenimiento
- UnidadMedida
- Repuestos
- Sector
- TipoTareas
- OrdenServicioCabecera
- OrdenServicioDetalle

### Gestión de Usuarios

#### Crear nuevo empleado

1. Ir a Admin → Personal (Empleado)
2. Click en "Agregar Empleado"
3. Completar:
   - Nombre
   - DNI
   - Password (será hasheado automáticamente)
4. Asociar a User de Django si es necesario
5. Guardar

#### Migrar empleados a usuarios Django

Ejecutar comando personalizado:
```powershell
python manage.py migrate_empleados
```

Este comando crea automáticamente usuarios de Django para cada empleado.

### Configuración de Unidades de Negocio

1. Admin → UnidadNegocio
2. Agregar/Editar unidades
3. Definir nombre

### Configuración de Equipos

1. Admin → Equipo (Móviles)
2. Agregar equipo:
   - Patente
   - Detalle (descripción)
   - Tipo de móvil
   - Última hora/km registrado
   - Estado (baja: sí/no)

### Configuración de Tipos de Movil

Definir categorías: Motosierras, Skidder, Forwarder, Harvester, etc.

---

## ❗ Solución de Problemas

### Problema: No puedo iniciar sesión

**Síntomas**: Mensaje "Credenciales inválidas"

**Soluciones**:
1. Verificar que el DNI esté correcto
2. Confirmar que el empleado existe en la base de datos
3. Verificar que el usuario de Django asociado esté activo
4. Revisar que la contraseña sea correcta

### Problema: Error de conexión a la API

**Síntomas**: "Network Error" o "Failed to fetch"

**Soluciones**:
1. Verificar que el backend esté corriendo: `http://127.0.0.1:8000`
2. Revisar configuración en `src/services/api.js`
3. Verificar CORS en `settings.py`
4. Comprobar firewall/antivirus

### Problema: Datos no se actualizan

**Síntomas**: Información desactualizada en dashboard

**Soluciones**:
1. Refrescar la página (F5)
2. Limpiar caché del navegador
3. Cerrar sesión y volver a iniciar
4. Verificar que haya datos en el rango de fechas seleccionado

### Problema: Gráficos no se muestran

**Síntomas**: Espacio en blanco donde debería haber gráficos

**Soluciones**:
1. Verificar consola del navegador (F12)
2. Confirmar que Chart.js esté instalado: `npm list chart.js`
3. Reinstalar dependencias: `npm install`
4. Verificar que haya datos para el período seleccionado

### Problema: Error 500 en el servidor

**Síntomas**: Internal Server Error

**Soluciones**:
1. Revisar logs del servidor Django
2. Verificar configuración de base de datos
3. Comprobar que todas las migraciones estén aplicadas
4. Revisar permisos de archivos

### Problema: Token expirado

**Síntomas**: "Token inválido" después de un tiempo

**Soluciones**:
1. El token expira después de 60 minutos (configurable)
2. Cerrar sesión y volver a iniciar
3. Implementar refresh token automático (ya configurado)

### Problema: No se exporta a Excel

**Síntomas**: Botón no funciona o descarga archivo vacío

**Soluciones**:
1. Verificar que `xlsx` esté instalado: `npm list xlsx`
2. Reinstalar: `npm install xlsx`
3. Verificar permisos de descarga en el navegador
4. Probar en modo incógnito

---

## 📞 Soporte Técnico

### Contacto

**Desarrollador**: Oscar Vogel  
**Email**: sistemas@servinlgsm.com.ar  
**Repositorio**: https://github.com/oscarvogel/dashboard_fg

### Reportar un Bug

1. Ir a: https://github.com/oscarvogel/dashboard_fg/issues
2. Click en "New Issue"
3. Describir:
   - ¿Qué estabas haciendo?
   - ¿Qué esperabas que sucediera?
   - ¿Qué sucedió en cambio?
   - Capturas de pantalla (si aplica)
   - Mensajes de error

### Solicitar Nueva Funcionalidad

Enviar descripción detallada a sistemas@servinlgsm.com.ar con:
- Objetivo de la funcionalidad
- Usuarios beneficiados
- Prioridad (Alta/Media/Baja)

---

## 📚 Apéndices

### A. Estructura de Base de Datos

#### Tabla: `tablero_produccion`
Registros diarios de producción por equipo y operador.

**Campos principales**:
- `id`: Identificador único
- `fecha`: Fecha del registro
- `cod_equipo`: FK a `moviles`
- `cod_operador`: FK a `personal`
- `cod_un`: FK a `unidadnegocio`
- `operacion`: Tipo (VOLTEO, EXTRACCION, etc.)
- `hr_inicio`, `hr_fin`: Horas de operación
- `m3`, `tn_despachadas`, `plantas`: Producción
- `combustible`, `aceite_cadena`, `aceite_hidraulico`: Consumos
- `hrs_no_operativas`, `motivo_no_op`: Tiempos muertos
- `espada`, `puntera`, `cadena`, `pinon`, `giro_pinon`: Cambios de componentes

#### Tabla: `moviles`
Equipos y maquinaria.

#### Tabla: `personal`
Empleados y operadores.

#### Tabla: `cargacomb`
Cargas de combustible.

#### Tabla: `produccion_mensual`
Metas mensuales de producción (no gestionada por Django).

### B. Tecnologías Utilizadas

**Backend**:
- Django 5.1.1
- Django REST Framework
- djangorestframework-simplejwt
- django-filter
- PyMySQL
- python-dotenv

**Frontend**:
- Vue.js 3.5.17
- Vue Router 4.5.1
- Axios 1.11.0
- Chart.js 4.5.0
- Vue-ChartJS 5.3.2
- TailwindCSS 4.1.11
- XLSX 0.18.5
- FontAwesome 7.0.0
- Vite 7.0.4

### C. Convenciones de Código

**Backend (Python)**:
- PEP 8 style guide
- Snake_case para variables y funciones
- PascalCase para clases
- Docstrings en español

**Frontend (JavaScript)**:
- ESLint configurado
- camelCase para variables y funciones
- PascalCase para componentes Vue
- Nombres descriptivos en inglés

### D. Glosario

- **UN**: Unidad de Negocio
- **CTL**: Cut-to-Length (sistema de cosecha)
- **m³**: Metros cúbicos
- **Hr**: Horas (horómetro)
- **JWT**: JSON Web Token
- **API**: Application Programming Interface
- **REST**: Representational State Transfer
- **CRUD**: Create, Read, Update, Delete

---

## 📝 Historial de Versiones

### Versión 1.0.0 (Actual)
- Sistema completo funcional
- 8 módulos principales
- Autenticación JWT
- Exportación a Excel
- Gráficos interactivos

### Próximas Mejoras
- Módulo de Efectividad de Servicios completo
- Notificaciones en tiempo real
- Modo offline
- App móvil
- Integración con sistemas externos

---

## ✅ Lista de Verificación - Primeros Pasos

- [ ] Backend instalado y corriendo
- [ ] Frontend instalado y corriendo
- [ ] Base de datos configurada
- [ ] Superusuario creado
- [ ] Empleados migrados a usuarios
- [ ] Unidades de negocio configuradas
- [ ] Equipos registrados
- [ ] Primera carga de producción
- [ ] Primer login exitoso
- [ ] Dashboard visible con datos

---

**Última actualización**: 28 de Octubre, 2025  
**Versión del manual**: 1.0  
**Sistema**: Dashboard Forestal Garuhapé v1.0.0
