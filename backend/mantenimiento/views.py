# views.py
from django.db.models import Sum, Count, Case, When, IntegerField, Q, F
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import OrdenServicioDetalle, OrdenServicioCabecera, Sector, Empleado
from produccion.models import UnidadNegocio, RegistroProduccion
from datetime import datetime, timedelta, date
from .serializers import SectorEfectividadSerializer, EmpleadoEfectividadSerializer, EmpleadoConMovimientoSerializer

# Constantes configurables
HORAS_DIA_LABORAL = 9      # Lunes a viernes
HORAS_DIA_SABADO = 5       # Sábado
HORAS_SEMANA_ESPERADAS = 50  # Total semanal esperado

def calcular_horas_trabajadas(hora_inicio, hora_fin):
    """Calcula las horas trabajadas entre dos objetos time"""
    if not hora_inicio or not hora_fin:
        return 0
    
    try:
        # Convertir time a segundos
        inicio_segundos = hora_inicio.hour * 3600 + hora_inicio.minute * 60 + hora_inicio.second
        fin_segundos = hora_fin.hour * 3600 + hora_fin.minute * 60 + hora_fin.second
        
        # Si la hora fin es menor que la hora inicio, asumimos que cruza medianoche
        if fin_segundos < inicio_segundos:
            diferencia_segundos = (24 * 3600 - inicio_segundos) + fin_segundos
        else:
            diferencia_segundos = fin_segundos - inicio_segundos
        
        return diferencia_segundos / 3600
    except Exception as e:
        print(f"Error calculando horas: {e}")
        return 0

def calcular_horas_extras_campo(horas_extras_time):
    """Calcula las horas extras desde el campo TimeField"""
    if not horas_extras_time:
        return 0
    
    try:
        # Convertir time a horas decimales
        horas_extras_segundos = horas_extras_time.hour * 3600 + horas_extras_time.minute * 60 + horas_extras_time.second
        return horas_extras_segundos / 3600
    except Exception as e:
        print(f"Error calculando horas extras: {e}")
        return 0

def calcular_dias_laborables(fecha_inicio, fecha_fin):
    """Calcula la cantidad de días laborables entre dos fechas"""
    dias_completos = 0  # Lunes a viernes
    dias_sabado = 0     # Sábados
    
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        weekday = fecha_actual.weekday()  # 0 = Lunes, 6 = Domingo
        if weekday < 5:  # Lunes a Viernes
            dias_completos += 1
        elif weekday == 5:  # Sábado
            dias_sabado += 1
        # Domingo (6) no se cuenta
        fecha_actual += timedelta(days=1)
    
    return dias_completos, dias_sabado

@api_view(['GET'])
def efectividad_sector(request):
    """
    Devuelve desempeño por sector (horas prácticas, downtime, extras, efectividad).
    Base: 50 horas/semana por empleado (L-V 9h + S 5h).
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Calcular días laborables en el período
    dias_completos, dias_sabado = calcular_dias_laborables(start_date, end_date)
    
    # Calcular horas esperadas por empleado
    horas_esperadas_por_empleado = (dias_completos * HORAS_DIA_LABORAL + 
                                  dias_sabado * HORAS_DIA_SABADO)

    # Filtrar detalles por rango de fechas
    detalles = OrdenServicioDetalle.objects.filter(
        cabecera__fecha__range=[start_date, end_date],
        hora_inicio__isnull=False,
        hora_fin__isnull=False
    ).select_related('sector')

    # Agrupar por sector y calcular métricas
    sector_data = {}
    
    for detalle in detalles:
        sector_nombre = detalle.sector.descripcion if detalle.sector else "Sin Sector"
        
        if sector_nombre not in sector_data:
            sector_data[sector_nombre] = {
                'horas_practicas': 0,
                'downtime': 0,
                'horas_extras': 0,
                'empleados_unicos': set()
            }
        
        # Calcular horas trabajadas
        horas_trabajadas = calcular_horas_trabajadas(detalle.hora_inicio, detalle.hora_fin)
        
        # Calcular horas extras desde el campo
        horas_extras = calcular_horas_extras_campo(detalle.horas_extras)
            
        sector_data[sector_nombre]['horas_practicas'] += horas_trabajadas
        sector_data[sector_nombre]['horas_extras'] += horas_extras
        sector_data[sector_nombre]['cantidad_empleados'] = detalle.sector.cantidad_empleados if detalle.sector else 0
        # Registrar empleado único (manejar FK rotas)
        try:
            if detalle.mecanico:
                sector_data[sector_nombre]['empleados_unicos'].add(detalle.mecanico.id)
        except Exception:
            # FK rota o empleado eliminado, continuar sin registrar
            pass

    # Calcular downtime y efectividad por sector
    result = []
    for sector, data in sector_data.items():
        # cantidad_empleados = len(data['empleados_unicos'])
        cantidad_empleados = data['cantidad_empleados']

        # Horas esperadas totales para este sector
        horas_esperadas_totales = horas_esperadas_por_empleado * cantidad_empleados if cantidad_empleados > 0 else 0
        
        # Downtime = Horas esperadas - Horas prácticas
        downtime = max(0, horas_esperadas_totales - data['horas_practicas'])
        
        # Efectividad = (Horas prácticas / Horas esperadas) * 100
        efectividad = (data['horas_practicas'] / horas_esperadas_totales * 100) if horas_esperadas_totales > 0 else 0
        
        result.append({
            'sector': sector,
            'horas_practicas': round(data['horas_practicas'], 2),
            'downtime': round(downtime, 2),
            'horas_extras': round(data['horas_extras'], 2),
            'efectividad': round(efectividad, 2),
            'cantidad_empleados': cantidad_empleados
        })

    return Response(result)

@api_view(['GET'])
def efectividad_empleado(request):
    """
    Devuelve desempeño por empleado y sector, con filtro por fecha y empleado.
    Base: 50 horas/semana por empleado (L-V 9h + S 5h).
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    empleado_id = request.query_params.get('empleado')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Calcular días laborables en el período
    dias_completos, dias_sabado = calcular_dias_laborables(start_date, end_date)
    
    # Calcular horas esperadas por empleado
    horas_esperadas = (dias_completos * HORAS_DIA_LABORAL + 
                      dias_sabado * HORAS_DIA_SABADO)

    # Filtrar detalles por rango de fechas
    detalles = OrdenServicioDetalle.objects.filter(
        cabecera__fecha__range=[start_date, end_date],
        hora_inicio__isnull=False,
        hora_fin__isnull=False
    ).select_related('sector', 'mecanico')

    # Si se especifica empleado, filtrar por él
    if empleado_id:
        try:
            empleado_id = int(empleado_id)
            detalles = detalles.filter(mecanico_id=empleado_id)
        except (ValueError, TypeError):
            return Response({"error": "ID de empleado inválido"}, status=400)

    # Agrupar por empleado y sector
    empleado_data = {}
    for detalle in detalles:
        # Manejar FK rotas para mecanico
        try:
            if not detalle.mecanico:
                continue
                
            empleado_key = f"{detalle.mecanico.id}_{detalle.sector.id if detalle.sector else 'sin_sector'}"
            empleado_nombre = detalle.mecanico.nombre
            sector_nombre = detalle.sector.descripcion if detalle.sector else "Sin Sector"
        except Exception:
            # FK rota o empleado eliminado, omitir este detalle
            continue
        
        if empleado_key not in empleado_data:
            empleado_data[empleado_key] = {
                'empleado_id': detalle.mecanico.id,
                'empleado': empleado_nombre,
                'sector': sector_nombre,
                'horas_practicas': 0,
                'downtime': 0,
                'horas_extras': 0
            }
        
        # Calcular horas trabajadas
        horas_trabajadas = calcular_horas_trabajadas(detalle.hora_inicio, detalle.hora_fin)
        
        # Calcular horas extras desde el campo
        horas_extras = calcular_horas_extras_campo(detalle.horas_extras)
            
        empleado_data[empleado_key]['horas_practicas'] += horas_trabajadas
        empleado_data[empleado_key]['horas_extras'] += horas_extras

    # Calcular downtime y efectividad por empleado
    result = []
    for data in empleado_data.values():
        # Downtime = Horas esperadas - Horas prácticas
        downtime = max(0, horas_esperadas - data['horas_practicas'])
        
        # Efectividad = (Horas prácticas / Horas esperadas) * 100
        efectividad = (data['horas_practicas'] / horas_esperadas * 100) if horas_esperadas > 0 else 0
        
        result.append({
            'empleado_id': data['empleado_id'],
            'empleado': data['empleado'],
            'sector': data['sector'],
            'horas_practicas': round(data['horas_practicas'], 2),
            'downtime': round(downtime, 2),
            'horas_extras': round(data['horas_extras'], 2),
            'efectividad': round(efectividad, 2)
        })

    return Response(result)

@api_view(['GET'])
def empleados_con_movimiento(request):
    """
    Devuelve empleados que tuvieron movimiento en un rango de fechas
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Obtener empleados que trabajaron en ese rango
    empleados = Empleado.objects.filter(
        ordenserviciodetalle__cabecera__fecha__range=[start_date, end_date],
        ordenserviciodetalle__hora_inicio__isnull=False,
        ordenserviciodetalle__hora_fin__isnull=False
    ).distinct()

    serializer = EmpleadoConMovimientoSerializer(empleados, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def detalles_sector(request):
    """
    Devuelve los detalles de las tareas realizadas en un sector específico
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    sector_nombre = request.query_params.get('sector')

    if not fecha_inicio or not fecha_fin or not sector_nombre:
        return Response({"error": "Se requieren fechas inicio, fin y sector"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Filtrar detalles por sector y rango de fechas
    detalles = OrdenServicioDetalle.objects.filter(
        cabecera__fecha__range=[start_date, end_date],
        sector__descripcion=sector_nombre,
        hora_inicio__isnull=False,
        hora_fin__isnull=False
    ).select_related('mecanico', 'cabecera').order_by('-cabecera__fecha', 'hora_inicio')

    result = []
    for detalle in detalles:
        # Formatear horas extras
        horas_extras_formatted = None
        if detalle.horas_extras:
            horas_extras_formatted = f"{detalle.horas_extras.hour:02d}:{detalle.horas_extras.minute:02d}"

        # Manejar FK rota para mecanico
        try:
            mecanico_nombre = detalle.mecanico.nombre if detalle.mecanico else 'Sin asignar'
        except Exception:
            mecanico_nombre = 'Sin asignar'

        result.append({
            'fecha': detalle.cabecera.fecha.strftime('%Y-%m-%d'),
            'mecanico': mecanico_nombre,
            'observaciones': detalle.observaciones or 'Sin observaciones',
            'hora_inicio': detalle.hora_inicio.strftime('%H:%M') if detalle.hora_inicio else None,
            'hora_fin': detalle.hora_fin.strftime('%H:%M') if detalle.hora_fin else None,
            'horas_extras': horas_extras_formatted,
            'detalle_tarea': detalle.detalle or 'Sin detalle',
            'orden_servicio': detalle.cabecera.orden_servicio
        })

    return Response(result)

@api_view(['GET'])
def tareas_empleado(request):
    """
    Devuelve todas las tareas realizadas por un empleado en un rango de fechas
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    empleado_id = request.query_params.get('empleado_id')

    if not fecha_inicio or not fecha_fin or not empleado_id:
        return Response({"error": "Se requieren fechas inicio, fin y empleado_id"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        empleado_id = int(empleado_id)
    except ValueError:
        return Response({"error": "Formato de fecha o empleado_id inválido"}, status=400)

    # Filtrar tareas por empleado y rango de fechas
    detalles = OrdenServicioDetalle.objects.filter(
        cabecera__fecha__range=[start_date, end_date],
        mecanico_id=empleado_id,
        hora_inicio__isnull=False,
        hora_fin__isnull=False
    ).select_related('mecanico', 'cabecera', 'sector').order_by('-cabecera__fecha', 'hora_inicio')

    result = []
    for detalle in detalles:
        # Calcular horas trabajadas
        horas_trabajadas = calcular_horas_trabajadas(detalle.hora_inicio, detalle.hora_fin)
        
        # Formatear horas extras
        horas_extras_formatted = None
        if detalle.horas_extras:
            horas_extras_formatted = f"{detalle.horas_extras.hour:02d}:{detalle.horas_extras.minute:02d}"

        result.append({
            'fecha': detalle.cabecera.fecha.strftime('%Y-%m-%d'),
            'sector': detalle.sector.descripcion if detalle.sector else 'Sin sector',
            'hora_inicio': detalle.hora_inicio.strftime('%H:%M') if detalle.hora_inicio else None,
            'hora_fin': detalle.hora_fin.strftime('%H:%M') if detalle.hora_fin else None,
            'horas_trabajadas': round(horas_trabajadas, 2),
            'horas_extras': horas_extras_formatted,
            'detalle_tarea': detalle.detalle or 'Sin detalle de tarea',
            'observaciones': detalle.observaciones or 'Sin observaciones',
            'orden_servicio': detalle.cabecera.orden_servicio
        })

    return Response(result)

@api_view(['GET'])
def resumen_por_equipo(request):
    """
    Devuelve resumen de órdenes de servicio agrupadas por equipo
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    equipo_id = request.query_params.get('equipo')
    tipo_tarea_id = request.query_params.get('tipo_tarea')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Filtrar órdenes por rango de fechas
    ordenes_query = OrdenServicioCabecera.objects.filter(
        fecha__range=[start_date, end_date]
    ).select_related('equipo', 'unidad_negocio')

    # Si se especifica equipo, filtrar por él
    if equipo_id:
        try:
            equipo_id = int(equipo_id)
            ordenes_query = ordenes_query.filter(equipo_id=equipo_id)
        except (ValueError, TypeError):
            return Response({"error": "ID de equipo inválido"}, status=400)

    # Agrupar por equipo y calcular métricas
    equipo_data = {}
    
    for orden in ordenes_query:
        if not orden.equipo:
            continue
            
        # Filtrar detalles por tipo de tarea si se especificó
        detalles = OrdenServicioDetalle.objects.filter(cabecera=orden)
        if tipo_tarea_id:
            try:
                tipo_tarea_int = int(tipo_tarea_id)
                detalles = detalles.filter(tipo_tarea_id=tipo_tarea_int)
            except (ValueError, TypeError):
                return Response({"error": "ID de tipo_tarea inválido"}, status=400)
        
        detalles = detalles.select_related('mecanico', 'sector', 'repuesto')
        
        # Si hay filtro de tipo_tarea y esta orden no tiene detalles de ese tipo, omitirla
        if tipo_tarea_id and not detalles.exists():
            continue
            
        equipo_key = orden.equipo.id
        equipo_nombre = str(orden.equipo) if orden.equipo else "Sin Equipo"
        un_nombre = orden.unidad_negocio.nombre if orden.unidad_negocio else "Sin UN"
        
        if equipo_key not in equipo_data:
            equipo_data[equipo_key] = {
                'equipo_id': equipo_key,
                'equipo': equipo_nombre,
                'unidad_negocio': un_nombre,
                'total_ordenes': 0,
                'ordenes_cerradas': 0,
                'ordenes_abiertas': 0,
                'tareas_preventivas': 0,
                'tareas_correctivas': 0,
                'total_horas_trabajo': 0,
                'total_horas_extras': 0,
                'total_costo_repuestos': 0,
                'cantidad_repuestos': 0,
                'mecanicos_involucrados': set(),
                'sectores_involucrados': set(),
                'total_tareas': 0
            }
        
        # Contar órdenes por estado
        equipo_data[equipo_key]['total_ordenes'] += 1
        if orden.estado and orden.estado.lower() == 'cerrado':
            equipo_data[equipo_key]['ordenes_cerradas'] += 1
        else:
            equipo_data[equipo_key]['ordenes_abiertas'] += 1
        
        # Analizar detalles de la orden (ya filtrados por tipo_tarea si corresponde)
        for detalle in detalles:
            equipo_data[equipo_key]['total_tareas'] += 1
            
            # Clasificar por tipo de mantenimiento
            if detalle.preventivo:
                equipo_data[equipo_key]['tareas_preventivas'] += 1
            if detalle.correctivo:
                equipo_data[equipo_key]['tareas_correctivas'] += 1
            
            # Calcular horas trabajadas
            if detalle.hora_inicio and detalle.hora_fin:
                horas_trabajadas = calcular_horas_trabajadas(detalle.hora_inicio, detalle.hora_fin)
                equipo_data[equipo_key]['total_horas_trabajo'] += horas_trabajadas
            
            # Calcular horas extras
            if detalle.horas_extras:
                horas_extras = calcular_horas_extras_campo(detalle.horas_extras)
                equipo_data[equipo_key]['total_horas_extras'] += horas_extras
            
            # Calcular costos de repuestos
            if detalle.repuesto and detalle.cantidad and detalle.precio_unitario:
                costo_repuesto = detalle.cantidad * detalle.precio_unitario
                equipo_data[equipo_key]['total_costo_repuestos'] += costo_repuesto
                equipo_data[equipo_key]['cantidad_repuestos'] += detalle.cantidad
            
            # Registrar mecánicos y sectores involucrados
            try:
                if detalle.mecanico:
                    equipo_data[equipo_key]['mecanicos_involucrados'].add(detalle.mecanico.nombre)
            except Exception:
                # FK rota, omitir mecánico
                pass
            if detalle.sector:
                equipo_data[equipo_key]['sectores_involucrados'].add(detalle.sector.descripcion)

    # Formatear resultado
    result = []
    for data in equipo_data.values():
        # Calcular métricas adicionales
        porcentaje_ordenes_cerradas = (data['ordenes_cerradas'] / data['total_ordenes'] * 100) if data['total_ordenes'] > 0 else 0
        promedio_horas_por_orden = (data['total_horas_trabajo'] / data['total_ordenes']) if data['total_ordenes'] > 0 else 0
        promedio_tareas_por_orden = (data['total_tareas'] / data['total_ordenes']) if data['total_ordenes'] > 0 else 0
        
        result.append({
            'equipo_id': data['equipo_id'],
            'equipo': data['equipo'],
            'unidad_negocio': data['unidad_negocio'],
            'total_ordenes': data['total_ordenes'],
            'ordenes_cerradas': data['ordenes_cerradas'],
            'ordenes_abiertas': data['ordenes_abiertas'],
            'porcentaje_cerradas': round(porcentaje_ordenes_cerradas, 2),
            'total_tareas': data['total_tareas'],
            'tareas_preventivas': data['tareas_preventivas'],
            'tareas_correctivas': data['tareas_correctivas'],
            'promedio_tareas_por_orden': round(promedio_tareas_por_orden, 2),
            'total_horas_trabajo': round(data['total_horas_trabajo'], 2),
            'total_horas_extras': round(data['total_horas_extras'], 2),
            'promedio_horas_por_orden': round(promedio_horas_por_orden, 2),
            'total_costo_repuestos': round(data['total_costo_repuestos'], 2),
            'cantidad_repuestos': round(data['cantidad_repuestos'], 2),
            'cantidad_mecanicos': len(data['mecanicos_involucrados']),
            'cantidad_sectores': len(data['sectores_involucrados']),
            'mecanicos': sorted(list(data['mecanicos_involucrados'])),
            'sectores': sorted(list(data['sectores_involucrados']))
        })
    
    # Ordenar por equipo
    result.sort(key=lambda x: x['equipo'])
    
    return Response(result)

@api_view(['GET'])
def equipos_con_ordenes(request):
    """
    Devuelve equipos que tuvieron órdenes de servicio en un rango de fechas
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Obtener equipos que tuvieron órdenes en ese rango
    equipos = OrdenServicioCabecera.objects.filter(
        fecha__range=[start_date, end_date]
    ).values(
        'equipo__id', 
        'equipo__detalle','equipo__patente'
    ).distinct().order_by('equipo__detalle')

    result = [
        {
            'id': equipo['equipo__id'],
            'nombre': f"{equipo['equipo__patente']} - {equipo['equipo__detalle']}"
        }
        for equipo in equipos if equipo['equipo__id'] and equipo['equipo__detalle']
    ]

    return Response(result)

@api_view(['GET'])
def ordenes_por_equipo(request):
    """
    Devuelve las órdenes de servicio de un equipo específico en un rango de fechas
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    equipo_id = request.query_params.get('equipo_id')

    if not fecha_inicio or not fecha_fin or not equipo_id:
        return Response({"error": "Se requieren fechas inicio, fin y equipo_id"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        equipo_id = int(equipo_id)
    except ValueError:
        return Response({"error": "Formato de fecha o equipo_id inválido"}, status=400)

    # Filtrar órdenes por equipo y rango de fechas
    ordenes = OrdenServicioCabecera.objects.filter(
        fecha__range=[start_date, end_date],
        equipo_id=equipo_id
    ).select_related('equipo', 'unidad_negocio').order_by('-fecha', '-orden_servicio')

    result = []
    for orden in ordenes:
        # Obtener detalles de la orden
        detalles = OrdenServicioDetalle.objects.filter(cabecera=orden).select_related(
            'mecanico', 'sector', 'repuesto'
        )
        
        # Calcular métricas de la orden
        total_horas_trabajo = 0
        total_horas_extras = 0
        total_costo_repuestos = 0
        mecanicos = set()
        sectores = set()
        tareas_preventivas = 0
        tareas_correctivas = 0
        total_repuestos = 0
        
        detalles_lista = []
        
        for detalle in detalles:
            # Calcular horas trabajadas
            if detalle.hora_inicio and detalle.hora_fin:
                horas_trabajadas = calcular_horas_trabajadas(detalle.hora_inicio, detalle.hora_fin)
                total_horas_trabajo += horas_trabajadas
            else:
                horas_trabajadas = 0
            
            # Calcular horas extras
            if detalle.horas_extras:
                horas_extras = calcular_horas_extras_campo(detalle.horas_extras)
                total_horas_extras += horas_extras
            else:
                horas_extras = 0
            
            # Calcular costos de repuestos
            costo_repuesto = 0
            if detalle.repuesto and detalle.cantidad and detalle.precio_unitario:
                costo_repuesto = detalle.cantidad * detalle.precio_unitario
                total_costo_repuestos += costo_repuesto
                total_repuestos += detalle.cantidad
            
            # Registrar mecánicos y sectores
            try:
                if detalle.mecanico:
                    mecanicos.add(detalle.mecanico.nombre)
            except Exception:
                # FK rota, omitir mecánico
                pass
            if detalle.sector:
                sectores.add(detalle.sector.descripcion)
            
            # Contar tipos de mantenimiento
            if detalle.preventivo:
                tareas_preventivas += 1
            if detalle.correctivo:
                tareas_correctivas += 1
            
            # Formatear horas extras para mostrar
            horas_extras_formatted = None
            if detalle.horas_extras:
                horas_extras_formatted = f"{detalle.horas_extras.hour:02d}:{detalle.horas_extras.minute:02d}"
            
            # Manejar FK rota para mecanico en detalle
            try:
                mecanico_nombre = detalle.mecanico.nombre if detalle.mecanico else 'Sin asignar'
            except Exception:
                mecanico_nombre = 'Sin asignar'
            
            detalles_lista.append({
                'detalle_id': detalle.id,
                'mecanico': mecanico_nombre,
                'sector': detalle.sector.descripcion if detalle.sector else 'Sin sector',
                'km_hora': detalle.km_hora if detalle.km_hora else 0,
                'hora_inicio': detalle.hora_inicio.strftime('%H:%M') if detalle.hora_inicio else None,
                'hora_fin': detalle.hora_fin.strftime('%H:%M') if detalle.hora_fin else None,
                'horas_trabajadas': round(horas_trabajadas, 2),
                'horas_extras': horas_extras_formatted,
                'detalle_tarea': detalle.detalle or 'Sin detalle',
                'observaciones': detalle.observaciones or 'Sin observaciones',
                'preventivo': detalle.preventivo,
                'correctivo': detalle.correctivo,
                'repuesto': str(detalle.repuesto) if detalle.repuesto else None,
                'cantidad_repuesto': detalle.cantidad if detalle.cantidad else 0,
                'precio_unitario': detalle.precio_unitario if detalle.precio_unitario else 0,
                'costo_repuesto': round(costo_repuesto, 2)
            })
        
        result.append({
            'orden_servicio': orden.orden_servicio,
            'fecha': orden.fecha.strftime('%Y-%m-%d'),
            'equipo': str(orden.equipo) if orden.equipo else 'Sin Equipo',
            'unidad_negocio': orden.unidad_negocio.nombre if orden.unidad_negocio else 'Sin UN',
            'estado': orden.estado or 'Sin estado',
            'descripcion': orden.descripcion or 'Sin descripción',
            'observaciones': orden.descripcion or 'Sin observaciones',
            'total_tareas': len(detalles_lista),
            'tareas_preventivas': tareas_preventivas,
            'tareas_correctivas': tareas_correctivas,
            'total_horas_trabajo': round(total_horas_trabajo, 2),
            'total_horas_extras': round(total_horas_extras, 2),
            'total_costo_repuestos': round(total_costo_repuestos, 2),
            'total_repuestos': round(total_repuestos, 2),
            'mecanicos_involucrados': sorted(list(mecanicos)),
            'sectores_involucrados': sorted(list(sectores)),
            'cantidad_mecanicos': len(mecanicos),
            'cantidad_sectores': len(sectores),
            'detalles': detalles_lista
        })
    
    return Response(result)


@api_view(['GET'])
def tipos_tareas_con_movimiento(request):
    """
    Devuelve los tipos de tareas que tuvieron movimiento en el rango de fechas provisto
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Obtener tipos de tareas que aparecen en OrdenServicioDetalle dentro del rango
    tipos = OrdenServicioDetalle.objects.filter(
        cabecera__fecha__range=[start_date, end_date]
    ).values('tipo_tarea_id', 'tipo_tarea__tarea').distinct()

    result = []
    for t in tipos:
        if t.get('tipo_tarea_id'):
            result.append({
                'id': t.get('tipo_tarea_id'),
                'tarea': t.get('tipo_tarea__tarea') or 'Sin nombre'
            })

    # Ordenar por nombre de tarea
    result.sort(key=lambda x: x['tarea'])
    return Response(result)

@api_view(['GET'])
def kpis_mantenimiento(request):
    """
    Calcula MTBF, MTTR y Downtime para una Unidad de Negocio en un rango de fechas.
    Si se especifica unidad_negocio, devuelve KPIs globales + KPIs por equipo.
    Utiliza tablero_produccion para obtener horas trabajadas por equipo.
    """
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    unidad_negocio_id = request.query_params.get('unidad_negocio')

    if not fecha_inicio or not fecha_fin:
        return Response({"error": "Se requieren fechas inicio y fin"}, status=400)

    try:
        start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end_date = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

    # Filtro base para fallas correctivas
    filters = {
        'cabecera__fecha__range': [start_date, end_date],
        'correctivo': True, # Solo fallas correctivas para MTBF/MTTR/Downtime
        'hora_inicio__isnull': False,
        'hora_fin__isnull': False
    }

    if unidad_negocio_id:
        filters['cabecera__unidad_negocio_id'] = unidad_negocio_id

    detalles = OrdenServicioDetalle.objects.filter(**filters).select_related('cabecera', 'cabecera__equipo')

    total_downtime_hours = 0
    cantidad_fallas = detalles.count()
    
    # Agrupar por equipo para calcular KPIs individuales
    equipos_data = {}
    
    # Calcular Downtime total y por equipo
    for detalle in detalles:
        horas_reparacion = calcular_horas_trabajadas(detalle.hora_inicio, detalle.hora_fin)
        horas_extras = calcular_horas_extras_campo(detalle.horas_extras)
        downtime_detalle = horas_reparacion + horas_extras
        total_downtime_hours += downtime_detalle
        
        # Agrupar por equipo
        equipo = detalle.cabecera.equipo
        if equipo:
            equipo_key = equipo.id
            if equipo_key not in equipos_data:
                equipos_data[equipo_key] = {
                    'equipo_id': equipo.id,
                    'equipo_nombre': f"{equipo.patente} - {equipo.detalle}",
                    'downtime': 0,
                    'cantidad_fallas': 0,
                    'horas_trabajadas': 0,
                    'unidad_negocio': None
                }
            equipos_data[equipo_key]['downtime'] += downtime_detalle
            equipos_data[equipo_key]['cantidad_fallas'] += 1

    # Obtener horas trabajadas de tablero_produccion para cada equipo
    filtro_produccion = Q(fecha__range=[start_date, end_date])
    if unidad_negocio_id:
        filtro_produccion &= Q(cod_un_id=unidad_negocio_id)
    
    # Obtener todos los equipos con horas trabajadas, incluyendo los que no tienen fallas
    equipos_produccion = RegistroProduccion.objects.filter(
        filtro_produccion,
        cod_equipo_id__isnull=False
    ).values(
        'cod_equipo_id',
        'cod_equipo__patente',
        'cod_equipo__detalle',
        'cod_un__nombre'
    ).annotate(
        total_horas=Sum(F('hr_fin') - F('hr_inicio'))
    ).order_by('cod_equipo_id')
    
    # Actualizar horas trabajadas y agregar equipos sin fallas
    for equipo_prod in equipos_produccion:
        equipo_id = equipo_prod['cod_equipo_id']
        horas = float(equipo_prod['total_horas'] or 0)
        
        if equipo_id in equipos_data:
            # Equipo con fallas, actualizar horas trabajadas
            equipos_data[equipo_id]['horas_trabajadas'] = horas
            equipos_data[equipo_id]['unidad_negocio'] = equipo_prod['cod_un__nombre']
        else:
            # Equipo sin fallas, agregarlo
            equipos_data[equipo_id] = {
                'equipo_id': equipo_id,
                'equipo_nombre': f"{equipo_prod['cod_equipo__patente']} - {equipo_prod['cod_equipo__detalle']}",
                'downtime': 0,
                'cantidad_fallas': 0,
                'horas_trabajadas': horas,
                'unidad_negocio': equipo_prod['cod_un__nombre']
            }

    # Calcular MTTR (Mean Time To Repair) global
    # MTTR = Total Downtime / Número de fallas
    mttr = (total_downtime_hours / cantidad_fallas) if cantidad_fallas > 0 else 0

    # Calcular tiempo total trabajado de todos los equipos
    total_horas_trabajadas = sum(data['horas_trabajadas'] for data in equipos_data.values())
    
    # Calcular MTBF global
    # MTBF = (Tiempo Total Trabajado - Downtime) / Número de fallas
    if cantidad_fallas > 0:
        mtbf = (total_horas_trabajadas - total_downtime_hours) / cantidad_fallas if total_horas_trabajadas > 0 else 0
    else:
        mtbf = total_horas_trabajadas

    # Contar equipos únicos analizados
    equipos_activos_count = len(equipos_data)

    # Calcular KPIs por equipo
    equipos_kpis = []
    for equipo_id, data in equipos_data.items():
        # MTTR por equipo
        mttr_equipo = (data['downtime'] / data['cantidad_fallas']) if data['cantidad_fallas'] > 0 else 0
        
        # MTBF por equipo
        # MTBF = (Horas Trabajadas - Downtime) / Número de fallas
        horas_disponibles = data['horas_trabajadas']
        if data['cantidad_fallas'] > 0 and horas_disponibles > 0:
            mtbf_equipo = (horas_disponibles - data['downtime']) / data['cantidad_fallas']
        else:
            mtbf_equipo = horas_disponibles
        
        # Disponibilidad = (Horas Trabajadas - Downtime) / Horas Trabajadas * 100
        if horas_disponibles > 0:
            disponibilidad = ((horas_disponibles - data['downtime']) / horas_disponibles * 100)
        else:
            disponibilidad = 0
        
        equipos_kpis.append({
            'equipo_id': data['equipo_id'],
            'equipo_nombre': data['equipo_nombre'],
            'unidad_negocio': data['unidad_negocio'] or 'Sin asignar',
            'mtbf': round(mtbf_equipo, 2),
            'mttr': round(mttr_equipo, 2),
            'downtime': round(data['downtime'], 2),
            'horas_trabajadas': round(horas_disponibles, 2),
            'cantidad_fallas': data['cantidad_fallas'],
            'disponibilidad': round(disponibilidad, 2)
        })
    
    # Ordenar por downtime descendente
    equipos_kpis.sort(key=lambda x: x['downtime'], reverse=True)

    # Disponibilidad global
    disponibilidad_global = ((total_horas_trabajadas - total_downtime_hours) / total_horas_trabajadas * 100) if total_horas_trabajadas > 0 else 0

    return Response({
        'mtbf': round(mtbf, 2),
        'mttr': round(mttr, 2),
        'downtime': round(total_downtime_hours, 2),
        'cantidad_fallas': cantidad_fallas,
        'equipos_analizados': equipos_activos_count,
        'total_horas_trabajadas': round(total_horas_trabajadas, 2),
        'disponibilidad_global': round(disponibilidad_global, 2),
        'unidad_negocio': unidad_negocio_id,
        'equipos': equipos_kpis
    })