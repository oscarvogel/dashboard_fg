import calendar
from rest_framework.decorators import api_view
from django.http import JsonResponse
import logging
import os

from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
import django_filters as df                            # django-filter
from django.contrib.auth import authenticate

from django.db.models import Q, Sum
from django.db import models
from django.contrib.auth.hashers import check_password as django_check_password

from django.db.models.functions import Trim
from django.utils.dateparse import parse_date

# Create your views here.
from produccion_api.BaseViewSet import BaseAppModelViewSet, DebugSerializerErrorsMixin, StandarPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework import filters
from rest_framework.permissions import AllowAny  # 👈 Recomendado

from .models import CargaCombustible, Empleado, Equipo, ProduccionMensual, RegistroProduccion, UnidadNegocio
from .serializers import CargaCombustibleSerializer, EmpleadoSerializer, EquipoSerializer, LoginSerializer, RegistroProduccionDiarioSerializer, RegistroProduccionSerializer
from .combustible_services import (
    combustible_equipo_lh,
    combustible_equipo_vs_historico,
    combustible_sin_produccion,
    parse_consulta_params,
)
from .facturacion_services import calcular_facturacion_movil, parse_facturacion_params
from .indicadores_services import calcular_movil_operativo, parse_movil_operativo_params
from django.db.models import Sum, F
from datetime import datetime
from datetime import timedelta, date

# logger para esta vista: además guardar en backend/logs/produccion_queries.log
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logs_dir = os.path.join(base_dir, 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, 'produccion_queries.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Añadir handler si no existe para evitar duplicados
if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '') == os.path.abspath(log_file) for h in logger.handlers):
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)


class CombustibleEquipoLHView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = parse_consulta_params(request.query_params)
        return Response(combustible_equipo_lh(**params))


class CombustibleEquipoVsHistoricoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = parse_consulta_params(request.query_params, include_history=True)
        return Response(combustible_equipo_vs_historico(**params))


class CombustibleSinProduccionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        params = parse_consulta_params(request.query_params)
        return Response(combustible_sin_produccion(**params))


class FacturacionMovilView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        params = parse_facturacion_params(request.query_params)
        try:
            result = calcular_facturacion_movil(**params)
        except Equipo.DoesNotExist:
            return Response(
                {"movil_id": ["No existe un móvil con el identificador indicado."]},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)


class MovilOperativoView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        params = parse_movil_operativo_params(request.query_params)
        try:
            result = calcular_movil_operativo(**params)
        except Equipo.DoesNotExist:
            return Response(
                {"movil_id": ["No existe un móvil con el identificador indicado."]},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(result)

class ProduccionOperadorView(APIView):

    def get(self, request):
        operador_id = request.GET.get('operador_id') or request.GET.get('operador')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not operador_id or not fecha_inicio or not fecha_fin:
            return Response(
                {"error": "Faltan parámetros: operador u operador_id, fecha_inicio, fecha_fin"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Usa YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            operador_id = int(operador_id)
            if operador_id <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "operador_id debe ser un entero positivo"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registros = RegistroProduccion.objects.filter(
            cod_operador_id=operador_id,
            fecha__range=[fecha_inicio, fecha_fin]
        ).select_related('cod_operador', 'cod_equipo', 'cod_un', 'origen_camion').order_by('-fecha')

        if not registros.exists():
            return Response({"error": "No se encontraron registros"}, status=status.HTTP_404_NOT_FOUND)

        # Acumulados
        m3_total = registros.aggregate(total=Sum('m3'))['total'] or 0
        litros_total = registros.aggregate(
            total=Sum(F('combustible'))
        )['total'] or 0.00
        plantas_total = registros.aggregate(total=Sum('plantas'))['total'] or 0

        # Horas trabajadas
        registros = registros.annotate(
            horas_trabajadas=F('hr_fin') - F('hr_inicio')
        )
        horas_total = sum(float(r.horas_trabajadas) for r in registros)

        # Último registro
        ultimo_registro = registros.first()
        ultimo_registro_data = RegistroProduccionSerializer(ultimo_registro).data

        # Producción por hora promedio
        produccion_total = registros.aggregate(total=Sum('produccion'))['total'] or 0.00
        produccion_por_hora = round(float(produccion_total) / float(horas_total), 2) if horas_total > 0 else 0.00

        return Response({
            "operador_id": ultimo_registro.cod_operador_id,
            "operador": ultimo_registro.cod_operador.nombre,
            "produccion_acumulada_mensual": {
                "m3": m3_total,
                "litros": float(litros_total),
                "horas_trabajadas": round(horas_total, 2),
                "plantas": round(plantas_total, 2),
            },
            "ultimo_registro": ultimo_registro_data,
            "promedio_produccion_por_hora": produccion_por_hora
        })

class EmpleadoViewSet(BaseAppModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nombre']  # Asegúrate de que 'nombre' es el campo correcto en el modelo 'Clientes'
    ordering_fields = ['nombre']        

class LoginEmpleadoView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        dni = request.data.get('dni')
        password = request.data.get('password')

        user = authenticate(username=dni, password=password)
        if not user:
            return Response(
                {"error": "Credenciales inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            empleado = Empleado.objects.get(user=user)
        except Empleado.DoesNotExist:
            return Response(
                {"error": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "operador": EmpleadoSerializer(empleado).data
        }, status=status.HTTP_200_OK)

class RegistrosEmpleadoViewSet(DebugSerializerErrorsMixin, viewsets.GenericViewSet):
    serializer_class = RegistroProduccionSerializer
    pagination_class = StandarPagination
    
    # Necesario para evitar el error: debe haber un queryset o get_queryset()
    def get_queryset(self):
        # Devolvemos un queryset vacío, ya que lo filtramos dinámicamente en list()
        return RegistroProduccion.objects.none()
    
    def list(self, request, *args, **kwargs):
        empleado_id = request.GET.get('id')  # Recibimos el ID del empleado
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not empleado_id or not fecha_inicio or not fecha_fin:
            return Response(
                {"error": "Faltan parámetros: id, fecha_inicio, fecha_fin"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Usa YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar el empleado
        try:
            empleado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            return Response(
                {"error": "Empleado no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Filtrar registros
        registros = RegistroProduccion.objects.filter(
            cod_operador_id=empleado_id,
            fecha__range=[fecha_inicio, fecha_fin]
        ).select_related('cod_operador', 'cod_equipo', 'cod_un', 'origen_camion').order_by('fecha')

        # Paginación
        page = self.paginate_queryset(registros)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(registros, many=True)

        return Response({
            "empleado": {
                "id": empleado.id,
                "nombre": empleado.nombre,
                "dni": empleado.dni
            },
            "rango_fechas": {
                "inicio": str(fecha_inicio),
                "fin": str(fecha_fin)
            },
            "total_registros": len(serializer.data),
            "registros": serializer.data
        }, status=status.HTTP_200_OK)
             
class FiltrosDinamicosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        cod_un = request.GET.get('cod_un')  # Puede ser múltiple: "1,2,3"
        operacion = request.GET.get('operacion')  # Puede ser múltiple: "VOLTEO,EXTRACCION"
        acta = request.GET.get('acta')
        predio = request.GET.get('predio')

        filtro = Q()
        if start_date:
            filtro &= Q(fecha__gte=start_date)
        if end_date:
            filtro &= Q(fecha__lte=end_date)
        
        # Manejo de múltiples unidades de negocio
        if cod_un:
            try:
                # Dividir por comas y convertir a enteros
                cod_un_ids = [int(x.strip()) for x in cod_un.split(',') if x.strip()]
                if cod_un_ids:
                    filtro &= Q(cod_un_id__in=cod_un_ids)
            except (ValueError, TypeError):
                pass  # Ignorar si no son números válidos
        
        # Manejo de múltiples operaciones
        if operacion:
            operaciones = [x.strip() for x in operacion.split(',') if x.strip()]
            if operaciones:
                filtro &= Q(operacion__in=operaciones)
        
        if acta:
            filtro &= Q(acta=acta)

        # Si no hay fechas, devolver listas vacías
        if not start_date and not end_date:
            return Response({
                "operaciones": [],
                "unidades": [],
                "equipos": [],
                "operadores": [],
                "actas": [],
                "predios": []
            })

        registros = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo', 'cod_un', 'cod_operador', 'origen_camion')

        # Obtener opciones únicas
        operaciones = list(registros.values_list('operacion', flat=True).distinct().order_by('operacion'))
        operadores_qs = (
            registros.values('cod_operador_id', 'cod_operador__nombre')
            .distinct()
            .order_by('cod_operador__nombre', 'cod_operador_id')
        )
        operadores = [
            {'id': item['cod_operador_id'], 'nombre': item['cod_operador__nombre']}
            for item in operadores_qs
            if item['cod_operador_id'] and item['cod_operador__nombre']
        ]
        equipos = list(registros.values_list('cod_equipo__detalle', flat=True).distinct().order_by('cod_equipo__detalle'))
        actas = list(registros.values_list('acta', flat=True).distinct().order_by('acta'))
        predios = list(registros.values_list('predio', flat=True).distinct().order_by('predio'))


        # Unidades: obtener id y nombre
        unidades_qs = (
            registros
            .values('cod_un_id', 'cod_un__nombre')
            .distinct()
            .order_by('cod_un__nombre')
        )
        unidades = [
            {'id': item['cod_un_id'], 'nombre': item['cod_un__nombre']}
            for item in unidades_qs
            if item['cod_un_id']
        ]

        return Response({
            "operaciones": [op for op in operaciones if op],
            "unidades": unidades,
            "equipos": [eq for eq in equipos if eq],
            "operadores": operadores,
            "actas": [a for a in actas if a],
            "predios": [p for p in predios if p]
        })


class UnidadesNegocioActivasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')

        if not month or not year:
            return Response(
                {"error": "Los parámetros 'month' y 'year' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month_int = int(month)
            year_int = int(year)
            if month_int < 1 or month_int > 12:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "Parámetros inválidos. Usa month (1-12) y year (YYYY)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date = date(year_int, month_int, 1)
        end_date = date(year_int, month_int, calendar.monthrange(year_int, month_int)[1])

        unidades_qs = (
            RegistroProduccion.objects
            .filter(fecha__range=[start_date, end_date], cod_un__isnull=False)
            .values('cod_un_id', 'cod_un__nombre')
            .distinct()
            .order_by('cod_un__nombre')
        )

        unidades = [
            {"id": item['cod_un_id'], "nombre": item['cod_un__nombre']}
            for item in unidades_qs
            if item['cod_un_id'] and item['cod_un__nombre']
        ]

        return Response({
            "unidades": unidades,
            "periodo": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        })


class ProduccionEjecutivaView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _safe_float(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _safe_ratio(numerator, denominator):
        if denominator <= 0:
            return 0.0
        return round(numerator / denominator, 2)

    def get(self, request):
        month = request.GET.get('month')
        year = request.GET.get('year')
        day = request.GET.get('day')
        cod_un = request.GET.get('cod_un')
        tipo_operacion = request.GET.get('tipo_operacion', 'PROCESO')  # Por defecto filtrar por PROCESO

        if not month or not year or not cod_un:
            return Response(
                {"error": "Los parámetros 'month', 'year' y 'cod_un' son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            month_int = int(month)
            year_int = int(year)
            cod_un_id = int(cod_un)
            if month_int < 1 or month_int > 12:
                raise ValueError
        except ValueError:
            return Response(
                {"error": "Parámetros inválidos. Usa month (1-12), year (YYYY) y cod_un numérico."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not UnidadNegocio.objects.filter(id=cod_un_id).exists():
            return Response(
                {"error": "La unidad de negocio no existe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date = date(year_int, month_int, 1)
        month_end = date(year_int, month_int, calendar.monthrange(year_int, month_int)[1])

        # Queryset base SIN filtro de operación → para detectar cutoff y construir tablas
        base_qs_all = RegistroProduccion.objects.filter(
            fecha__range=[start_date, month_end],
            cod_un_id=cod_un_id,
        )
        # Queryset filtrado por tipo_operacion → para KPIs y registros
        base_qs_kpi = base_qs_all.filter(operacion=tipo_operacion)

        if day:
            try:
                day_int = int(day)
                if day_int < 1 or day_int > month_end.day:
                    raise ValueError
                cutoff_date = date(year_int, month_int, day_int)
            except ValueError:
                return Response(
                    {"error": "Parámetro 'day' inválido para el mes seleccionado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            cutoff_date = base_qs_kpi.aggregate(max_fecha=models.Max('fecha')).get('max_fecha')
            if not cutoff_date:
                cutoff_date = month_end

        # filtered_qs para KPIs y registros (con filtro de tipo_operacion)
        filtered_qs = base_qs_kpi.filter(fecha__lte=cutoff_date).select_related('cod_equipo', 'cod_un').order_by('-fecha', '-hr_fin')
        # all_filtered_qs para tablas (todos los equipos de la UN)
        all_filtered_qs = base_qs_all.filter(fecha__lte=cutoff_date).select_related('cod_equipo', 'cod_un').order_by('-fecha', '-hr_fin')

        periodo = cutoff_date.strftime('%Y%m')
        dias_del_mes = sum(
            1 for d in range(1, calendar.monthrange(cutoff_date.year, cutoff_date.month)[1] + 1)
            if date(cutoff_date.year, cutoff_date.month, d).weekday() < 5
        )
        dias_habiles_rango = sum(
            1 for d in range((cutoff_date - start_date).days + 1)
            if (start_date + timedelta(days=d)).weekday() < 5
        )
        proporcion = dias_habiles_rango / dias_del_mes if dias_del_mes > 0 else 0

        queryset_mensual = ProduccionMensual.objects.filter(
            periodo=periodo,
            unidad_negocio_id=cod_un_id,
            tipo_operacion=tipo_operacion,  # Filtrar por tipo de operación (default: PROCESO)
        )

        unidad_produccion = queryset_mensual.values_list('unidad_produccion', flat=True).distinct().first()
        if not unidad_produccion:
            unidad_produccion = (
                filtered_qs.exclude(unidad_produccion__isnull=True)
                .exclude(unidad_produccion='')
                .values_list('unidad_produccion', flat=True)
                .first()
            )

        agregado = queryset_mensual.aggregate(
            meta_mensual=Sum('produccion'),
        )
        meta_mensual = self._safe_float(agregado.get('meta_mensual'))
        produccion_esperada_acumulada = round(meta_mensual * proporcion, 2)

        jornadas = calcular_jornadas_en_rango(start_date, cutoff_date)
        total_jornadas = sum(jornada for _, jornada in jornadas)
        if total_jornadas == 0:
            produccion_esperada_por_dia = {item[0]: 0.0 for item in jornadas}
        else:
            produccion_diaria_base = produccion_esperada_acumulada / total_jornadas
            produccion_esperada_por_dia = {
                fecha: round(jornada * produccion_diaria_base, 2)
                for fecha, jornada in jornadas
            }

        equipos = {}
        for reg in all_filtered_qs:  # Todos los equipos de la UN (sin filtro de operación)
            equipo_id = reg.cod_equipo_id or f"sin-equipo-{reg.id}"
            equipo_nombre = (
                reg.cod_equipo.detalle if reg.cod_equipo and reg.cod_equipo.detalle
                else reg.equipo or 'Sin equipo'
            )
            horas = max(0.0, self._safe_float(reg.hr_fin) - self._safe_float(reg.hr_inicio))
            m3 = self._safe_float(reg.m3)
            combustible = self._safe_float(reg.combustible)
            produccion = self._safe_float(reg.produccion)
            plantas = self._safe_float(reg.plantas)

            if equipo_id not in equipos:
                equipos[equipo_id] = {
                    'equipo': equipo_nombre,
                    'unidad_produccion': reg.unidad_produccion or '',
                    'horas_dia': 0.0,
                    'combustible_dia': 0.0,
                    'm3_dia': 0.0,
                    'produccion_dia': 0.0,
                    'plantas_dia': 0.0,
                    'horas_acum': 0.0,
                    'combustible_acum': 0.0,
                    'm3_acum': 0.0,
                    'produccion_acum': 0.0,
                    'plantas_acum': 0.0,
                }

            row = equipos[equipo_id]
            if not row['unidad_produccion'] and reg.unidad_produccion:
                row['unidad_produccion'] = reg.unidad_produccion

            row['horas_acum'] += horas
            row['combustible_acum'] += combustible
            row['m3_acum'] += m3
            row['produccion_acum'] += produccion
            row['plantas_acum'] += plantas

            if reg.fecha == cutoff_date:
                row['horas_dia'] += horas
                row['combustible_dia'] += combustible
                row['m3_dia'] += m3
                row['produccion_dia'] += produccion
                row['plantas_dia'] += plantas

        tabla_consumo = []
        tabla_produccion = []
        for row in sorted(equipos.values(), key=lambda x: x['equipo'].lower()):
            tabla_consumo.append({
                'equipo': row['equipo'],
                'lts_hora_dia': self._safe_ratio(row['combustible_dia'], row['horas_dia']),
                'lts_hora_acumulado': self._safe_ratio(row['combustible_acum'], row['horas_acum']),
                'lts_m3_dia': self._safe_ratio(row['combustible_dia'], row['m3_dia']),
                'lts_m3_acumulado': self._safe_ratio(row['combustible_acum'], row['m3_acum']),
            })

            tabla_produccion.append({
                'equipo': row['equipo'],
                'unidad_produccion': row['unidad_produccion'] or unidad_produccion or '',
                'produccion_dia': round(row['produccion_dia'], 2),
                'produccion_acumulada': round(row['produccion_acum'], 2),
                'produccion_hora_dia': self._safe_ratio(row['produccion_dia'], row['horas_dia']),
                'produccion_hora_acumulada': self._safe_ratio(row['produccion_acum'], row['horas_acum']),
                'produccion_arbol_dia': self._safe_ratio(row['produccion_dia'], row['plantas_dia']),
                'produccion_arbol_acumulada': self._safe_ratio(row['produccion_acum'], row['plantas_acum']),
            })

        registros_serializados = RegistroProduccionSerializer(filtered_qs, many=True).data

        # Stock ABC: suma del último día con actividad (todos los equipos de la UN)
        stock_abc_total = all_filtered_qs.filter(fecha=cutoff_date).aggregate(
            total=Sum('stock_abc')
        ).get('total') or 0.0
        stock_abc_total = round(float(stock_abc_total), 2)

        return Response({
            'periodo': {
                'month': month_int,
                'year': year_int,
                'day_param': int(day) if day else None,
                'start_date': start_date.isoformat(),
                'end_date': month_end.isoformat(),
                'cutoff_date': cutoff_date.isoformat(),
            },
            'unidad_negocio': cod_un_id,
            'unidad_produccion': unidad_produccion or '',
            'produccion_esperada_acumulada': produccion_esperada_acumulada,
            'produccion_esperada_por_dia': produccion_esperada_por_dia,
            'stock_abc_total': stock_abc_total,
            'registros': registros_serializados,
            'tabla_consumo': tabla_consumo,
            'tabla_produccion': tabla_produccion,
        })
        
        
class ResumenOperacionalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        un = request.GET.get('un')
        fecha = request.GET.get('fecha')  # Filtro opcional: un día específico

        # Validar que se envíen start_date y end_date
        if not start_date or not end_date:
            return Response(
                {"error": "Los parámetros 'start_date' y 'end_date' son requeridos."},
                status=400
            )

        # --- 1. ACUMULADO DEL MES (rango completo, sin importar 'fecha') ---
        filtro_mes = Q(fecha__gte=start_date, fecha__lte=end_date)
        if un:
            filtro_mes &= Q(cod_un=un)

        registros_mes = RegistroProduccion.objects.filter(filtro_mes).select_related('cod_equipo')

        datos_mes = {}
        for r in registros_mes:
            maquina = r.cod_equipo.detalle if r.cod_equipo else "Sin máquina"
            if maquina not in datos_mes:
                datos_mes[maquina] = {
                    'maquina': maquina,
                    'horas': 0,
                    'arboles': 0,
                    'm3': 0,
                    'toneladas': 0,
                    'viajes': 0,
                    'combustible': 0,
                    'lubricante': 0
                }

            # Calcular horas trabajadas
            horas_inicio = r.hr_inicio or 0
            horas_fin = r.hr_fin or 0
            horas_trabajadas = max(0, horas_fin - horas_inicio)

            # Acumular valores
            datos_mes[maquina]['horas'] += horas_trabajadas
            datos_mes[maquina]['arboles'] += r.plantas or 0
            datos_mes[maquina]['m3'] += r.m3 or 0
            datos_mes[maquina]['toneladas'] += r.tn_despachadas or 0

            # Viajes: solo si es EXTRACCIÓN y UN = COSECHA CTL
            if r.operacion == 'EXTRACCION' and r.UN == 'COSECHA CTL':
                datos_mes[maquina]['viajes'] += r.produccion or 0

            datos_mes[maquina]['combustible'] += r.combustible or 0
            datos_mes[maquina]['lubricante'] += r.aceite_cadena or 0

        # --- 2. DATOS DEL DÍA (solo si se envía `fecha`) ---
        if fecha:
            filtro_dia = Q(fecha=fecha)
            if un:
                filtro_dia &= Q(cod_un=un)
            registros_dia = RegistroProduccion.objects.filter(filtro_dia).select_related('cod_equipo')
        else:
            registros_dia = []

        datos_dia = {}
        for r in registros_dia:
            maquina = r.cod_equipo.detalle if r.cod_equipo else "Sin máquina"
            if maquina not in datos_dia:
                datos_dia[maquina] = {
                    'maquina': maquina,
                    'horas': 0,
                    'arboles': 0,
                    'm3': 0,
                    'toneladas': 0,
                    'viajes': 0,
                    'combustible': 0,
                    'lubricante': 0
                }

            horas_inicio = r.hr_inicio or 0
            horas_fin = r.hr_fin or 0
            horas_trabajadas = max(0, horas_fin - horas_inicio)

            datos_dia[maquina]['horas'] += horas_trabajadas
            datos_dia[maquina]['arboles'] += r.plantas or 0
            datos_dia[maquina]['m3'] += r.m3 or 0
            datos_dia[maquina]['toneladas'] += r.tn_despachadas or 0

            if r.operacion == 'EXTRACCION' and r.UN == 'COSECHA CTL':
                datos_dia[maquina]['viajes'] += r.produccion or 0

            datos_dia[maquina]['combustible'] += r.combustible or 0
            datos_dia[maquina]['lubricante'] += r.aceite_cadena or 0

        return Response({
            "diario": list(datos_dia.values()) if fecha else [],
            "acumulado_mes": list(datos_mes.values())
        })
        

class FiltrosCombustibleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            return Response({"unidades": []})

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"unidades": []}, status=400)

        # Obtener IDs de UN y Lugares de Carga únicas en el rango
        cargas_qs = CargaCombustible.objects.filter(
            fecha__range=[start_date, end_date]
        )

        unidad_ids = cargas_qs.values_list('unidad_negocio', flat=True).distinct()
        lugar_ids = cargas_qs.values_list('lugar_carga', flat=True).distinct()

        unidades = UnidadNegocio.objects.filter(
            id__in=[i for i in unidad_ids if i]
        ).order_by('nombre')

        unidades_data = [{"id": u.id, "nombre": u.nombre} for u in unidades]

        # Obtener lugares de carga disponibles en el rango
        from .models import LugarCarga
        lugares = LugarCarga.objects.filter(id__in=[i for i in lugar_ids if i]).order_by('detalle')
        lugares_data = [{"id": l.id, "detalle": l.detalle} for l in lugares]

        return Response({"unidades": unidades_data, "lugares": lugares_data})
    
class EquiposPorUNView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        un_id = request.GET.get('un_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not un_id:
            return Response({"equipos": []})

        # Validar fechas
        if not start_date or not end_date:
            return Response({"equipos": []}, status=400)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"equipos": []}, status=400)

        # Obtener IDs de moviles (equipos) que tuvieron cargas en esa UN y rango de fechas
        movil_ids = CargaCombustible.objects.filter(
            unidad_negocio=un_id,
            fecha__range=[start_date, end_date]
        ).values_list('equipo', flat=True).distinct()

        # Obtener los equipos (Movil) con esos IDs
        equipos = Equipo.objects.filter(
            id__in=list(movil_ids)
        ).order_by('detalle')

        # Serializar
        data = [
            {
                "id": m.id,
                "detalle": m.detalle,
                "patente": m.patente
            }
            for m in equipos
        ]

        return Response({"equipos": data})
        
    
class CargasCombustibleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        un_id = request.GET.get('un_id')
        movil_id = request.GET.get('movil_id')
        # Nuevo parámetro: lugar de carga (id)
        lugar_id = request.GET.get('lugar_id')

        if not start_date or not end_date:
            return Response({"error": "start_date y end_date son requeridos"}, status=400)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Usa YYYY-MM-DD."}, status=400)

        # Filtrar cargas en el rango de fechas
        query = CargaCombustible.objects.filter(fecha__range=[start_date, end_date])

        if un_id:
            query = query.filter(unidad_negocio_id=un_id)
        if movil_id:
            query = query.filter(equipo_id=movil_id)
        if lugar_id:
            query = query.filter(lugar_carga_id=lugar_id)

        # Prefetch o select_related para optimizar consultas
        query = query.select_related('equipo', 'unidad_negocio', 'lugar_carga')

        # Calcular totales por tipo_mov
        totales = query.values('tipo_mov').annotate(total_litros=Sum('litros')).order_by('tipo_mov')
        totales_dict = {}
        for item in totales:
            tipo = 'Ingreso' if item['tipo_mov'] == 'I' else 'Egreso'
            totales_dict[tipo] = float(item['total_litros'])

        # Serializar datos detallados
        serializer = CargaCombustibleSerializer(query, many=True)

        # Respuesta final
        return Response({
            "results": serializer.data,
            "totales": {
                "Ingreso": totales_dict.get("Ingreso", 0.0),
                "Egreso": totales_dict.get("Egreso", 0.0)
            }
        }, status=status.HTTP_200_OK)
        

# Lista de feriados (puedes moverlo a un modelo o settings si crece)
FERIADOS = {
    # Agrega más según tu calendario
}

def es_dia_laborable(current_date):
    """
    Determina si una fecha es laborable:
    - Lunes a Viernes → 1.0
    - Sábado → 0.5
    - Domingo → 0.0
    - Feriados → 1.0 (incluso si caen domingo)
    """
    fecha_str = current_date.isoformat()
    if fecha_str in FERIADOS:
        return True
    if current_date.weekday() in [5, 6]:  # sabado y domingo
        return False
    return True


def calcular_jornadas_en_rango(start_date, end_date):
    """
    Devuelve una lista de tuplas: (fecha, jornada)
    jornada: 1.0 (completo), 0.5 (medio), 0.0 (no laborable)
    """
    current = start_date
    jornadas = []

    while current <= end_date:
        if es_dia_laborable(current):
            jornada = 0.5 if current.weekday() == 5 else 1.0  # sábado = 0.5
        else:
            jornada = 0.0
        jornadas.append((current.isoformat(), jornada))
        current += timedelta(days=1)

    return jornadas


class ProduccionDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # =======================
        # 1. Obtener parámetros
        # =======================
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        cod_un = request.GET.get('cod_un')  # Puede ser múltiple: "1,2,3"
        operacion = request.GET.get('operacion')  # Puede ser múltiple: "VOLTEO,EXTRACCION"
        detalle_equipo = request.GET.get('detalle_equipo')
        operador = request.GET.get('operador')
        acta = request.GET.get('acta')

        if not start_date_str or not end_date_str:
            return Response(
                {"error": "Las fechas 'start_date' y 'end_date' son obligatorias."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Las fechas deben estar en formato 'YYYY-MM-DD'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:
            return Response(
                {"error": "'start_date' no puede ser posterior a 'end_date'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar y convertir cod_un múltiples a enteros si existen
        cod_un_ids = []
        if cod_un:
            try:
                cod_un_ids = [int(x.strip()) for x in cod_un.split(',') if x.strip()]
                # Validar que todas las unidades existan
                existing_ids = set(UnidadNegocio.objects.filter(id__in=cod_un_ids).values_list('id', flat=True))
                invalid_ids = set(cod_un_ids) - existing_ids
                if invalid_ids:
                    return Response(
                        {"error": f"Las siguientes unidades de negocio no existen: {list(invalid_ids)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {"error": "Los parámetros 'cod_un' deben ser números válidos separados por comas."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar operaciones múltiples
        operaciones_list = []
        if operacion:
            operaciones_list = [x.strip() for x in operacion.split(',') if x.strip()]

        # =======================
        # 2. Filtrar registros de producción
        # =======================
        filtro = Q()
        filtro &= Q(fecha__gte=start_date) & Q(fecha__lte=end_date)

        if cod_un_ids:
            filtro &= Q(cod_un_id__in=cod_un_ids)
        if operaciones_list:
            filtro &= Q(operacion__in=operaciones_list)
        if detalle_equipo:
            filtro &= Q(cod_equipo__detalle=detalle_equipo)
        if operador:
            try:
                operador_id = int(operador)
                if operador_id <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return Response(
                    {"error": "El parámetro 'operador' debe ser un ID entero positivo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            filtro &= Q(cod_operador_id=operador_id)
        if acta:
            filtro &= Q(acta=acta)

        # Ordenar por fecha y hora de fin para evitar resultados inconsistentes
        registros = (
            RegistroProduccion.objects.filter(filtro)
            .select_related('cod_equipo', 'cod_un', 'origen_camion')
            .prefetch_related('cod_operador')
            .order_by('-fecha', '-hr_fin')
        )

        # Dataset completo para gráficos (sin paginar). Orden ascendente para series temporales.
        registros_grafico_qs = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo', 'cod_un').order_by('fecha', 'hr_fin')
        # Loguear la consulta SQL para diagnóstico
        try:
            logger.info("ProduccionDashboardView - filtros: start_date=%s end_date=%s cod_un=%s operacion=%s operador=%s acta=%s",
                        start_date_str, end_date_str, cod_un, operacion, operador, acta)
            logger.debug("SQL registros (paginated): %s", str(registros.query))
            logger.debug("SQL registros_grafico: %s", str(registros_grafico_qs.query))
        except Exception as e:
            logger.exception("Error al obtener SQL del queryset: %s", e)
        registros_grafico = RegistroProduccionDiarioSerializer(registros_grafico_qs, many=True).data
        # =======================
        # 3. Calcular producción esperada acumulada
        # =======================
        periodo = end_date.strftime('%Y%m')
        # Calcular cantidad de días laborables (lunes a viernes) en el mes de end_date
        dias_del_mes = sum(
            1 for d in range(1, calendar.monthrange(end_date.year, end_date.month)[1] + 1)
            if date(end_date.year, end_date.month, d).weekday() < 5
        )
        # proporcion = (end_date - start_date).days + 1 / dias_del_mes  # días del rango / días del mes
        # Calcular cantidad de días hábiles (lunes a viernes) en el rango seleccionado
        dias_habiles_rango = sum(
            1 for d in range((end_date - start_date).days + 1)
            if (start_date + timedelta(days=d)).weekday() < 5
        )
        proporcion = dias_habiles_rango / dias_del_mes if dias_del_mes > 0 else 0

        queryset_mensual = ProduccionMensual.objects.filter(periodo=periodo)
        if operaciones_list:
            # Para múltiples operaciones, filtrar por cualquiera de ellas
            queryset_mensual = queryset_mensual.filter(tipo_operacion__in=operaciones_list)
        if cod_un_ids:
            # Para múltiples unidades, filtrar por cualquiera de ellas
            queryset_mensual = queryset_mensual.filter(unidad_negocio_id__in=cod_un_ids)
        
        if detalle_equipo:
            queryset_mensual = queryset_mensual.filter(equipo__detalle=detalle_equipo)
            
        # Obtener la unidad_produccion (asumiendo que todos los registros coinciden)
        unidad_produccion = queryset_mensual.values_list('unidad_produccion', flat=True).distinct().first()
        
        agregado = queryset_mensual.aggregate(
            meta_mensual=Sum('produccion'),
            total_equipos=Sum('cantidad_equipo')
        )

        meta_mensual = float(agregado['meta_mensual'] or 0.0)
        if operador:
            meta_mensual = meta_mensual / agregado['total_equipos'] if agregado['total_equipos'] else 0.0
        produccion_esperada_acumulada = round(meta_mensual * proporcion, 2)

        # =======================
        # 4. Calcular producción esperada por día
        # =======================
        jornadas = calcular_jornadas_en_rango(start_date, end_date)
        total_jornadas = sum(jornada for _, jornada in jornadas)

        if total_jornadas == 0:
            produccion_esperada_por_dia = {item[0]: 0.0 for item in jornadas}
        else:
            produccion_diaria_base = produccion_esperada_acumulada / total_jornadas
            produccion_esperada_por_dia = {
                fecha: round(jornada * produccion_diaria_base, 2)
                for fecha, jornada in jornadas
            }

        # =======================
        # 5. Calcular consumo real de combustible desde CargaCombustible
        # =======================
        consumo_por_dia = {}
        total_consumo = 0.0

        try:
            cargas_qs = CargaCombustible.objects.filter(
                fecha__gte=start_date,
                fecha__lte=end_date,
                tipo_mov='E'  # Solo egresos (cargas de combustible)
            )

            # Aplicar filtros
            if detalle_equipo:
                cargas_qs = cargas_qs.filter(equipo__detalle=detalle_equipo)
            
            if cod_un_ids:
                cargas_qs = cargas_qs.filter(unidad_negocio_id__in=cod_un_ids)

            # Agrupar por fecha
            consumos_data = cargas_qs.values('fecha').annotate(total_litros=Sum('litros'))
            consumo_por_dia = {
                item['fecha'].isoformat(): round(float(item['total_litros']), 2)
                for item in consumos_data
            }
            total_consumo = sum(consumo_por_dia.values())
        except Exception as e:
            print(f"Error al calcular consumo de combustible: {e}")
            consumo_por_dia = {}
            total_consumo = 0.0

        # =======================
        # 6. Filtros dinámicos
        # =======================
        registros_filtro = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo', 'cod_operador', 'origen_camion')

        operaciones = list(registros_filtro.values_list('operacion', flat=True).distinct().order_by('operacion'))
        unidades = list(registros_filtro.values_list('cod_un__nombre', flat=True).distinct().order_by('cod_un__nombre'))
        equipos = list(registros_filtro.values_list('cod_equipo__detalle', flat=True).distinct().order_by('cod_equipo__detalle'))
        operadores_qs = (
            registros_filtro.values('cod_operador_id', 'cod_operador__nombre')
            .distinct()
            .order_by('cod_operador__nombre', 'cod_operador_id')
        )
        operadores = [
            {'id': item['cod_operador_id'], 'nombre': item['cod_operador__nombre']}
            for item in operadores_qs
            if item['cod_operador_id'] and item['cod_operador__nombre']
        ]
        actas = list(registros_filtro.values_list('acta', flat=True).distinct().order_by('acta'))

        # =======================
        # 7. Respuesta final (con paginación)
        # =======================
        paginator = StandarPagination()
        page = paginator.paginate_queryset(registros, request)

        if page is not None:
            serializer = RegistroProduccionSerializer(page, many=True)
            paginated_response = paginator.get_paginated_response(serializer.data)
            # Log info sobre los datos paginados devueltos (cantidad y fechas ejemplo)
            try:
                results = serializer.data
                count = paginated_response.data.get('count', None)
                sample_ids = [r.get('id') for r in results[:5]]
                sample_fechas = [r.get('fecha') for r in results[:5]]
                logger.info("ProduccionDashboardView - paginated response count=%s sample_ids=%s sample_fechas=%s",
                            count, sample_ids, sample_fechas)
            except Exception:
                logger.exception("Error al loggear la respuesta paginada")
            # añadir campos adicionales a la respuesta paginada
            extra = {
                "produccion_esperada_acumulada": produccion_esperada_acumulada,
                "produccion_esperada_por_dia": produccion_esperada_por_dia,
                "unidad_produccion": unidad_produccion,
                "consumo_combustible_total": round(total_consumo, 2),
                "consumo_combustible_por_dia": consumo_por_dia,
                "registros_grafico": registros_grafico,
                "filtros": {
                    "operaciones": [op for op in operaciones if op],
                    "unidades": [u for u in unidades if u],
                    "equipos": [e for e in equipos if e],
                    "operadores": operadores,
                    "actas": [a for a in actas if a],
                }
            }
            # paginated_response.data es un diccionario con keys count, next, previous, results
            paginated_response.data.update(extra)
            return paginated_response

        # si no hay paginación (devuelve todo)
        serializer = RegistroProduccionSerializer(registros, many=True)
        results = serializer.data
        try:
            sample_ids_all = [r.get('id') for r in results[:5]]
            sample_fechas_all = [r.get('fecha') for r in results[:5]]
            logger.info("ProduccionDashboardView - full response results_len=%s sample_ids=%s sample_fechas=%s",
                        len(results), sample_ids_all, sample_fechas_all)
        except Exception:
            logger.exception("Error al loggear la respuesta completa")
        return Response({
            "results": results,
            "registros_grafico": registros_grafico,
            "produccion_esperada_acumulada": produccion_esperada_acumulada,
            "produccion_esperada_por_dia": produccion_esperada_por_dia,
            "unidad_produccion": unidad_produccion,
            "consumo_combustible_total": round(total_consumo, 2),
            "consumo_combustible_por_dia": consumo_por_dia,
            "filtros": {
                "operaciones": [op for op in operaciones if op],
                "unidades": [u for u in unidades if u],
                "equipos": [e for e in equipos if e],
                "operadores": operadores,
                "actas": [a for a in actas if a],
            }
        }, status=status.HTTP_200_OK)

class HorasNoOperativasDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        cod_un_id = request.query_params.get('un', None)
        fecha_inicio_str = request.query_params.get('fecha_inicio', None)
        fecha_fin_str = request.query_params.get('fecha_fin', None)

        fecha_inicio = parse_date(fecha_inicio_str) if fecha_inicio_str else None
        fecha_fin = parse_date(fecha_fin_str) if fecha_fin_str else None

        if not fecha_inicio or not fecha_fin:
            return Response({
                "error": "Debe proporcionar fecha_inicio y fecha_fin."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filtrar registros
        registros = RegistroProduccion.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).exclude(motivo_no_op__exact='').filter(motivo_no_op__isnull=False)

        registros = registros.filter(hrs_no_operativas__gt=0)
        if cod_un_id:
            registros = registros.filter(cod_un_id=cod_un_id)
        # Filtrar por equipo (movil_id) si se provee desde el frontend
        movil_id = request.query_params.get('movil_id', None)
        if movil_id:
            try:
                movil_id_int = int(movil_id)
                registros = registros.filter(cod_equipo_id=movil_id_int)
            except (ValueError, TypeError):
                pass

        # === DATOS PARA EL GRÁFICO (agrupado por motivo) ===
        registros_annotated = registros.annotate(motivo_limpio=Trim(F('motivo_no_op')))
        datos_agrupados = (
            registros_annotated
            .values('motivo_limpio')
            .annotate(total_hrs_no_op=Sum('hrs_no_operativas'))
            .order_by('-total_hrs_no_op')
        )

        results_grafico = [
            {
                "motivo": item['motivo_limpio'],
                "total_hrs_no_op": float(item['total_hrs_no_op'])
            }
            for item in datos_agrupados
        ]

        # === DATOS PARA LA TABLA (registros crudos) ===
        datos_tabla = []
        for reg in registros.select_related('cod_un', 'cod_equipo'):  # optimiza con select_related
            datos_tabla.append({
                "un": reg.cod_un.nombre if reg.cod_un else reg.UN,  # Usa nombre de UnidadNegocio si existe, sino campo UN
                "fecha": reg.fecha.isoformat() if reg.fecha else None,
                "equipo": reg.cod_equipo.detalle if getattr(reg, 'cod_equipo', None) else (getattr(reg, 'equipo', None) or '-'),
                "equipo_patente": reg.cod_equipo.patente if getattr(reg, 'cod_equipo', None) else None,
                "hrs_no_operativas": float(reg.hrs_no_operativas),
                "motivo": reg.motivo_no_op.strip(),
                "observaciones": reg.observaciones or '-'
            })

        # === UNIDADES DISPONIBLES ===
        unidades_ids = registros.values_list('cod_un_id', flat=True).distinct()
        unidades = UnidadNegocio.objects.filter(id__in=unidades_ids).values('id', 'nombre')
        unidades_disponibles = [{"id": u['id'], "nombre": u['nombre']} for u in unidades]

        return Response({
            "results_grafico": results_grafico,
            "datos_tabla": datos_tabla,
            "unidades_disponibles": unidades_disponibles,
            "total_registros": len(datos_tabla)
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
def maquinas_por_frente_operador(request):
    fecha_inicio_str = request.query_params.get('fecha_inicio')
    fecha_fin_str = request.query_params.get('fecha_fin')
    cod_un_id = request.query_params.get('cod_un')  # Filtro opcional por frente

    if not fecha_inicio_str or not fecha_fin_str:
        return JsonResponse(
            {'error': 'Se requieren fecha_inicio y fecha_fin (formato: YYYY-MM-DD)'},
            status=400
        )

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido. Usa YYYY-MM-DD.'}, status=400)

    # Validar cod_un si se envía
    if cod_un_id:
        try:
            cod_un_id = int(cod_un_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'cod_un debe ser un número válido.'}, status=400)

    # Construir filtro
    filtro = Q(fecha__range=[fecha_inicio, fecha_fin])
    if cod_un_id:
        filtro &= Q(cod_un__id=cod_un_id)

    # Obtener registros ordenados por fecha y hr_fin (descendente)
    registros = RegistroProduccion.objects.filter(filtro).select_related(
        'cod_equipo', 'cod_un'
    ).prefetch_related('cod_operador').only(
        'cod_equipo__id', 'cod_equipo__patente', 'cod_equipo__detalle',
        'cod_un__nombre', 'cod_operador_id', 'cod_operador__nombre', 'operador', 'fecha', 'hr_fin'
    ).order_by('-fecha', '-hr_fin')  # Primero los más recientes

    # Eliminar duplicados: guardar solo el más reciente por (equipo, frente, operador)
    vistos = set()
    resultado = []

    for reg in registros:
        try:
            operador_nombre = reg.cod_operador.nombre
        except Empleado.DoesNotExist:
            operador_nombre = None
        key = (reg.cod_equipo.id, reg.cod_un.nombre if reg.cod_un else None, reg.cod_operador_id)
        if key not in vistos:
            vistos.add(key)
            resultado.append({
                'cod_equipo': reg.cod_equipo.patente,         # Patente como ID
                'detalle_equipo': reg.cod_equipo.detalle,    # Detalle del equipo (ej: "Excavadora 20T")
                'frente': reg.cod_un.nombre if reg.cod_un else None,
                'operador_id': reg.cod_operador_id,
                'operador': operador_nombre,
                'operador_texto_legacy': reg.operador,
                'ultima_fecha': reg.fecha,
                'ultima_hr_fin': float(reg.hr_fin) if reg.hr_fin else None  # Decimal a float
            })

    return JsonResponse({'data': resultado}, safe=False)

@api_view(['GET'])
def resumen_maquinas_componentes(request):
    """
    Vista que genera una tabla con resumen de máquinas y componentes
    
    Para cada máquina muestra:
    - Unidad de negocio (cod_un)
    - Cantidad de cadenas utilizadas
    - Última hora registrada (hr_fin)
    - Cantidad de horas trabajadas (hr_fin - hr_inicio)
    - Total de m³ producidos en el rango de fechas
    - Rendimiento por cadena (m³/cadena)
    - m³ desde el último cambio de espada, puntera y piñón
    - Total de aceite de cadena utilizado
    - Última hora registrada para cambio de espada, puntera, piñón y giro piñón
    
    Parámetros:
    - fecha_inicio: fecha de inicio del rango (YYYY-MM-DD)
    - fecha_fin: fecha fin del rango (YYYY-MM-DD)
    
    Solo muestra equipos que tuvieron novedades en el rango de fechas
    """
    fecha_inicio_str = request.query_params.get('fecha_inicio')
    fecha_fin_str = request.query_params.get('fecha_fin')
    cod_un = request.query_params.get('cod_un')  # Puede ser múltiple: "1,2,3"
    operacion = request.query_params.get('operacion')  # Puede ser múltiple: "VOLTEO,EXTRACCION"
    
    if not fecha_inicio_str or not fecha_fin_str:
        return JsonResponse(
            {'error': 'Se requieren fecha_inicio y fecha_fin (formato: YYYY-MM-DD)'},
            status=400
        )
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido. Usa YYYY-MM-DD.'}, status=400)
    
    # Filtrar registros en el rango de fechas
    filtro = Q(fecha__range=[fecha_inicio, fecha_fin])
    
    # Manejo de múltiples unidades de negocio
    if cod_un:
        try:
            # Dividir por comas y convertir a enteros
            cod_un_ids = [int(x.strip()) for x in cod_un.split(',') if x.strip()]
            if cod_un_ids:
                filtro &= Q(cod_un_id__in=cod_un_ids)
        except (ValueError, TypeError):
            pass  # Ignorar si no son números válidos
    
    # Manejo de múltiples operaciones
    if operacion:
        operaciones = [x.strip() for x in operacion.split(',') if x.strip()]
        if operaciones:
            filtro &= Q(operacion__in=operaciones)
    
    registros = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo', 'cod_un').order_by('cod_equipo', '-fecha', '-hr_fin')
    
    # Filtrar solo registros que tengan cambios de componentes
    registros_con_cambios = registros.filter(
        Q(espada=True) | Q(puntera=True) | Q(pinon=True) | Q(giro_pinon=True)
    )
    
    if not registros_con_cambios.exists():
        return JsonResponse({'data': []}, safe=False)
    
    # Obtener todos los registros de las máquinas que tuvieron cambios (para calcular totales)
    equipos_con_cambios = set(r.cod_equipo.id for r in registros_con_cambios if r.cod_equipo)
    todos_registros = registros.filter(cod_equipo__id__in=equipos_con_cambios)
    
    # Procesar datos por máquina
    datos_maquinas = {}
    
    # Primero procesamos todos los registros para obtener totales
    for registro in todos_registros:
        equipo_id = registro.cod_equipo.id if registro.cod_equipo else 'sin_equipo'
        
        if equipo_id not in datos_maquinas:
            datos_maquinas[equipo_id] = {
                'maquina': registro.cod_equipo.detalle if registro.cod_equipo else 'Sin equipo',
                'patente': registro.cod_equipo.patente if registro.cod_equipo else 'Sin patente',
                'unidad_negocio': registro.cod_un.nombre if registro.cod_un else 'Sin UN',
                'cod_un': registro.cod_un.id if registro.cod_un else None,
                'cantidad_cadenas_total': 0,
                'ultima_hr_registrada': None,
                'total_horas_trabajadas': 0,
                'total_m3': 0,
                'total_aceite_cadena': 0,
                'ultima_hr_cambio_espada': None,
                'ultima_hr_cambio_puntera': None,
                'ultima_hr_cambio_pinon': None,
                'ultima_hr_cambio_giro_pinon': None,
                'm3_desde_ultimo_cambio_espada': 0,
                'm3_desde_ultimo_cambio_puntera': 0,
                'm3_desde_ultimo_cambio_pinon': 0,
                'registros_procesados': []
            }
        
        maquina_data = datos_maquinas[equipo_id]
        
        # Calcular horas trabajadas para este registro
        horas_inicio = float(registro.hr_inicio or 0)
        horas_fin = float(registro.hr_fin or 0)
        horas_trabajadas = max(0, horas_fin - horas_inicio)
        
        # Acumular valores generales
        maquina_data['cantidad_cadenas_total'] += registro.cantidad_cadenas or 0
        maquina_data['total_m3'] += registro.m3 or 0
        maquina_data['total_aceite_cadena'] += float(registro.aceite_cadena or 0)
        
        # Actualizar última hora registrada (tomar la más reciente)
        if maquina_data['ultima_hr_registrada'] is None or horas_fin > maquina_data['ultima_hr_registrada']:
            maquina_data['ultima_hr_registrada'] = horas_fin
        
        # Acumular horas trabajadas
        maquina_data['total_horas_trabajadas'] += horas_trabajadas
    
    # Ahora procesamos los registros con cambios para obtener las últimas horas de cambio
    for registro in registros_con_cambios:
        equipo_id = registro.cod_equipo.id if registro.cod_equipo else 'sin_equipo'
        maquina_data = datos_maquinas[equipo_id]
        
        horas_fin = float(registro.hr_fin or 0)
        
        # Verificar cambios de componentes y actualizar última hora
        if registro.espada and (maquina_data['ultima_hr_cambio_espada'] is None or horas_fin > maquina_data['ultima_hr_cambio_espada']):
            maquina_data['ultima_hr_cambio_espada'] = horas_fin
            
        if registro.puntera and (maquina_data['ultima_hr_cambio_puntera'] is None or horas_fin > maquina_data['ultima_hr_cambio_puntera']):
            maquina_data['ultima_hr_cambio_puntera'] = horas_fin
            
        if registro.pinon and (maquina_data['ultima_hr_cambio_pinon'] is None or horas_fin > maquina_data['ultima_hr_cambio_pinon']):
            maquina_data['ultima_hr_cambio_pinon'] = horas_fin
            
        if registro.giro_pinon and (maquina_data['ultima_hr_cambio_giro_pinon'] is None or horas_fin > maquina_data['ultima_hr_cambio_giro_pinon']):
            maquina_data['ultima_hr_cambio_giro_pinon'] = horas_fin
    
    # Calcular m³ desde el último cambio de cada componente
    for equipo_id, maquina_data in datos_maquinas.items():
        # Para calcular m³ desde el último cambio, necesitamos filtrar registros posteriores al cambio
        if maquina_data['ultima_hr_cambio_espada']:
            m3_desde_espada = todos_registros.filter(
                cod_equipo__id=equipo_id,
                hr_fin__gte=maquina_data['ultima_hr_cambio_espada']
            ).aggregate(total=Sum('m3'))['total'] or 0
            maquina_data['m3_desde_ultimo_cambio_espada'] = m3_desde_espada
            
        if maquina_data['ultima_hr_cambio_puntera']:
            m3_desde_puntera = todos_registros.filter(
                cod_equipo__id=equipo_id,
                hr_fin__gte=maquina_data['ultima_hr_cambio_puntera']
            ).aggregate(total=Sum('m3'))['total'] or 0
            maquina_data['m3_desde_ultimo_cambio_puntera'] = m3_desde_puntera
            
        if maquina_data['ultima_hr_cambio_pinon']:
            m3_desde_pinon = todos_registros.filter(
                cod_equipo__id=equipo_id,
                hr_fin__gte=maquina_data['ultima_hr_cambio_pinon']
            ).aggregate(total=Sum('m3'))['total'] or 0
            maquina_data['m3_desde_ultimo_cambio_pinon'] = m3_desde_pinon
    
    # Preparar resultado final
    resultado = []
    for maquina_data in datos_maquinas.values():
        # Calcular rendimiento por cadena
        rendimiento_por_cadena = 0
        if maquina_data['cantidad_cadenas_total'] > 0:
            rendimiento_por_cadena = round(maquina_data['total_m3'] / maquina_data['cantidad_cadenas_total'], 2)
        
        resultado.append({
            'maquina': maquina_data['maquina'],
            'patente': maquina_data['patente'],
            'unidad_negocio': maquina_data['unidad_negocio'],
            'cod_un': maquina_data['cod_un'],
            'cantidad_cadenas_utilizadas': maquina_data['cantidad_cadenas_total'],
            'ultima_hr_registrada': round(maquina_data['ultima_hr_registrada'], 2) if maquina_data['ultima_hr_registrada'] else 0,
            'total_horas_trabajadas': round(maquina_data['total_horas_trabajadas'], 2),
            'total_m3': maquina_data['total_m3'],
            'rendimiento_por_cadena': rendimiento_por_cadena,
            'total_aceite_cadena': round(maquina_data['total_aceite_cadena'], 2),
            'm3_desde_ultimo_cambio_espada': maquina_data['m3_desde_ultimo_cambio_espada'],
            'm3_desde_ultimo_cambio_puntera': maquina_data['m3_desde_ultimo_cambio_puntera'],
            'm3_desde_ultimo_cambio_pinon': maquina_data['m3_desde_ultimo_cambio_pinon'],
            'ultima_hr_cambio_espada': round(maquina_data['ultima_hr_cambio_espada'], 2) if maquina_data['ultima_hr_cambio_espada'] else None,
            'ultima_hr_cambio_puntera': round(maquina_data['ultima_hr_cambio_puntera'], 2) if maquina_data['ultima_hr_cambio_puntera'] else None,
            'ultima_hr_cambio_pinon': round(maquina_data['ultima_hr_cambio_pinon'], 2) if maquina_data['ultima_hr_cambio_pinon'] else None,
            'ultima_hr_cambio_giro_pinon': round(maquina_data['ultima_hr_cambio_giro_pinon'], 2) if maquina_data['ultima_hr_cambio_giro_pinon'] else None
        })
    
    # Ordenar por máquina
    resultado.sort(key=lambda x: x['maquina'])
    
    # Calcular totales generales
    total_m3 = sum(item['total_m3'] for item in resultado)
    total_aceite = sum(item['total_aceite_cadena'] for item in resultado)
    total_cadenas = sum(item['cantidad_cadenas_utilizadas'] for item in resultado)
    
    return JsonResponse({
        'data': resultado,
        'total_maquinas': len(resultado),
        'totales': {
            'total_m3': total_m3,
            'total_aceite_cadena': round(total_aceite, 2),
            'total_cadenas': total_cadenas,
            'rendimiento_promedio': round(total_m3 / total_cadenas, 2) if total_cadenas > 0 else 0
        },
        'rango_fechas': {
            'fecha_inicio': fecha_inicio_str,
            'fecha_fin': fecha_fin_str
        }
    }, safe=False)

# === feature/equipo-aliases (2026-07-08) =====================================
class EquiposListSearchView(APIView):
    """`GET /api/equipos/?q=bufalo` — busqueda multi-campo.

    Implementado como APIView (no ModelViewSet) para:
      - Saltarse el bug pre-existente `idUnidadNegocio` (db_column inconsistente
        en SQLite dev) usando `.values()` en vez de cargar instancias.
      - Permitir que el caller filtre `?q=` contra detalle/codigo_fg/patente/
        modelo_normalizado/aliases.
      - Permitir `?limit=N` y `?offset=N` (no usa paginator de DRF).

    Reglas (Oscar 2026-07-08):
      - Regla #1: NO se auto-crean Equipos. Solo se devuelven existentes.
      - Regla #4: si hay N>1 matches, el caller resuelve con su usuario final.
    """
    permission_classes = [AllowAny]   # ajustar con auth JWT en el deploy

    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get('limit', 50)), 200))
            offset = max(0, int(request.query_params.get('offset', 0)))
        except (TypeError, ValueError):
            return Response({'error': 'limit/offset invalid'}, status=400)

        # Cargar todos los equipos con campos selectivos. Catalogo chico
        # (decenas a cientos), por lo que el filtro se hace 100% Python.
        rows = list(Equipo.objects.values(
            'id', 'patente', 'detalle', 'codigo_fg', 'modelo_normalizado',
            'aliases', 'ultima_sync_filtros', 'baja',
        ).order_by('detalle'))

        q = request.query_params.get('q', '').strip()
        if q:
            ql = q.lower()
            def match(row):
                if ql in (row.get('detalle') or '').lower(): return True
                if ql in (row.get('codigo_fg') or '').lower(): return True
                if ql in (row.get('patente') or '').lower(): return True
                if ql in (row.get('modelo_normalizado') or '').lower(): return True
                for alias in (row.get('aliases') or []):
                    if isinstance(alias, str) and ql in alias.lower(): return True
                return False
            filtered = [r for r in rows if match(r)]
        else:
            filtered = rows

        total = len(filtered)
        window = filtered[offset:offset + limit]
        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'count': len(window),
            'results': window,
        })


class EquipoAliasesPatchView(APIView):
    """`PATCH /api/equipos/<patente>/aliases` — suma aliases a un Equipo.

    Body: {"add": ["bufalo", "PONSSE"]} o {"replace": ["PONSSE BUFALO"]}.
    Devuelve el Equipo actualizado.
    """
    permission_classes = [AllowAny]   # ajustar con auth JWT en deploy

    def patch(self, request, patente):
        try:
            row = Equipo.objects.values('id', 'aliases').get(patente=patente)
        except Equipo.DoesNotExist:
            return Response({'error': f'Equipo con patente {patente!r} no existe'}, status=404)

        aliases_actual = list(row.get('aliases') or [])
        add = request.data.get('add', []) if hasattr(request, 'data') else []
        replace = request.data.get('replace')

        if replace is not None:
            nuevos = list(replace) if isinstance(replace, list) else []
        else:
            nuevos = list(aliases_actual)
            for a in (add if isinstance(add, list) else []):
                if isinstance(a, str) and a.strip() and a not in nuevos:
                    nuevos.append(a)

        Equipo.objects.filter(pk=row['id']).update(aliases=nuevos)
        return Response({
            'patente': patente,
            'aliases': nuevos,
            'added': [a for a in nuevos if a not in aliases_actual],
        })
