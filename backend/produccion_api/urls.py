"""
URL configuration for produccion_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('produccion.urls')),
    path('api/mantenimiento/', include('mantenimiento.urls')),
    path('api/forestal-bot/', include('forestal_bot.urls')),
    path('api/bot/', include('forestal_bot.bot_urls')),
    path('api/bot/fgpy-maintenance/', include('fgpy_mantenimiento.bot_urls')),
    path('api/incidencias/', include('incidencias.urls')),
    path('api/fgpy-mantenimiento/', include('fgpy_mantenimiento.urls')),
]
