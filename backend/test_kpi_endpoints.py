#!/usr/bin/env python
"""
Script para verificar que ambos endpoints retornan la misma produccion_esperada_acumulada
Ejecutar desde: python backend/test_kpi_endpoints.py
"""

import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'produccion_api.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from produccion.models import ProduccionMensual, ProduccionMensual, UnidadNegocio
from datetime import date, timedelta
import calendar

def test_expected_production_calculation():
    """
    Verifica que la lógica de cálculo de producción esperada sea consistente
    """
    print("=" * 80)
    print("TEST: Verificar cálculo de producción esperada")
    print("=" * 80)
    
    # Parámetros de prueba
    month = 5
    year = 2026
    cod_un_id = 1  # COSECHA FULL TREE
    
    # Calcular periodo (formato YYYYMM)
    periodo = f"{year:04d}{month:02d}"
    start_date = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    
    print(f"\nParámetros:")
    print(f"  Periodo: {periodo}")
    print(f"  Rango: {start_date} a {month_end}")
    print(f"  Unidad Negocio ID: {cod_un_id}")
    
    # Verificar que la unidad existe
    try:
        un = UnidadNegocio.objects.get(id=cod_un_id)
        print(f"  Unidad encontrada: {un.nombre}")
    except UnidadNegocio.DoesNotExist:
        print(f"  ERROR: Unidad de negocio {cod_un_id} no existe")
        return
    
    # Scenario 1: ProduccionEjecutivaView (sin filtros de operación/equipo)
    print("\n" + "-" * 80)
    print("Scenario 1: ProduccionEjecutivaView (solo periodo + unidad_negocio)")
    print("-" * 80)
    
    queryset_ej = ProduccionMensual.objects.filter(
        periodo=periodo,
        unidad_negocio_id=cod_un_id,
    )
    print(f"  Registros ProduccionMensual: {queryset_ej.count()}")
    for pm in queryset_ej[:3]:
        print(f"    - {pm.periodo}: {pm.produccion} ({pm.tipo_operacion})")
    
    agregado_ej = queryset_ej.aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('produccion')
    )
    meta_ej = float(agregado_ej.get('total') or 0.0)
    
    # Calcular proporción (usando cutoff_date = último día con actividad)
    from produccion.views import RegistroProduccion
    last_activity = RegistroProduccion.objects.filter(
        fecha__range=[start_date, month_end],
        cod_un_id=cod_un_id,
    ).aggregate(__import__('django.db.models', fromlist=['Max']).Max('fecha')).get(
        f'fecha__max'
    )
    
    if not last_activity:
        last_activity = month_end
    
    dias_del_mes = sum(
        1 for d in range(1, calendar.monthrange(year, month)[1] + 1)
        if date(year, month, d).weekday() < 5
    )
    dias_habiles_rango = sum(
        1 for d in range((last_activity - start_date).days + 1)
        if (start_date + timedelta(days=d)).weekday() < 5
    )
    proporcion_ej = dias_habiles_rango / dias_del_mes if dias_del_mes > 0 else 0
    
    produccion_esperada_ej = round(meta_ej * proporcion_ej, 2)
    
    print(f"\n  Cálculo:")
    print(f"    Meta mensual: {meta_ej}")
    print(f"    Días hábiles en rango: {dias_habiles_rango}")
    print(f"    Días hábiles en mes: {dias_del_mes}")
    print(f"    Proporción: {proporcion_ej:.4f}")
    print(f"    Producción esperada acumulada: {produccion_esperada_ej}")
    
    # Scenario 2: ProduccionDashboardView (sin filtros de operación/equipo)
    print("\n" + "-" * 80)
    print("Scenario 2: ProduccionDashboardView (solo periodo, sin operacion/equipo)")
    print("-" * 80)
    
    queryset_db = ProduccionMensual.objects.filter(periodo=periodo)
    queryset_db = queryset_db.filter(unidad_negocio_id__in=[cod_un_id])
    
    print(f"  Registros ProduccionMensual: {queryset_db.count()}")
    for pm in queryset_db[:3]:
        print(f"    - {pm.periodo}: {pm.produccion} ({pm.tipo_operacion})")
    
    agregado_db = queryset_db.aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('produccion'),
        total_equipos=__import__('django.db.models', fromlist=['Sum']).Sum('cantidad_equipo')
    )
    meta_db = float(agregado_db.get('total') or 0.0)
    
    # ProduccionDashboardView usa end_date completo (no cutoff_date)
    dias_habiles_rango_db = sum(
        1 for d in range((month_end - start_date).days + 1)
        if (start_date + timedelta(days=d)).weekday() < 5
    )
    proporcion_db = dias_habiles_rango_db / dias_del_mes if dias_del_mes > 0 else 0
    
    produccion_esperada_db = round(meta_db * proporcion_db, 2)
    
    print(f"\n  Cálculo:")
    print(f"    Meta mensual: {meta_db}")
    print(f"    Días hábiles en rango: {dias_habiles_rango_db}")
    print(f"    Días hábiles en mes: {dias_del_mes}")
    print(f"    Proporción: {proporcion_db:.4f}")
    print(f"    Producción esperada acumulada: {produccion_esperada_db}")
    
    # Comparación
    print("\n" + "=" * 80)
    print("COMPARACIÓN:")
    print("=" * 80)
    print(f"  ProduccionEjecutivaView: {produccion_esperada_ej}")
    print(f"  ProduccionDashboardView: {produccion_esperada_db}")
    print(f"  ¿SON IGUALES?: {produccion_esperada_ej == produccion_esperada_db}")
    
    if produccion_esperada_ej != produccion_esperada_db:
        print(f"\n  DIFERENCIA ENCONTRADA!")
        print(f"    Diferencia: {abs(produccion_esperada_ej - produccion_esperada_db)}")
        print(f"    Causa probable:")
        print(f"      - ProduccionEjecutivaView usa cutoff_date (última actividad): {last_activity}")
        print(f"      - ProduccionDashboardView usa end_date (fin de período): {month_end}")
    
    return produccion_esperada_ej == produccion_esperada_db

if __name__ == '__main__':
    result = test_expected_production_calculation()
    sys.exit(0 if result else 1)
