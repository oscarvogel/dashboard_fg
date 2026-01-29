import io
import os
import json
import calendar
from collections import defaultdict, OrderedDict
from datetime import date, datetime, timedelta

from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.core.management.base import BaseCommand
from django.db.models import Sum, F

from dateutil.relativedelta import relativedelta
# (Gráficos ahora se renderizan en el adjunto HTML con ApexCharts)

from produccion.models import (
    CargaCombustible,
    RegistroProduccion,
    ProduccionMensual,
    UnidadNegocio,
)


def _parse_date_or_none(s: str):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _business_days_in_month(d: date) -> int:
    year = d.year
    month = d.month
    days_in_month = calendar.monthrange(year, month)[1]
    return sum(1 for day in range(1, days_in_month + 1) if date(year, month, day).weekday() < 5)


def _business_days_in_range(start: date, end: date) -> int:
    return sum(1 for i in range((end - start).days + 1) if (start + timedelta(days=i)).weekday() < 5)


# Ya no generamos PNGs; los gráficos se renderizan en el HTML adjunto


class Command(BaseCommand):
    help = "Envía un mail con KPIs y gráficos de producción/combustible en el rango dado"

    def add_arguments(self, parser):
        parser.add_argument("--start-date", dest="start_date", help="YYYY-MM-DD (opcional)")
        parser.add_argument("--end-date", dest="end_date", help="YYYY-MM-DD (opcional)")
        parser.add_argument("--un-ids", dest="un_ids", help="IDs de UN separados por coma (opcional)")
        parser.add_argument("--operaciones", dest="operaciones", help="Operaciones separadas por coma (opcional)")
        parser.add_argument("--to", dest="to", required=False, help="Emails separados por coma (si no se indica, usa KPI_REPORT_TO del .env)")
        parser.add_argument("--subject", dest="subject", help="Asunto del email (opcional)")
        parser.add_argument(
            "--period",
            dest="period",
            choices=["auto", "last-month", "last-week"],
            default="auto",
            help="Si no se indican fechas: auto=mes anterior si hoy es día 1, sino semana anterior",
        )

    def handle(self, *args, **options):
        start_date = _parse_date_or_none(options.get("start_date"))
        end_date = _parse_date_or_none(options.get("end_date"))
        period = options.get("period")

        # Rango por defecto: si no se pasa, usar mes anterior.
        if not start_date or not end_date:
            today = date.today()
            if period == "last-week":
                # semana anterior (lunes-domingo)
                weekday = today.weekday()
                last_sunday = today - timedelta(days=weekday + 1)
                last_monday = last_sunday - timedelta(days=6)
                start_date = start_date or last_monday
                end_date = end_date or last_sunday
            else:
                # mes anterior calendario
                first_this_month = today.replace(day=1)
                last_month_end = first_this_month - timedelta(days=1)
                last_month_start = last_month_end.replace(day=1)
                start_date = start_date or last_month_start
                end_date = end_date or last_month_end

        if start_date > end_date:
            raise SystemExit("start_date no puede ser posterior a end_date")

        # Filtros opcionales
        un_ids = []
        if options.get("un_ids"):
            try:
                un_ids = [int(x.strip()) for x in options["un_ids"].split(",") if x.strip()]
            except Exception:
                pass

        operaciones = []
        if options.get("operaciones"):
            operaciones = [x.strip() for x in options["operaciones"].split(",") if x.strip()]

        to_value = options.get("to") or os.getenv("KPI_REPORT_TO", "")
        to_emails = [x.strip() for x in to_value.split(",") if x.strip()]
        if not to_emails:
            raise SystemExit("Debe indicar destinatarios con --to o definir KPI_REPORT_TO en el .env")
        subject = options.get("subject") or self._default_subject(start_date, end_date)

        # 1) Consumo total de combustible por frente (UN)
        consumo_por_frente = self._consumo_por_frente(start_date, end_date)

        # 2) Producción real vs esperada (según ProduccionMensual)
        real_total, esperada_total, unidad_prod = self._produccion_real_vs_esperada(
            start_date, end_date, un_ids=un_ids, operaciones=operaciones
        )

        # 3) Consumos medios por equipo + semáforo vs 6 meses antes
        equipos_current = self._consumo_por_equipo_lh(start_date, end_date)
        prev_start = start_date - relativedelta(months=6)
        prev_end = end_date - relativedelta(months=6)
        equipos_prev = self._consumo_por_equipo_lh(prev_start, prev_end)
        comparativa = self._comparar_periodos_equipo(equipos_current, equipos_prev)

        # 4) Generar reporte HTML (ApexCharts + Tailwind) como adjunto
        attachment_html = self._render_html_attachment(
            start_date,
            end_date,
            consumo_por_frente,
            real_total,
            esperada_total,
            unidad_prod,
            comparativa,
        )

        # Armar email (solo texto breve en el cuerpo)
        body_text = (
            f"Adjunto encontrará el reporte de KPIs del período {start_date:%Y-%m-%d} a {end_date:%Y-%m-%d}. "
            "Abra el archivo HTML adjunto para ver los gráficos interactivos."
        )
        msg = EmailMultiAlternatives(subject=subject, body=body_text, to=to_emails)

        # Adjuntar archivo HTML
        filename = f"kpi_report_{start_date:%Y%m%d}-{end_date:%Y%m%d}.html"
        msg.attach(filename, attachment_html, "text/html")

        msg.send()

        self.stdout.write(self.style.SUCCESS(f"Reporte enviado a {', '.join(to_emails)}"))

    def _default_subject(self, start_date: date, end_date: date) -> str:
        return f"KPIs Producción y Combustible ({start_date:%Y-%m-%d} a {end_date:%Y-%m-%d})"

    def _consumo_por_frente(self, start: date, end: date):
        qs = (
            CargaCombustible.objects.filter(fecha__range=[start, end], tipo_mov="E")
            .values("unidad_negocio")
            .annotate(total_litros=Sum("litros"))
        )
        un_map = {u.id: u.nombre for u in UnidadNegocio.objects.filter(id__in=[x["unidad_negocio"] for x in qs if x["unidad_negocio"]])}
        datos = OrderedDict()
        for item in qs:
            if not item["unidad_negocio"]:
                nombre = "Sin UN"
            else:
                nombre = un_map.get(item["unidad_negocio"], str(item["unidad_negocio"]))
            datos[nombre] = float(item["total_litros"] or 0.0)
        return datos

    def _produccion_real_vs_esperada(self, start: date, end: date, un_ids=None, operaciones=None):
        un_ids = un_ids or []
        operaciones = operaciones or []

        # Real: sumar campo 'produccion' (asumiendo misma unidad que meta)
        filtro = {"fecha__gte": start, "fecha__lte": end}
        if un_ids:
            filtro["cod_un_id__in"] = un_ids
        if operaciones:
            filtro["operacion__in"] = operaciones

        real_total = (
            RegistroProduccion.objects.filter(**filtro).aggregate(total=Sum("produccion"))
        )["total"] or 0.0

        # Esperada: seguir lógica del dashboard
        dias_mes = _business_days_in_month(end)
        dias_hab_rango = _business_days_in_range(start, end)
        proporcion = (dias_hab_rango / dias_mes) if dias_mes > 0 else 0.0

        periodo = end.strftime("%Y%m")
        qm = ProduccionMensual.objects.filter(periodo=periodo)
        if un_ids:
            qm = qm.filter(unidad_negocio_id__in=un_ids)
        if operaciones:
            qm = qm.filter(tipo_operacion__in=operaciones)

        agregado = qm.aggregate(meta_mensual=Sum("produccion"))
        meta_mensual = float(agregado["meta_mensual"] or 0.0)
        esperada_total = round(meta_mensual * proporcion, 2)
        unidad_produccion = qm.values_list("unidad_produccion", flat=True).distinct().first()

        return float(real_total), float(esperada_total), (unidad_produccion or "unidades")

    def _consumo_por_equipo_lh(self, start: date, end: date):
        # Combustible por equipo (litros)
        fuel_qs = (
            CargaCombustible.objects.filter(fecha__range=[start, end], tipo_mov="E")
            .values("equipo_id")
            .annotate(litros=Sum("litros"))
        )
        fuel_map = {row["equipo_id"]: float(row["litros"] or 0.0) for row in fuel_qs}

        # Horas por equipo
        horas_qs = (
            RegistroProduccion.objects.filter(fecha__range=[start, end])
            .values("cod_equipo_id")
            .annotate(horas=Sum(F("hr_fin") - F("hr_inicio")))
        )
        horas_map = {row["cod_equipo_id"]: float(row["horas"] or 0.0) for row in horas_qs}

        # Nombres
        # Traer solo equipos presentes en fuel u horas para limitar consulta
        ids = set(fuel_map.keys()) | set(horas_map.keys())
        from produccion.models import Equipo

        nombre_map = {}
        if ids:
            for e in Equipo.objects.filter(id__in=list(ids)).only("id", "detalle", "patente"):
                nombre_map[e.id] = f"{e.detalle or e.patente}"

        out = []
        for eq_id in ids:
            horas = horas_map.get(eq_id, 0.0)
            litros = fuel_map.get(eq_id, 0.0)
            if horas <= 0:
                lh = None
            else:
                lh = litros / horas if horas else None
            out.append({
                "equipo_id": eq_id,
                "equipo": nombre_map.get(eq_id, str(eq_id)),
                "horas": round(horas, 2),
                "litros": round(litros, 2),
                "lph": round(lh, 3) if lh is not None else None,
            })
        # Ordenar por consumo por hora desc, nulos al final
        out.sort(key=lambda x: (x["lph"] is None, -(x["lph"] or 0)))
        return out

    def _comparar_periodos_equipo(self, actual, previo):
        prev_map = {x["equipo_id"]: x for x in previo}
        comparativa = []
        for x in actual:
            prev = prev_map.get(x["equipo_id"])
            lph_prev = prev["lph"] if prev else None
            lph_act = x["lph"]
            delta_pct = None
            color = "gris"
            if lph_act is not None and lph_prev is not None and lph_prev > 0:
                delta_pct = (lph_act / lph_prev) - 1.0
                # Menor consumo por hora = mejora (verde)
                if delta_pct <= -0.05:
                    color = "verde"
                elif -0.05 < delta_pct <= 0.05:
                    color = "amarillo"
                else:
                    color = "rojo"
            comparativa.append({
                **x,
                "lph_prev": lph_prev,
                "delta_pct": round(delta_pct * 100, 1) if delta_pct is not None else None,
                "indicador": color,
            })
        return comparativa

    def _render_html(
        self,
        start: date,
        end: date,
        consumo_por_frente,
        real_total,
        esperada_total,
        unidad_produccion,
        comparativa_equipos,
    ) -> str:
        # Tabla equipos (top 15 por horas)
        comps = sorted([x for x in comparativa_equipos if x.get("horas", 0) > 0 and x.get("lph") is not None], key=lambda x: -x["horas"])[:15]

        def badge(color):
            m = {"verde": "#22c55e", "amarillo": "#eab308", "rojo": "#ef4444", "gris": "#9ca3af"}
            return f"<span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{m.get(color, '#9ca3af')}'></span>"

        filas_parts = []
        for x in comps:
            prev_val = x.get("lph_prev")
            prev_str = "" if prev_val is None else f"{prev_val:.3f}"
            delta_val = x.get("delta_pct")
            delta_str = "" if delta_val is None else f"{delta_val:.1f}%"
            filas_parts.append(
                (
                    "<tr>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #eee'>{x['equipo']}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #eee;text-align:right'>{x['horas']:.2f}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #eee;text-align:right'>{x['lph']:.3f}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #eee;text-align:right'>{prev_str}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #eee;text-align:right'>{delta_str}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #eee;text-align:center'>{badge(x['indicador'])}</td>"
                    "</tr>"
                )
            )
        filas = "".join(filas_parts)

        un_rows = "".join(
            f"<tr><td style='padding:6px 8px;border-bottom:1px solid #eee'>{un}</td>"
            f"<td style='padding:6px 8px;border-bottom:1px solid #eee;text-align:right'>{litros:,.0f}</td></tr>"
            for un, litros in consumo_por_frente.items()
        )

        html = f"""
        <div style='font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#0f172a'>
          <h2 style='margin:0 0 12px 0'>KPIs de Producción y Combustible</h2>
          <p style='margin:0 0 16px 0'>Periodo: {start:%Y-%m-%d} a {end:%Y-%m-%d}</p>

          <h3 style='margin:16px 0 6px 0'>1) Consumo total de combustible por frente</h3>
          <img src="cid:kpi1.png" alt="Consumo por frente" style="max-width:100%;height:auto;border:1px solid #eee"/>
          <table cellpadding='0' cellspacing='0' style='border-collapse:collapse;margin-top:8px;min-width:320px'>
            <thead>
              <tr>
                <th style='text-align:left;padding:6px 8px;border-bottom:2px solid #e5e7eb'>Frente</th>
                <th style='text-align:right;padding:6px 8px;border-bottom:2px solid #e5e7eb'>Litros</th>
              </tr>
            </thead>
            <tbody>
              {un_rows}
            </tbody>
          </table>

          <h3 style='margin:20px 0 6px 0'>2) Producción real vs esperada</h3>
          <img src="cid:kpi2.png" alt="Real vs Esperada" style="max-width:100%;height:auto;border:1px solid #eee"/>
          <p style='margin:8px 0 0 0'>
            Real: <strong>{real_total:,.0f}</strong> {unidad_produccion or ''} —
            Esperada (proporcional): <strong>{esperada_total:,.0f}</strong> {unidad_produccion or ''}
          </p>

          <h3 style='margin:20px 0 6px 0'>3) Consumos medios por equipo (L/h) vs hace 6 meses</h3>
          <img src="cid:kpi3.png" alt="Consumo medio por equipo" style="max-width:100%;height:auto;border:1px solid #eee"/>
          <table cellpadding='0' cellspacing='0' style='border-collapse:collapse;margin-top:8px;min-width:520px'>
            <thead>
              <tr>
                <th style='text-align:left;padding:6px 8px;border-bottom:2px solid #e5e7eb'>Equipo</th>
                <th style='text-align:right;padding:6px 8px;border-bottom:2px solid #e5e7eb'>Horas</th>
                <th style='text-align:right;padding:6px 8px;border-bottom:2px solid #e5e7eb'>L/h actual</th>
                <th style='text-align:right;padding:6px 8px;border-bottom:2px solid #e5e7eb'>L/h -6m</th>
                <th style='text-align:right;padding:6px 8px;border-bottom:2px solid #e5e7eb'>Var.</th>
                <th style='text-align:center;padding:6px 8px;border-bottom:2px solid #e5e7eb'>Indicador</th>
              </tr>
            </thead>
            <tbody>
              {filas}
            </tbody>
          </table>

          <p style='margin-top:18px;color:#475569'>
            Nota: Indicador verde = mejora (menor L/h que hace 6 meses), amarillo = estable (±5%), rojo = peor (>+5%).
          </p>
        </div>
        """
        return html

    def _render_html_attachment(
                self,
                start: date,
                end: date,
                consumo_por_frente,
                real_total,
                esperada_total,
                unidad_produccion,
                comparativa_equipos,
        ) -> str:
        # Preparar datos para JS
        frentes_labels = list(consumo_por_frente.keys())
        frentes_values = list(consumo_por_frente.values())

        real_vs_esp = [float(real_total or 0.0), float(esperada_total or 0.0)]

        comps = sorted([x for x in comparativa_equipos if x.get("horas", 0) > 0 and x.get("lph") is not None], key=lambda x: -x["horas"])[:20]
        equipos_labels = [c["equipo"] for c in comps]
        equipos_lph = [c["lph"] for c in comps]
        equipos_horas = [c["horas"] for c in comps]
        equipos_prev = [c.get("lph_prev") for c in comps]
        equipos_delta = [c.get("delta_pct") for c in comps]
        indicadores = [c.get("indicador", "gris") for c in comps]

        # JSON serializados
        jl = lambda x: json.dumps(x, ensure_ascii=False)
        unidad = (unidad_produccion or "unidades")

        html = f"""<!doctype html>
<html lang="es">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Reporte KPIs {start:%Y-%m-%d} a {end:%Y-%m-%d}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    </head>
    <body class="bg-slate-50 text-slate-800">
        <div class="max-w-6xl mx-auto p-6">
            <h1 class="text-2xl font-semibold mb-1">Reporte de KPIs</h1>
            <p class="text-sm text-slate-600 mb-6">Período: {start:%Y-%m-%d} a {end:%Y-%m-%d}</p>

            <!-- Consumo por Frente -->
            <div class="bg-white rounded-lg shadow p-4 mb-6">
                <h2 class="text-lg font-medium mb-3">1) Consumo de Combustible por Frente</h2>
                <div id="chart_frentes"></div>
                <div class="mt-4 overflow-x-auto">
                    <table class="min-w-[320px] w-full text-sm">
                        <thead>
                            <tr class="border-b">
                                <th class="text-left py-2">Frente</th>
                                <th class="text-right py-2">Litros</th>
                            </tr>
                        </thead>
                        <tbody>
                        {''.join(f'<tr class="border-b last:border-b-0"><td class="py-2">{n}</td><td class="py-2 text-right">{v:,.0f}</td></tr>' for n, v in consumo_por_frente.items())}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Real vs Esperada -->
            <div class="bg-white rounded-lg shadow p-4 mb-6">
                <h2 class="text-lg font-medium mb-3">2) Producción Real vs Esperada</h2>
                <div id="chart_real_esp"></div>
                <p class="mt-3 text-sm">Unidad: {unidad}</p>
            </div>

            <!-- Consumo medio por equipo -->
            <div class="bg-white rounded-lg shadow p-4 mb-6">
                <h2 class="text-lg font-medium mb-3">3) Consumos medios por equipo (L/h) vs hace 6 meses</h2>
                <div id="chart_equipos" class="mb-4"></div>
                <div class="overflow-x-auto">
                    <table class="min-w-[520px] w-full text-sm">
                        <thead>
                            <tr class="border-b">
                                <th class="text-left py-2">Equipo</th>
                                <th class="text-right py-2">Horas</th>
                                <th class="text-right py-2">L/h actual</th>
                                <th class="text-right py-2">L/h -6m</th>
                                <th class="text-right py-2">Var.</th>
                                <th class="text-center py-2">Indicador</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(
                                f'<tr class="border-b last:border-b-0">'
                                f'<td class="py-2">{c["equipo"]}</td>'
                                f'<td class="py-2 text-right">{c["horas"]:.2f}</td>'
                                f'<td class="py-2 text-right">{c["lph"]:.3f}</td>'
                                f'<td class="py-2 text-right">{"" if (c.get("lph_prev") is None) else f"{c["lph_prev"]:.3f}"}</td>'
                                f'<td class="py-2 text-right">{"" if (c.get("delta_pct") is None) else f"{c["delta_pct"]:.1f}%"}</td>'
                                f'<td class="py-2 text-center">'
                                f'  <span class="inline-block w-3 h-3 rounded-full ' + '{"verde":"bg-green-500","amarillo":"bg-yellow-500","rojo":"bg-red-500"}.get(c.get("indicador","gris"),"bg-slate-400")' + '"></span>'
                                f'</td>'
                                f'</tr>'
                                for c in comps
                            )}
                        </tbody>
                    </table>
                </div>
                <p class="mt-3 text-xs text-slate-500">Indicador: verde ≤ -5%, amarillo ±5%, rojo > +5% vs 6 meses atrás.</p>
            </div>
        </div>

        <script>
            const frentesLabels = {jl(frentes_labels)};
            const frentesValues = {jl(frentes_values)};

            const realVsEsperada = {jl(real_vs_esp)};
            const unidadProd = {json.dumps(unidad, ensure_ascii=False)};

            const equiposLabels = {jl(equipos_labels)};
            const equiposLph = {jl(equipos_lph)};

            // Chart 1: Consumo por Frente
            new ApexCharts(document.querySelector('#chart_frentes'), {{
                chart: {{ type: 'bar', height: 380, toolbar: {{ show: false }} }},
                series: [{{ name: 'Litros', data: frentesValues }}],
                xaxis: {{ categories: frentesLabels }},
                colors: ['#3b82f6'],
                dataLabels: {{ enabled: false }},
                tooltip: {{ y: {{ formatter: (val) => Intl.NumberFormat('es-AR').format(val) + ' L' }} }}
            }}).render();

            // Chart 2: Real vs Esperada
            new ApexCharts(document.querySelector('#chart_real_esp'), {{
                chart: {{ type: 'bar', height: 360, toolbar: {{ show: false }} }},
                series: [{{ name: 'Valor', data: realVsEsperada }}],
                xaxis: {{ categories: ['Real', 'Esperada'] }},
                colors: ['#10b981', '#f59e0b'],
                dataLabels: {{ enabled: true, formatter: (val) => Intl.NumberFormat('es-AR').format(val) }},
                tooltip: {{ y: {{ formatter: (val) => Intl.NumberFormat('es-AR').format(val) + ' ' + unidadProd }} }}
            }}).render();

            // Chart 3: L/h por Equipo (Top por horas)
            new ApexCharts(document.querySelector('#chart_equipos'), {{
                chart: {{ type: 'bar', height: 420, toolbar: {{ show: false }} }},
                series: [{{ name: 'L/h', data: equiposLph }}],
                xaxis: {{ categories: equiposLabels }},
                plotOptions: {{ bar: {{ horizontal: true }} }},
                colors: ['#06b6d4'],
                dataLabels: {{ enabled: false }},
                tooltip: {{ y: {{ formatter: (val) => (val ?? 0).toFixed(3) + ' L/h' }} }}
            }}).render();
        </script>
    </body>
</html>
        """
        return html
