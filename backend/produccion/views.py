import calendar
from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
import django_filters as df                            # django-filter
from django.contrib.auth import authenticate

from django.db.models import Q
from django.contrib.auth.hashers import check_password as django_check_password

# Create your views here.
from produccion_api.BaseViewSet import BaseAppModelViewSet, DebugSerializerErrorsMixin, StandarPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework import filters
from rest_framework.permissions import AllowAny  # 👈 Recomendado

from .models import CargaCombustible, Empleado, Equipo, ProduccionMensual, RegistroProduccion, UnidadNegocio
from .serializers import CargaCombustibleSerializer, EmpleadoSerializer, LoginSerializer, RegistroProduccionDiarioSerializer, RegistroProduccionSerializer
from django.db.models import Sum, F
from datetime import datetime

class ProduccionOperadorView(APIView):

    def get(self, request):
        operador = request.GET.get('operador')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not operador or not fecha_inicio or not fecha_fin:
            return Response(
                {"error": "Faltan parámetros: operador, fecha_inicio, fecha_fin"},
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

        print(fecha_inicio, fecha_fin)
        registros = RegistroProduccion.objects.filter(
            cod_operador=operador,
            fecha__range=[fecha_inicio, fecha_fin]
        ).order_by('-fecha')

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
            "operador": ultimo_registro.operador,
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
            cod_operador=empleado_id,
            fecha__range=[fecha_inicio, fecha_fin]
        ).order_by('fecha')

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
        

class ProduccionFilter(df.FilterSet):
    start_date = df.DateFilter(field_name="fecha", lookup_expr='gte')
    end_date = df.DateFilter(field_name="fecha", lookup_expr='lte')
    un = df.CharFilter(field_name="UN", lookup_expr='iexact')
    operacion = df.CharFilter(field_name="operacion", lookup_expr='iexact')
    equipo = df.CharFilter(field_name="equipo", lookup_expr='icontains')
    operador = df.CharFilter(field_name="operador", lookup_expr='icontains')
    patente = df.CharFilter(field_name="cod_equipo__patente", lookup_expr='icontains')
    detalle_equipo = df.CharFilter(field_name="cod_equipo__detalle", lookup_expr='icontains')
    acta = df.CharFilter(field_name="acta", lookup_expr='icontains')

    class Meta:
        model = RegistroProduccion
        fields = []

class ProduccionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtros desde query params
        queryset = RegistroProduccion.objects.all().select_related('cod_equipo')

        # Aplicar filtros
        filter_instance = ProduccionFilter(request.GET, queryset=queryset)
        registros = filter_instance.qs

        # Serializar
        serializer = RegistroProduccionSerializer(registros, many=True)

        return Response({
            "count": len(serializer.data),
            "results": serializer.data
        }, status=status.HTTP_200_OK)        

class FiltrosDinamicosView(APIView):
    permission_classes = [IsAuthenticated]

    # FiltrosDinamicosView
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        un = request.GET.get('un')  # Nuevo: filtrar por UN
        acta = request.GET.get('acta')  # Nuevo: filtrar por acta

        filtro = Q()
        if start_date:
            filtro &= Q(fecha__gte=start_date)
        if end_date:
            filtro &= Q(fecha__lte=end_date)
        if un:
            filtro &= Q(UN=un)
        if acta:
            filtro &= Q(acta=acta)

        if not start_date and not end_date:
            return Response({
                "operaciones": [],
                "unidades": [],
                "equipos": [],
                "operadores": [],
                "actas": []
            })

        registros = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo')

        operaciones = list(registros.values_list('operacion', flat=True).distinct().order_by('operacion'))
        unidades = list(registros.values_list('UN', flat=True).distinct().order_by('UN'))
        equipos = list(registros.values_list('cod_equipo__detalle', flat=True).distinct().order_by('cod_equipo__detalle'))
        operadores = list(registros.values_list('operador', flat=True).distinct().order_by('operador'))
        actas = list(registros.values_list('acta', flat=True).distinct().order_by('acta'))
        

        return Response({
            "operaciones": operaciones,
            "unidades": [un_val for un_val in unidades if un_val],
            "equipos": [eq for eq in equipos if eq],
            "operadores": [o for o in operadores if o],
            "actas": [a for a in actas if a]
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
            filtro_mes &= Q(UN=un)

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
                filtro_dia &= Q(UN=un)
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

        # Obtener IDs de UN únicas en el rango
        unidad_ids = CargaCombustible.objects.filter(
            fecha__range=[start_date, end_date]
        ).values_list('unidad_negocio', flat=True).distinct()

        # ✅ CORREGIDO: Filtrar UnidadNegocio por idUnidadNegocio, no por unidad_negocio
        unidades = UnidadNegocio.objects.filter(
            id__in=list(unidad_ids)
        ).order_by('nombre')

        unidades_data = [
            {"id": u.id, "nombre": u.nombre}
            for u in unidades
        ]

        return Response({"unidades": unidades_data})
    
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

        if not start_date or not end_date:
            return Response({"error": "start_date y end_date son requeridos"}, status=400)

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Formato de fecha inválido"}, status=400)

        # Filtrar
        query = CargaCombustible.objects.filter(fecha__range=[start_date, end_date])

        if un_id:
            query = query.filter(unidad_negocio_id=un_id)
        if movil_id:
            query = query.filter(equipo_id=movil_id)

        query = query.select_related(
            'equipo', 'unidad_negocio', 'lugar_carga'
        )

        serializer = CargaCombustibleSerializer(query, many=True)
        return Response({"results": serializer.data})


class ProduccionDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # =======================
        # 1. Obtener parámetros
        # =======================
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        un = request.GET.get('un')
        operacion = request.GET.get('operacion')
        detalle_equipo = request.GET.get('detalle_equipo')
        operador = request.GET.get('operador')
        acta = request.GET.get('acta')

        if not start_date or not end_date:
            return Response(
                {"error": "Las fechas 'start_date' y 'end_date' son obligatorias."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            fecha_corte = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "La fecha debe estar en formato 'YYYY-MM-DD'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # =======================
        # 2. Filtrar registros de producción
        # =======================
        filtro = Q()
        if start_date:
            filtro &= Q(fecha__gte=start_date)
        if end_date:
            filtro &= Q(fecha__lte=end_date)
        if un:
            filtro &= Q(UN=un)
        if operacion:
            filtro &= Q(operacion=operacion)
        if detalle_equipo:
            filtro &= Q(cod_equipo__detalle=detalle_equipo)
        if operador:
            filtro &= Q(operador__icontains=operador)
        if acta:
            filtro &= Q(acta=acta)

        registros = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo')

        # Serializar
        serializer = RegistroProduccionSerializer(registros, many=True)
        results = serializer.data

        # =======================
        # 3. Calcular producción esperada
        # =======================
        periodo = fecha_corte.strftime('%Y%m')
        _, dias_del_mes = calendar.monthrange(fecha_corte.year, fecha_corte.month)
        proporcion = fecha_corte.day / dias_del_mes

        queryset_mensual = ProduccionMensual.objects.filter(periodo=periodo)
        if un:
            queryset_mensual = queryset_mensual.filter(unidad_negocio__nombre=un)  # Ajusta si usas otro campo

        agregado = queryset_mensual.aggregate(
            meta_mensual=Sum('produccion'),
            total_equipos=Sum('cantidad_equipo')
        )

        meta_mensual = float(agregado['meta_mensual'] or 0.0)
        if operador:
            meta_mensual = meta_mensual / agregado['total_equipos'] if agregado['total_equipos'] else 0.0
        produccion_esperada_acumulada = round(meta_mensual * proporcion, 2)

        # =======================
        # 4. Filtros dinámicos (como en FiltrosDinamicosView)
        # =======================
        # Reusamos el mismo filtro base
        registros_filtro = RegistroProduccion.objects.filter(filtro).select_related('cod_equipo')

        if detalle_equipo:
            registros_filtro = registros_filtro.filter(cod_equipo__detalle=detalle_equipo)

        operaciones = list(registros_filtro.values_list('operacion', flat=True).distinct().order_by('operacion'))
        unidades = list(registros_filtro.values_list('UN', flat=True).distinct().order_by('UN'))
        equipos = list(registros_filtro.values_list('cod_equipo__detalle', flat=True).distinct().order_by('cod_equipo__detalle'))
        operadores = list(registros_filtro.values_list('operador', flat=True).distinct().order_by('operador'))
        actas = list(registros_filtro.values_list('acta', flat=True).distinct().order_by('acta'))

        # =======================
        # 5. Respuesta final
        # =======================
        return Response({
            "results": results,
            "produccion_esperada_acumulada": produccion_esperada_acumulada,
            "filtros": {
                "operaciones": operaciones,
                "unidades": [u for u in unidades if u],
                "equipos": [e for e in equipos if e],
                "operadores": [o for o in operadores if o],
                "actas": [a for a in actas if a],
            }
        }, status=status.HTTP_200_OK)    