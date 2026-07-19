from datetime import date, time

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from produccion.models import Equipo, Moneda, UnidadNegocio

from .models import (
    OrdenServicioCabecera,
    OrdenServicioDetalle,
    Repuestos,
    Sector,
    TipoTareas,
    UnidadMedida,
)


@override_settings(OPENCLAW_INGEST_TOKEN='test-openclaw-token')
class OrdenesBotAPITests(TestCase):
    unmanaged_models = (
        UnidadMedida,
        Repuestos,
        TipoTareas,
        Sector,
        OrdenServicioCabecera,
        OrdenServicioDetalle,
    )

    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as editor:
            for model in cls.unmanaged_models:
                editor.create_model(model)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as editor:
            for model in reversed(cls.unmanaged_models):
                editor.delete_model(model)

    def setUp(self):
        self.client = APIClient()
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer test-openclaw-token'}
        self.unidad = UnidadNegocio.objects.create(nombre='Forestal')
        self.moneda = Moneda.objects.create(
            descripcion='Peso', simbolo='$', cambio=1, activo=True
        )
        self.equipo = Equipo.objects.create(
            id=282,
            patente='GRUA -Nº9',
            detalle='Grua JOHN DEERE 200GLC - Nº 1 - ARAUCO',
            unidad_negocio=self.unidad,
        )
        self.tipo_tarea = TipoTareas.objects.create(
            tarea='Reparación',
            cada_cuanto=0,
            anticipacion=0,
            tipo_movil_id=0,
            activo=True,
            descripcion='',
            usuario='test',
        )
        self.sector = Sector.objects.create(
            id=1, descripcion='Taller', activo=True, cantidad_empleados=1
        )

    def crear_orden(self, **overrides):
        defaults = {
            'fecha': date(2026, 7, 16),
            'equipo': self.equipo,
            'descripcion': 'CAMBIO DE MANGUERAS RADIADOR Y DEPOSITO DE AGUA',
            'estado': 'Pendiente',
            'cerrado_por': '',
            'externo': False,
            'proveedor': 0,
            'mecanico': 0,
            'unidad_negocio': self.unidad,
            'usuario': 'test',
            'moneda': self.moneda,
            'cambio': 1,
            'orden_servicio': '',
            'planilla_trabajo': False,
        }
        defaults.update(overrides)
        return OrdenServicioCabecera.objects.create(**defaults)

    def crear_detalle(self, orden, **overrides):
        defaults = {
            'cabecera': orden,
            'tipo_tarea': self.tipo_tarea,
            'repuesto': None,
            'cantidad': 0,
            'precio_unitario': 0,
            'preventivo': False,
            'correctivo': True,
            'realizado': False,
            'km_hora': 0,
            'diferencia': 0,
            'detalle': 'Cambiar manguera',
            'fecha_realizacion': None,
            'mecanico': None,
            'moneda': self.moneda,
            'cambio': 1,
            'observaciones': '',
            'hora_inicio': None,
            'hora_fin': None,
            'horas_extras': None,
            'sector': self.sector,
        }
        defaults.update(overrides)
        return OrdenServicioDetalle.objects.create(**defaults)

    def consultar(self, referencia, **headers):
        return self.client.get(
            reverse('consultar-orden', args=[referencia]),
            **(headers or self.auth),
        )

    def test_consulta_por_id_pendiente(self):
        orden = self.crear_orden(id=2044)

        response = self.consultar(orden.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['encontrada'])
        self.assertEqual(response.data['estado'], 'Pendiente')
        self.assertFalse(response.data['cerrada'])

    def test_consulta_por_id_cerrado(self):
        orden = self.crear_orden(estado='Cerrado', cerrado_por='operador')

        response = self.consultar(orden.id)

        self.assertTrue(response.data['cerrada'])
        self.assertTrue(response.data['evidencia_cierre']['estado_cerrado'])

    def test_consulta_por_orden_servicio(self):
        orden = self.crear_orden(orden_servicio='OS-2026-15')

        response = self.consultar('OS-2026-15')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], orden.id)
        self.assertEqual(response.data['referencia_visible'], 'OS-2026-15')

    def test_numero_vacio_usa_id_como_referencia_visible(self):
        orden = self.crear_orden(id=2044, orden_servicio='')

        response = self.consultar(orden.id)

        self.assertEqual(response.data['numero_orden'], '')
        self.assertEqual(response.data['referencia_visible'], 'OMA 2044')

    def test_orden_inexistente(self):
        response = self.consultar(999999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data, {'encontrada': False, 'referencia': '999999'}
        )

    def test_orden_servicio_duplicada_devuelve_conflicto_y_candidatos(self):
        primera = self.crear_orden(orden_servicio='DUP-1')
        segunda = self.crear_orden(orden_servicio='DUP-1')

        response = self.consultar('DUP-1')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(response.data['encontrada'])
        self.assertCountEqual(
            [item['id'] for item in response.data['candidatos']],
            [primera.id, segunda.id],
        )

    def test_estado_cerrado_normaliza_mayusculas_y_espacios(self):
        for estado_orden in (' cerrado ', 'CERRADO', 'CeRrAdO'):
            orden = self.crear_orden(estado=estado_orden)
            self.assertTrue(self.consultar(orden.id).data['cerrada'])

        pendiente = self.crear_orden(estado=' Pendiente ')
        self.assertFalse(self.consultar(pendiente.id).data['cerrada'])

    def test_detalles_realizados_y_no_realizados_no_cierran_cabecera(self):
        orden = self.crear_orden(estado='Pendiente')
        self.crear_detalle(
            orden,
            realizado=True,
            fecha_realizacion=date(2026, 7, 17),
            hora_inicio=time(8, 0),
            hora_fin=time(9, 0),
        )
        self.crear_detalle(orden, realizado=False, detalle='Tarea pendiente')

        response = self.consultar(orden.id)

        self.assertEqual(len(response.data['detalles']), 2)
        self.assertFalse(response.data['cerrada'])
        self.assertFalse(
            response.data['evidencia_cierre']['todas_las_tareas_realizadas']
        )
        self.assertTrue(
            response.data['evidencia_cierre']['fecha_realizacion_presente']
        )

    def test_autenticacion_ausente_e_invalida(self):
        orden = self.crear_orden()

        ausente = self.client.get(reverse('consultar-orden', args=[orden.id]))
        invalida = self.client.get(
            reverse('consultar-orden', args=[orden.id]),
            HTTP_AUTHORIZATION='Bearer incorrecto',
        )

        self.assertEqual(ausente.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(invalida.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_no_modifica_tablas(self):
        orden = self.crear_orden()
        self.crear_detalle(orden)
        antes = (
            OrdenServicioCabecera.objects.count(),
            OrdenServicioDetalle.objects.count(),
        )

        self.consultar(orden.id)
        self.client.get(
            reverse('buscar-estado-orden'),
            {'equipo_id': self.equipo.id},
            **self.auth,
        )

        despues = (
            OrdenServicioCabecera.objects.count(),
            OrdenServicioDetalle.objects.count(),
        )
        self.assertEqual(despues, antes)

    def test_consulta_por_id_usa_cantidad_acotada_de_queries(self):
        orden = self.crear_orden()
        self.crear_detalle(orden)

        with CaptureQueriesContext(connection) as queries:
            response = self.consultar(orden.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(queries), 2)

    def test_busqueda_devuelve_unica_candidatos_y_sin_coincidencias(self):
        primera = self.crear_orden(
            fecha=date(2026, 7, 16),
            descripcion='Cambio de mangueras radiador',
        )
        url = reverse('buscar-estado-orden')

        unica = self.client.get(
            url,
            {
                'equipo_id': self.equipo.id,
                'fecha_desde': '2026-07-01',
                'descripcion': 'mangueras',
            },
            **self.auth,
        )
        self.assertEqual(unica.data['resultado'], 'coincidencia_unica')
        self.assertEqual(unica.data['orden']['id'], primera.id)

        segunda = self.crear_orden(
            fecha=date(2026, 7, 18),
            descripcion='Revisar mangueras hidráulicas',
        )
        candidatos = self.client.get(
            url,
            {'equipo_id': self.equipo.id, 'descripcion': 'mangueras'},
            **self.auth,
        )
        self.assertEqual(candidatos.data['resultado'], 'candidatos')
        self.assertEqual(
            [item['id'] for item in candidatos.data['candidatos']],
            [segunda.id, primera.id],
        )

        ninguna = self.client.get(
            url, {'descripcion': 'inexistente'}, **self.auth
        )
        self.assertEqual(ninguna.data['resultado'], 'sin_coincidencias')

    def test_busqueda_limita_resultados_y_queries(self):
        for indice in range(4):
            self.crear_orden(descripcion=f'Mangueras {indice}')

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse('buscar-estado-orden'),
                {'descripcion': 'mangueras', 'limite': 2},
                **self.auth,
            )

        self.assertEqual(response.data['cantidad'], 2)
        self.assertTrue(response.data['truncado'])
        self.assertLessEqual(len(queries), 2)
