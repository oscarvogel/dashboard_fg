import os
import ftplib
import io
from datetime import timedelta, datetime
from django.core.management.base import BaseCommand
from django.db.models import Sum, F, FloatField, ExpressionWrapper, Q
from django.utils import timezone
from produccion.models import RegistroProduccion, ProduccionMensual


class Command(BaseCommand):
    help = 'Genera el reporte diario de facturación por unidad de negocio (CTL y FT) en HTML.'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Fecha del reporte (YYYY-MM-DD o DD-MM-YYYY). Por defecto ayer.')

    def handle(self, *args, **options):
        if options.get('date'):
            date_str = options.get('date')
            target_date = None
            # Accept YYYY-MM-DD, DD-MM-YYYY or DD/MM/YYYY
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
                try:
                    target_date = datetime.strptime(date_str, fmt).date()
                    break
                except Exception:
                    continue
            if not target_date:
                raise ValueError('Formato de fecha no reconocido. Use YYYY-MM-DD o DD-MM-YYYY.')
        else:
            target_date = timezone.now().date() - timedelta(days=1)

        month_start = target_date.replace(day=1)
        month_end = self._get_month_end(target_date)

        self.stdout.write(f"Generando reporte de facturación para: {target_date}")

        qs_month = RegistroProduccion.objects.filter(fecha__gte=month_start, fecha__lte=target_date)

        units = self._collect_units(qs_month, target_date, month_start, month_end)

        html = self._generate_html(target_date, units)

        filename = f"reporte_facturacion_{target_date.strftime('%Y%m%d')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        self.stdout.write(self.style.SUCCESS(f"Archivo generado: {filename}"))

        self.upload_ftp(filename, html)

    def _collect_units(self, qs_month, target_date, month_start, month_end):
        # Build structure: FT/CTL aggregated by UN, BIOMASA per equipo (chipeado only)
        units = {}
        
        # Obtener tarifas de ProduccionMensual para este período
        period = target_date.strftime('%Y%m')
        tarifas_map = {}  # {(un_id, tipo_operacion): tarifa}
        pm_qs = ProduccionMensual.objects.filter(periodo=period)
        for pm in pm_qs:
            tipo = (pm.tipo_operacion or '').strip().upper()
            if tipo in ('PROCESO', 'CARGA', 'CHIPEADO', 'CHIPEADO SOBRE CAMION', 'CHIPEADO EN SUELO', 'ACARREO DE TROZAS', 'ACARREO'):
                un_id = pm.unidad_negocio_id if pm.unidad_negocio_id else None
                if un_id:
                    # Normalizar tipo_operacion para búsqueda
                    if 'CHIPEADO' in tipo:
                        tipo_normalizado = 'CHIPEADO'
                    elif 'ACARREO' in tipo:
                        tipo_normalizado = 'ACARREO DE TROZAS'
                    elif 'HORAS' in tipo:
                        tipo_normalizado = 'HORAS MAQUINA'
                    else:
                        tipo_normalizado = tipo
                    key = (un_id, tipo_normalizado)
                    # Si hay múltiples entradas, usar la que tenga tarifa mayor (más específica)
                    if key not in tarifas_map or float(pm.tarifa or 0.0) > tarifas_map[key]:
                        tarifas_map[key] = float(pm.tarifa or 0.0)
        
        registros = qs_month.filter(Q(operacion__in=['PROCESO', 'CARGA']) | Q(operacion__icontains='ACARREO') | Q(operacion__icontains='HORAS')).select_related('cod_un', 'cod_equipo')

        for r in registros:
            un_name = (r.cod_un.nombre or '').strip() if r.cod_un else 'Sin UN'
            un_key = (un_name or '').upper()
            
            # Skip BIOMASA for PROCESO/CARGA/ACARREO (biomasa only uses chipeado)
            if 'BIOMASA' in un_key:
                continue

            eq = r.cod_equipo
            eq_id = eq.id if eq else None
            un_id = r.cod_un.id if r.cod_un else None

            if un_name not in units:
                units[un_name] = {'rows': {}, 'subtotal': {'day': 0.0, 'month': 0.0}, 'biomasa_chipeado': {}, 'equipos_ids': set(), 'un_id': un_id}

            # Determinar el nombre de la fila según la operación y unidad
            operacion_tipo = r.operacion.strip().upper() if r.operacion else ''
            if 'ACARREO' in operacion_tipo:
                row_key = 'Acarreo de Trozas'
            elif 'CTL' in un_key:
                row_key = 'Cosecha CTL'
            elif 'FT' in un_key or 'FULL TREE' in un_key:
                row_key = 'Cosecha FT'
            else:
                # No es CTL, FT ni Acarreo: ignorar (evita filas duplicadas irrelevantes)
                continue
            
            if row_key not in units[un_name]['rows']:
                units[un_name]['rows'][row_key] = {'equipo_ids': set(), 'un_id': un_id, 'day': 0.0, 'month': 0.0}

            if eq_id:
                units[un_name]['rows'][row_key]['equipo_ids'].add(eq_id)

            # Obtener tarifa de ProduccionMensual basado en UN y tipo de operación
            tarifa = 0.0
            if un_id:
                # Normalizar búsqueda de tarifa para ACARREO
                if 'ACARREO' in operacion_tipo:
                    tipo_lookup = 'ACARREO DE TROZAS'
                else:
                    tipo_lookup = operacion_tipo
                if tipo_lookup in ('PROCESO', 'CARGA', 'ACARREO DE TROZAS', 'HORAS MAQUINA'):
                    tarifa = tarifas_map.get((un_id, tipo_lookup), 0.0)
            
            prod = float(r.produccion or 0.0)
            fact = prod * tarifa

            units[un_name]['rows'][row_key]['month'] += fact
            if r.fecha == target_date:
                units[un_name]['rows'][row_key]['day'] += fact

        # Chipeado for biomasa (per equipo)
        chipeado_qs = RegistroProduccion.objects.filter(fecha__gte=month_start, fecha__lte=target_date, operacion__icontains='CHIPEADO').select_related('cod_un', 'cod_equipo')
        for r in chipeado_qs:
            un_name = (r.cod_un.nombre or '').strip() if r.cod_un else 'Sin UN'
            if 'BIOMASA' not in (un_name or '').upper():
                continue
            eq = r.cod_equipo
            eq_name = (eq.detalle or eq.patente) if eq else f'Equipo-{eq.id if eq else "X"}'
            eq_id = eq.id if eq else None
            un_id = r.cod_un.id if r.cod_un else None
            
            # Obtener tarifa de ProduccionMensual basado en UN y tipo CHIPEADO
            tarifa = 0.0
            if un_id:
                tarifa = tarifas_map.get((un_id, 'CHIPEADO'), 0.0)
            
            prod = float(r.produccion or 0.0)
            fact = prod * tarifa
            if un_name not in units:
                units[un_name] = {'rows': {}, 'subtotal': {'day': 0.0, 'month': 0.0}, 'biomasa_chipeado': {}, 'un_id': un_id}
            if eq_name not in units[un_name]['biomasa_chipeado']:
                units[un_name]['biomasa_chipeado'][eq_name] = {'equipo_id': eq_id, 'un_id': un_id, 'day': 0.0, 'month': 0.0}
            units[un_name]['biomasa_chipeado'][eq_name]['month'] += fact
            if r.fecha == target_date:
                units[un_name]['biomasa_chipeado'][eq_name]['day'] += fact

        # Expected production from ProduccionMensual (incluye tarifa)
        period = target_date.strftime('%Y%m')
        pm_qs = ProduccionMensual.objects.filter(periodo=period)
        expected_by_equipo = {}
        expected_by_un = {}  # {un_id: {'total': money, 'cantidad_equipo': int}}
        for pm in pm_qs:
            tipo = (pm.tipo_operacion or '').strip().upper()
            # Aceptar PROCESO, CARGA, ACARREO, HORAS MAQUINA, y cualquier tipo que contenga CHIPEADO
            if tipo not in ('PROCESO', 'CARGA') and 'CHIPEADO' not in tipo and 'ACARREO' not in tipo and 'HORAS' not in tipo:
                continue
            
            prod_qty = float(pm.produccion or 0.0)
            tarifa = float(pm.tarifa or 0.0)
            plan_money = prod_qty * tarifa
            
            if pm.equipo_id and pm.equipo_id != 477:
                # Sum if multiple entries for same equipo (plan in money)
                expected_by_equipo[pm.equipo_id] = expected_by_equipo.get(pm.equipo_id, 0.0) + plan_money
            elif pm.unidad_negocio_id:
                # Sum if multiple entries for same unidad (plan in money) y guardar cantidad_equipo
                if pm.unidad_negocio_id not in expected_by_un:
                    expected_by_un[pm.unidad_negocio_id] = {'total': 0.0, 'cantidad_equipo': float(pm.cantidad_equipo or 1)}
                expected_by_un[pm.unidad_negocio_id]['total'] += plan_money
                # Usar el mayor cantidad_equipo si hay múltiples entradas
                if pm.cantidad_equipo and float(pm.cantidad_equipo) > expected_by_un[pm.unidad_negocio_id]['cantidad_equipo']:
                    expected_by_un[pm.unidad_negocio_id]['cantidad_equipo'] = float(pm.cantidad_equipo)

        business_days_total = self._count_weekdays(month_start, month_end)
        business_days_elapsed = self._count_weekdays(month_start, target_date)

        # Attach plan money per equipment and compute subtotals
        for un_name, block in units.items():
            subtotal_day = 0.0
            subtotal_month = 0.0
            # For CTL/FT: aggregate plan from all equipos in the set
            for row_name, stats in block['rows'].items():
                equipo_ids = stats.get('equipo_ids', set())
                un_id = stats.get('un_id')
                
                # Sum expected money from all equipos in this row
                plan_month_money = 0.0
                equipos_sin_plan = []
                
                for eq_id in equipo_ids:
                    if eq_id in expected_by_equipo:
                        plan_month_money += expected_by_equipo[eq_id]
                    else:
                        equipos_sin_plan.append(eq_id)
                
                # If some equipos don't have plan, try UN level and divide by cantidad_equipo
                if equipos_sin_plan and un_id and un_id in expected_by_un:
                    un_data = expected_by_un[un_id]
                    cantidad_equipos = un_data['cantidad_equipo'] or 1
                    plan_por_equipo = un_data['total'] / cantidad_equipos
                    # Sumar el plan de los equipos que no tenían plan específico
                    plan_month_money += plan_por_equipo * len(equipos_sin_plan)
                
                plan_day_money = (plan_month_money / business_days_total) if business_days_total > 0 else 0.0

                stats['plan_month'] = plan_month_money
                stats['plan_day'] = plan_day_money

                subtotal_day += stats.get('day', 0.0)
                subtotal_month += stats.get('month', 0.0)

            # For biomasa chipeado: per-equipo plan (already in money from ProduccionMensual)
            for eq_name, stats in block['biomasa_chipeado'].items():
                eq_id = stats.get('equipo_id')
                un_id = stats.get('un_id')
                plan_month_money = 0.0
                
                if eq_id and eq_id in expected_by_equipo:
                    plan_month_money = expected_by_equipo[eq_id]
                elif un_id and un_id in expected_by_un:
                    # No hay plan específico, usar plan de UN dividido por cantidad_equipo
                    un_data = expected_by_un[un_id]
                    cantidad_equipos = un_data['cantidad_equipo'] or 1
                    plan_month_money = un_data['total'] / cantidad_equipos
                
                plan_day_money = (plan_month_money / business_days_total) if business_days_total > 0 else 0.0
                stats['plan_month'] = plan_month_money
                stats['plan_day'] = plan_day_money

                subtotal_day += stats.get('day', 0.0)
                subtotal_month += stats.get('month', 0.0)

            block['subtotal']['day'] = subtotal_day
            block['subtotal']['month'] = subtotal_month

        return units

    def _generate_html(self, target_date, units):
        lines = []
        lines.append('<html><head><meta charset="utf-8"><title>Reporte Facturación</title>')
        lines.append('<style>body{font-family:Arial,Helvetica,sans-serif;background:#f6fbf7;color:#173a2f}h1,h2,h3{color:#1f6f3b;margin:6px 0}table{border-collapse:collapse;width:100%;background:#ffffff}th{background:#dff3e0;color:#0b4f2b;padding:8px;border:1px solid #cfe6d0}td{padding:6px;border:1px solid #e6f1ea}tr.total{background:#eaf7ec;font-weight:bold}td.right{text-align:right}caption{font-size:14px;font-weight:bold;padding:8px}</style>')
        lines.append('</head><body>')
        lines.append(f'<h1>FORESTAL GARUHAPE SA</h1>')
        lines.append(f'<h2>Reporte de Facturación - {target_date.strftime("%d/%m/%Y")}</h2>')

        # Una sola tabla con todas las unidades y equipos
        lines.append('<table>')
        lines.append('<caption>Montos en $</caption>')
        lines.append('<tr><th>Concepto</th><th>PLAN DÍA</th><th>PLAN MES</th><th>REAL DÍA</th><th>REAL MES</th></tr>')

        # Acumuladores para el total general
        total_general_plan_day = 0.0
        total_general_plan_month = 0.0
        total_general_real_day = 0.0
        total_general_real_month = 0.0

        # Recorrer todas las unidades de negocio
        for un_name, data in units.items():
            # Saltar unidades sin filas ni biomasa
            if not data.get('rows') and not data.get('biomasa_chipeado'):
                continue

            # Cabecera de la unidad (una fila que indica la unidad de negocio)
            lines.append(f'<tr><td colspan="5" style="background:#eef7ee;font-weight:bold">Negocio: {un_name}</td></tr>')
            # FT/CTL rows (aggregated)
            for row_name, stats in data.get('rows', {}).items():
                plan_day = stats.get('plan_day', 0.0)
                plan_month = stats.get('plan_month', 0.0)
                real_day = stats.get('day', 0.0)
                real_month = stats.get('month', 0.0)
                pct = (real_month / plan_month * 100.0) if plan_month > 0 else 0.0
                lines.append(f'<tr><td>{row_name}</td><td class="right">{plan_day:,.2f}</td><td class="right">{plan_month:,.2f}</td><td class="right">{real_day:,.2f}</td><td class="right">{real_month:,.2f} ({pct:.0f}%)</td></tr>')
                
                total_general_plan_day += plan_day
                total_general_plan_month += plan_month
                total_general_real_day += real_day
                total_general_real_month += real_month

            # biomasa chipeado (per equipo)
            if data.get('biomasa_chipeado'):
                for eq_name, stats in data.get('biomasa_chipeado', {}).items():
                    plan_day = stats.get('plan_day', 0.0)
                    plan_month = stats.get('plan_month', 0.0)
                    real_day = stats.get('day', 0.0)
                    real_month = stats.get('month', 0.0)
                    pct = (real_month / plan_month * 100.0) if plan_month > 0 else 0.0
                    lines.append(f'<tr><td>{eq_name}</td><td class="right">{plan_day:,.2f}</td><td class="right">{plan_month:,.2f}</td><td class="right">{real_day:,.2f}</td><td class="right">{real_month:,.2f} ({pct:.0f}%)</td></tr>')
                    
                    total_general_plan_day += plan_day
                    total_general_plan_month += plan_month
                    total_general_real_day += real_day
                    total_general_real_month += real_month

        # Total general
        total_general_pct = (total_general_real_month / total_general_plan_month * 100.0) if total_general_plan_month > 0 else 0.0
        lines.append(f'<tr class="total"><td>TOTAL GENERAL</td><td class="right">{total_general_plan_day:,.2f}</td><td class="right">{total_general_plan_month:,.2f}</td><td class="right">{total_general_real_day:,.2f}</td><td class="right">{total_general_real_month:,.2f} ({total_general_pct:.0f}%)</td></tr>')

        lines.append('</table>')
        lines.append('</body></html>')
        return '\n'.join(lines)

    def upload_ftp(self, filename, content):
        ftp_host = os.environ.get('FTP_HOST')
        ftp_user = os.environ.get('FTP_USER')
        ftp_pass = os.environ.get('FTP_PASSWORD')
        ftp_dir = os.environ.get('FTP_DIR')

        if not all([ftp_host, ftp_user, ftp_pass]):
            self.stdout.write(self.style.WARNING("Saltando carga FTP: Faltan credenciales (FTP_HOST, FTP_USER, FTP_PASSWORD)"))
            return

        try:
            ftp = ftplib.FTP(ftp_host)
            ftp.login(ftp_user, ftp_pass)
            if ftp_dir:
                try:
                    ftp.cwd(ftp_dir)
                except ftplib.error_perm:
                    pass
            bio = io.BytesIO(content.encode('utf-8'))
            ftp.storbinary(f'STOR {filename}', bio)
            ftp.quit()
            self.stdout.write(self.style.SUCCESS(f"Archivo subido a FTP: {filename}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error subiendo a FTP: {e}"))

    def _get_month_end(self, date_obj):
        # last day of month
        if date_obj.month == 12:
            return date_obj.replace(day=31)
        next_month = date_obj.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    def _count_weekdays(self, start_date, end_date):
        if start_date > end_date:
            return 0
        delta = (end_date - start_date).days + 1
        weeks, extra = divmod(delta, 7)
        weekdays = weeks * 5
        for i in range(extra):
            day = start_date + timedelta(days=weeks * 7 + i)
            if day.weekday() < 5:
                weekdays += 1
        return weekdays
