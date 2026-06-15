---
name: django-drf-vue-fullstack
description: Build fullstack web applications with Django + Django REST Framework backend and Vue.js frontend. Use when creating REST APIs, SPAs, dashboards with charts (ApexCharts), CRUD apps, or any project requiring Django backend with modern Vue.js + Tailwind CSS frontend and MySQL database. Handles project setup, API endpoints, Vue components, authentication, database models, and deployment.
---

# Django + DRF + Vue.js Fullstack Development

Build modern fullstack web applications with Django REST Framework backend, MySQL database, and Vue.js + ApexCharts + Tailwind CSS frontend.

## Quick Start

**Common tasks:**
- "Create a Django REST API for users with CRUD operations"
- "Add JWT authentication to the Django backend"
- "Create a Vue component with ApexCharts for displaying analytics"
- "Set up CORS between Django and Vue frontend"
- "Add database models with Django ORM and MySQL"
- "Create a dashboard with Tailwind CSS styling"
- "Implement pagination and filtering in DRF viewsets"

## Project Structure

### Backend (Django + DRF)
```
backend/
├── manage.py
├── requirements.txt
├── config/                    # Project settings
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL config
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/                # User management app
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── api/                  # Main API app
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── permissions.py
│   └── core/                 # Core utilities
│       ├── authentication.py
│       ├── pagination.py
│       └── mixins.py
└── static/
```

### Frontend (Vue + Apex + Tailwind)
```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── index.html
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/
│   │   └── index.js
│   ├── store/                # Pinia/Vuex state
│   │   ├── index.js
│   │   └── modules/
│   │       ├── auth.js
│   │       └── user.js
│   ├── views/
│   │   ├── Home.vue
│   │   ├── Dashboard.vue
│   │   └── Login.vue
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.vue
│   │   │   └── Sidebar.vue
│   │   ├── charts/
│   │   │   ├── LineChart.vue
│   │   │   ├── BarChart.vue
│   │   │   └── PieChart.vue
│   │   └── common/
│   │       ├── Button.vue
│   │       └── Card.vue
│   ├── services/             # API client
│   │   ├── api.js
│   │   ├── auth.js
│   │   └── user.js
│   └── assets/
│       └── styles/
│           └── main.css      # Tailwind imports
└── public/
```

## Backend Development (Django + DRF)

### 1. Initial Setup

**Install dependencies:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install django djangorestframework django-cors-headers mysqlclient
pip install djangorestframework-simplejwt python-decouple
pip freeze > requirements.txt
```

**Create Django project:**
```bash
django-admin startproject config .
python manage.py startapp users
python manage.py startapp api
```

### 2. Settings Configuration (settings.py)

```python
# config/settings.py

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Local apps
    'users',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # Alternative
]
CORS_ALLOW_CREDENTIALS = True

# Database - MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Custom user model (if needed)
# AUTH_USER_MODEL = 'users.CustomUser'
```

### 3. Models (Django ORM with MySQL)

```python
# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Extended user model"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

# api/models.py
from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name

class Item(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return self.title
```

### 4. Serializers (DRF)

```python
# users/serializers.py
from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone', 'avatar', 'created_at']
        read_only_fields = ['id', 'created_at']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'phone']
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

# api/serializers.py
from rest_framework import serializers
from .models import Category, Item

class CategorySerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'items_count', 'created_at']
    
    def get_items_count(self, obj):
        return obj.items.filter(is_active=True).count()

class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Item
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'owner', 'owner_username', 'price', 'quantity', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value
```

### 5. Views (DRF ViewSets)

```python
# users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import UserSerializer, UserCreateSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout user by blacklisting refresh token"""
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# api/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg
from .models import Category, Item
from .serializers import CategorySerializer, ItemSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.select_related('category', 'owner').all()
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price', 'title']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get items statistics for dashboard charts"""
        stats = {
            'total_items': Item.objects.count(),
            'active_items': Item.objects.filter(is_active=True).count(),
            'total_value': Item.objects.aggregate(
                total=Sum('price')
            )['total'] or 0,
            'avg_price': Item.objects.aggregate(
                avg=Avg('price')
            )['avg'] or 0,
            'by_category': list(
                Category.objects.annotate(
                    count=Count('items')
                ).values('name', 'count')
            ),
        }
        return Response(stats)
```

### 6. URLs Configuration

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import UserViewSet
from api.views import CategoryViewSet, ItemViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('categories', CategoryViewSet)
router.register('items', ItemViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

### 7. Environment Variables (.env)

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL Database
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306
```

## Frontend Development (Vue + Apex + Tailwind)

### 1. Initial Setup

```bash
# Create Vue project with Vite
npm create vite@latest frontend -- --template vue
cd frontend

# Install dependencies
npm install
npm install vue-router pinia
npm install axios
npm install apexcharts vue3-apexcharts
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Tailwind CSS Configuration

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}
```

```css
/* src/assets/styles/main.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }
  
  .btn-primary {
    @apply btn bg-primary-600 text-white hover:bg-primary-700;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
}
```

### 3. API Service (Axios)

```javascript
// src/services/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  }
})

// Request interceptor - add JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const refresh = localStorage.getItem('refresh_token')
        const { data } = await axios.post(
          'http://localhost:8000/api/token/refresh/',
          { refresh }
        )
        
        localStorage.setItem('access_token', data.access)
        api.defaults.headers.Authorization = `Bearer ${data.access}`
        
        return api(originalRequest)
      } catch (err) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
```

```javascript
// src/services/auth.js
import api from './api'

export const authService = {
  async login(username, password) {
    const { data } = await api.post('/token/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    return data
  },
  
  async logout() {
    const refresh = localStorage.getItem('refresh_token')
    try {
      await api.post('/users/logout/', { refresh })
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  },
  
  async getCurrentUser() {
    const { data } = await api.get('/users/me/')
    return data
  },
  
  isAuthenticated() {
    return !!localStorage.getItem('access_token')
  }
}
```

```javascript
// src/services/items.js
import api from './api'

export const itemService = {
  getAll(params = {}) {
    return api.get('/items/', { params })
  },
  
  getById(id) {
    return api.get(`/items/${id}/`)
  },
  
  create(item) {
    return api.post('/items/', item)
  },
  
  update(id, item) {
    return api.put(`/items/${id}/`, item)
  },
  
  delete(id) {
    return api.delete(`/items/${id}/`)
  },
  
  getStats() {
    return api.get('/items/stats/')
  }
}
```

### 4. State Management (Pinia)

```javascript
// src/store/index.js
import { createPinia } from 'pinia'
export const pinia = createPinia()

// src/store/modules/auth.js
import { defineStore } from 'pinia'
import { authService } from '@/services/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
  }),
  
  actions: {
    async login(username, password) {
      await authService.login(username, password)
      await this.fetchUser()
    },
    
    async fetchUser() {
      try {
        this.user = await authService.getCurrentUser()
        this.isAuthenticated = true
      } catch (error) {
        this.user = null
        this.isAuthenticated = false
      }
    },
    
    async logout() {
      await authService.logout()
      this.user = null
      this.isAuthenticated = false
    },
  },
})

// src/store/modules/items.js
import { defineStore } from 'pinia'
import { itemService } from '@/services/items'

export const useItemStore = defineStore('items', {
  state: () => ({
    items: [],
    currentItem: null,
    loading: false,
    stats: null,
  }),
  
  actions: {
    async fetchItems(params) {
      this.loading = true
      try {
        const { data } = await itemService.getAll(params)
        this.items = data.results || data
      } finally {
        this.loading = false
      }
    },
    
    async fetchStats() {
      const { data } = await itemService.getStats()
      this.stats = data
    },
    
    async createItem(item) {
      const { data } = await itemService.create(item)
      this.items.unshift(data)
      return data
    },
    
    async updateItem(id, item) {
      const { data } = await itemService.update(id, item)
      const index = this.items.findIndex(i => i.id === id)
      if (index !== -1) {
        this.items[index] = data
      }
      return data
    },
    
    async deleteItem(id) {
      await itemService.delete(id)
      this.items = this.items.filter(i => i.id !== id)
    },
  },
})
```

### 5. Vue Components with Tailwind CSS

```vue
<!-- src/components/layout/Navbar.vue -->
<template>
  <nav class="bg-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <router-link to="/" class="text-xl font-bold text-primary-600">
            MyApp
          </router-link>
          <div class="hidden md:flex ml-10 space-x-4">
            <router-link 
              to="/dashboard" 
              class="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md"
            >
              Dashboard
            </router-link>
            <router-link 
              to="/items" 
              class="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md"
            >
              Items
            </router-link>
          </div>
        </div>
        
        <div class="flex items-center space-x-4">
          <span class="text-gray-700">{{ user?.username }}</span>
          <button @click="handleLogout" class="btn btn-primary">
            Logout
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/modules/auth'

const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>
```

```vue
<!-- src/components/common/Card.vue -->
<template>
  <div class="card hover:shadow-lg transition-shadow">
    <div v-if="title" class="mb-4">
      <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
      <p v-if="subtitle" class="text-sm text-gray-600">{{ subtitle }}</p>
    </div>
    
    <div class="card-content">
      <slot />
    </div>
    
    <div v-if="$slots.footer" class="mt-4 pt-4 border-t border-gray-200">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String,
})
</script>
```

### 6. ApexCharts Components

```vue
<!-- src/components/charts/LineChart.vue -->
<template>
  <div class="chart-container">
    <apexchart
      type="line"
      :options="chartOptions"
      :series="series"
      height="350"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  categories: {
    type: Array,
    required: true
  },
  title: {
    type: String,
    default: 'Chart'
  }
})

const series = computed(() => [{
  name: 'Values',
  data: props.data
}])

const chartOptions = ref({
  chart: {
    type: 'line',
    toolbar: {
      show: true
    }
  },
  title: {
    text: props.title,
    align: 'left',
    style: {
      fontSize: '16px',
      fontWeight: 600,
    }
  },
  xaxis: {
    categories: props.categories
  },
  stroke: {
    curve: 'smooth',
    width: 3
  },
  colors: ['#3b82f6'],
  dataLabels: {
    enabled: false
  },
})
</script>
```

```vue
<!-- src/components/charts/BarChart.vue -->
<template>
  <div class="chart-container">
    <apexchart
      type="bar"
      :options="chartOptions"
      :series="series"
      height="350"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const props = defineProps({
  data: Array,
  categories: Array,
  title: String
})

const series = computed(() => [{
  name: 'Count',
  data: props.data
}])

const chartOptions = ref({
  chart: {
    type: 'bar',
    toolbar: { show: true }
  },
  title: {
    text: props.title,
    align: 'left'
  },
  plotOptions: {
    bar: {
      borderRadius: 8,
      horizontal: false,
      columnWidth: '55%',
    }
  },
  xaxis: {
    categories: props.categories
  },
  colors: ['#3b82f6'],
  dataLabels: {
    enabled: false
  },
})
</script>
```

```vue
<!-- src/components/charts/PieChart.vue -->
<template>
  <div class="chart-container">
    <apexchart
      type="pie"
      :options="chartOptions"
      :series="series"
      height="350"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

const apexchart = VueApexCharts

const props = defineProps({
  data: Array,
  labels: Array,
  title: String
})

const series = computed(() => props.data)

const chartOptions = ref({
  chart: {
    type: 'pie',
  },
  title: {
    text: props.title,
    align: 'center'
  },
  labels: props.labels,
  colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
  legend: {
    position: 'bottom'
  },
  responsive: [{
    breakpoint: 480,
    options: {
      chart: {
        width: 300
      },
      legend: {
        position: 'bottom'
      }
    }
  }]
})
</script>
```

### 7. Dashboard View with Charts

```vue
<!-- src/views/Dashboard.vue -->
<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card title="Total Items">
        <p class="text-3xl font-bold text-primary-600">
          {{ stats?.total_items || 0 }}
        </p>
      </Card>
      
      <Card title="Active Items">
        <p class="text-3xl font-bold text-green-600">
          {{ stats?.active_items || 0 }}
        </p>
      </Card>
      
      <Card title="Total Value">
        <p class="text-3xl font-bold text-blue-600">
          ${{ (stats?.total_value || 0).toFixed(2) }}
        </p>
      </Card>
      
      <Card title="Average Price">
        <p class="text-3xl font-bold text-purple-600">
          ${{ (stats?.avg_price || 0).toFixed(2) }}
        </p>
      </Card>
    </div>
    
    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card title="Items by Category">
        <BarChart
          v-if="categoryData.length"
          :data="categoryData"
          :categories="categoryLabels"
          title="Category Distribution"
        />
      </Card>
      
      <Card title="Category Breakdown">
        <PieChart
          v-if="categoryData.length"
          :data="categoryData"
          :labels="categoryLabels"
          title="Items per Category"
        />
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useItemStore } from '@/store/modules/items'
import Card from '@/components/common/Card.vue'
import BarChart from '@/components/charts/BarChart.vue'
import PieChart from '@/components/charts/PieChart.vue'

const itemStore = useItemStore()

const stats = computed(() => itemStore.stats)

const categoryData = computed(() => 
  stats.value?.by_category?.map(c => c.count) || []
)

const categoryLabels = computed(() => 
  stats.value?.by_category?.map(c => c.name) || []
)

onMounted(async () => {
  await itemStore.fetchStats()
})
</script>
```

### 8. Items List View

```vue
<!-- src/views/Items.vue -->
<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-900">Items</h1>
      <button @click="showCreateModal = true" class="btn btn-primary">
        + Add Item
      </button>
    </div>
    
    <!-- Search and Filters -->
    <div class="mb-6 flex gap-4">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search items..."
        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
        @input="handleSearch"
      />
      <select
        v-model="selectedCategory"
        class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
        @change="handleFilter"
      >
        <option value="">All Categories</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.slug">
          {{ cat.name }}
        </option>
      </select>
    </div>
    
    <!-- Items Grid -->
    <div v-if="loading" class="text-center py-12">
      <p class="text-gray-600">Loading...</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="item in items"
        :key="item.id"
        :title="item.title"
      >
        <div class="space-y-2">
          <p class="text-gray-600 line-clamp-2">{{ item.description }}</p>
          <div class="flex items-center justify-between">
            <span class="text-2xl font-bold text-primary-600">
              ${{ item.price }}
            </span>
            <span class="text-sm text-gray-500">
              Qty: {{ item.quantity }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
              {{ item.category_name }}
            </span>
            <span
              :class="[
                'px-2 py-1 text-xs rounded',
                item.is_active 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              ]"
            >
              {{ item.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
        
        <template #footer>
          <div class="flex gap-2">
            <button
              @click="editItem(item)"
              class="flex-1 px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
            >
              Edit
            </button>
            <button
              @click="deleteItem(item.id)"
              class="flex-1 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
            >
              Delete
            </button>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useItemStore } from '@/store/modules/items'
import Card from '@/components/common/Card.vue'

const itemStore = useItemStore()

const items = computed(() => itemStore.items)
const loading = computed(() => itemStore.loading)

const searchQuery = ref('')
const selectedCategory = ref('')
const categories = ref([])
const showCreateModal = ref(false)

const handleSearch = () => {
  fetchItems()
}

const handleFilter = () => {
  fetchItems()
}

const fetchItems = async () => {
  const params = {}
  if (searchQuery.value) params.search = searchQuery.value
  if (selectedCategory.value) params.category = selectedCategory.value
  await itemStore.fetchItems(params)
}

const editItem = (item) => {
  // Implement edit modal
  console.log('Edit', item)
}

const deleteItem = async (id) => {
  if (confirm('Are you sure you want to delete this item?')) {
    await itemStore.deleteItem(id)
  }
}

onMounted(() => {
  fetchItems()
  // Fetch categories for filter
})
</script>
```

### 9. Router Setup

```javascript
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { authService } from '@/services/auth'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/items',
    name: 'Items',
    component: () => import('@/views/Items.vue'),
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const isAuthenticated = authService.isAuthenticated()
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
```

### 10. Main App Setup

```javascript
// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { pinia } from './store'
import VueApexCharts from 'vue3-apexcharts'
import './assets/styles/main.css'

const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(VueApexCharts)

app.mount('#app')
```

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

```javascript
// package.json (relevant sections)
{
  "name": "frontend",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "apexcharts": "^3.45.0",
    "vue3-apexcharts": "^1.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

## Running the Application

### Development Mode

**Backend:**
```bash
cd backend

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
# Server runs at http://localhost:8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Server runs at http://localhost:5173
```

### Production Deployment

**Backend (Django):**
```bash
# Collect static files
python manage.py collectstatic

# Use gunicorn as WSGI server
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Or use uWSGI
pip install uwsgi
uwsgi --http :8000 --module config.wsgi
```

**Frontend (Vue):**
```bash
# Build for production
npm run build

# Deploy dist/ folder to:
# - Nginx
# - Apache
# - CDN (Netlify, Vercel, etc.)
```

### Docker Setup (Optional)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: myapp
      MYSQL_ROOT_PASSWORD: rootpassword
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DB_HOST=db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql_data:
```

## Common Patterns and Best Practices

### Authentication Flow
1. User logs in → receives JWT access + refresh tokens
2. Frontend stores tokens in localStorage
3. Axios interceptor adds token to all requests
4. On 401 error → refresh token → retry request
5. If refresh fails → redirect to login

### Error Handling
```javascript
// Vue composable for error handling
import { ref } from 'vue'

export function useErrorHandler() {
  const error = ref(null)
  const loading = ref(false)
  
  const handleAsync = async (fn) => {
    loading.value = true
    error.value = null
    try {
      return await fn()
    } catch (err) {
      error.value = err.response?.data?.message || 'An error occurred'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  return { error, loading, handleAsync }
}
```

### Django Signals for Auto Actions
```python
# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Item

@receiver(post_save, sender=Item)
def item_created(sender, instance, created, **kwargs):
    if created:
        # Send notification, update cache, etc.
        print(f"New item created: {instance.title}")
```

### Vue Composables
```javascript
// src/composables/useItems.js
import { ref, computed } from 'vue'
import { useItemStore } from '@/store/modules/items'

export function useItems() {
  const itemStore = useItemStore()
  const loading = ref(false)
  
  const items = computed(() => itemStore.items)
  
  const fetchItems = async (params) => {
    loading.value = true
    try {
      await itemStore.fetchItems(params)
    } finally {
      loading.value = false
    }
  }
  
  return {
    items,
    loading,
    fetchItems
  }
}
```

## Resources

### scripts/
Development utilities and automation scripts for project setup and management.

### references/
- `auth.md` - Authentication and JWT implementation details
- `database.md` - MySQL schema design and optimization
- `deployment.md` - Production deployment guides

### assets/
- `project-template/` - Full project boilerplate with Django + Vue setup
