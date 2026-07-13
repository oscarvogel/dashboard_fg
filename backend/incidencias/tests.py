from datetime import datetime, timezone as dt_timezone

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from produccion.models import Empleado, Equipo

from .models import EventoEstadoEquipo, IncidenciaEquipo, IncidenciaPersonal
from .services import resumen_horas_paradas


TOKEN = "test-openclaw-token"


@override_settings(OPENCLAW_INGEST_TOKEN=TOKEN)
class IncidenciasApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.equipo = Equipo.objects.create(patente="FORWA-5", detalle="Forwarder 5")
        cls.persona = Empleado.objects.create(nombre="Ana Perez", dni="12345678", password="x")

    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {TOKEN}")

    def _crear_equipo(self, source="msg-1", inicio="2026-07-01T08:00:00-03:00"):
        return self.client.post("/api/incidencias/equipos/", {
            "equipo": self.equipo.id,
            "tipo": "averia",
            "descripcion": "No arranca",
            "ubicacion": "Frente Norte",
            "estado_actual": "parado",
            "inicio": inicio,
            "mensaje_origen": "El forwarder no arranca",
            "source_message_id": source,
            "fuente": "whatsapp",
        }, format="json")

    def test_crea_incidencia_y_evento_inmutable_con_id_real(self):
        response = self._crear_equipo()
        self.assertEqual(response.status_code, 201)
        incidencia = IncidenciaEquipo.objects.get()
        evento = EventoEstadoEquipo.objects.get()
        self.assertEqual(incidencia.equipo_id, self.equipo.id)
        self.assertEqual(evento.equipo_id, self.equipo.id)
        self.assertEqual(evento.source_message_id, "msg-1")
        evento.descripcion = "cambio"
        with self.assertRaisesMessage(Exception, "inmutables"):
            evento.save()

    def test_source_message_id_evitar_duplicado(self):
        self.assertEqual(self._crear_equipo().status_code, 201)
        response = self._crear_equipo()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(IncidenciaEquipo.objects.count(), 1)

    def test_agrega_estado_y_cierra_incidencia(self):
        incidencia_id = self._crear_equipo().data["id"]
        evento = self.client.post(f"/api/incidencias/equipos/{incidencia_id}/eventos/", {
            "estado_nuevo": "intermitente",
            "fecha_hora": "2026-07-01T09:00:00-03:00",
            "fuente": "whatsapp",
            "source_message_id": "msg-2",
            "descripcion": "Arranca por momentos",
        }, format="json")
        self.assertEqual(evento.status_code, 201)
        cierre = self.client.post(f"/api/incidencias/equipos/{incidencia_id}/cerrar/", {
            "fecha_hora": "2026-07-01T10:00:00-03:00",
            "source_message_id": "msg-3",
            "mensaje": "Volvio a operar",
            "solucion": "Cambio de bateria",
            "responsable": "Taller",
        }, format="json")
        self.assertEqual(cierre.status_code, 200)
        self.assertFalse(cierre.data["abierta"])
        self.assertEqual(cierre.data["estado_actual"], "operativo")
        self.assertEqual(cierre.data["duracion_minutos"], 120)
        self.assertEqual(EventoEstadoEquipo.objects.count(), 3)

    def test_horas_paradas_no_duplica_incidencias_superpuestas(self):
        primera = self._crear_equipo("super-1", "2026-07-01T08:00:00-03:00").data["id"]
        segunda = self._crear_equipo("super-2", "2026-07-01T09:00:00-03:00").data["id"]
        self.client.post(f"/api/incidencias/equipos/{primera}/cerrar/", {
            "fecha_hora": "2026-07-01T10:00:00-03:00", "source_message_id": "super-3", "mensaje": "Operativo"
        }, format="json")
        self.client.post(f"/api/incidencias/equipos/{segunda}/cerrar/", {
            "fecha_hora": "2026-07-01T11:00:00-03:00", "source_message_id": "super-4", "mensaje": "Confirmado"
        }, format="json")
        datos = resumen_horas_paradas(
            datetime(2026, 7, 1, 3, tzinfo=dt_timezone.utc),
            datetime(2026, 7, 2, 3, tzinfo=dt_timezone.utc),
        )
        self.assertEqual(datos[0]["minutos_parado"], 120)
        self.assertEqual(datos[0]["cantidad_paradas"], 1)

    def test_parada_abierta_calcula_hasta_fin_y_marca_parcial(self):
        self._crear_equipo()
        response = self.client.get("/api/incidencias/horas-paradas/", {
            "inicio": "2026-07-01T00:00:00-03:00", "fin": "2026-07-01T12:00:00-03:00"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["minutos_parado"], 240)
        self.assertTrue(response.data[0]["duracion_parcial"])

    def test_personal_filtros_agrupacion_y_resumen_mensual(self):
        response = self.client.post("/api/incidencias/personas/", {
            "persona": self.persona.id,
            "tipo": "llegada_tarde",
            "fecha": "2026-07-03",
            "hora_inicio": "08:00:00",
            "hora_fin": "08:30:00",
            "motivo": "Transporte",
            "estado_justificacion": "pendiente",
            "mensaje_origen": "Ana llega tarde",
            "source_message_id": "personal-1",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["duracion_minutos"], 30)
        grupos = self.client.get("/api/incidencias/por-persona/", {"inicio": "2026-07-01", "fin": "2026-07-31"})
        self.assertEqual(grupos.data[0]["cantidad"], 1)
        resumen = self.client.get("/api/incidencias/resumen-mensual/", {"periodo": "2026-07"})
        self.assertEqual(resumen.status_code, 200)
        self.assertEqual(resumen.data["llegadas_tarde"], 1)
        self.assertEqual(resumen.data["retiros_anticipados"], 0)

    def test_resuelve_ids_por_nombre_o_referencia(self):
        equipos = self.client.get("/api/incidencias/resolver/", {"tipo": "equipo", "q": "Forwarder"})
        personas = self.client.get("/api/incidencias/resolver/", {"tipo": "persona", "q": "Ana"})
        self.assertEqual(equipos.data[0]["id"], self.equipo.id)
        self.assertEqual(personas.data[0]["id"], self.persona.id)

    def test_requiere_token_del_bot(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/incidencias/equipos/").status_code, 403)
