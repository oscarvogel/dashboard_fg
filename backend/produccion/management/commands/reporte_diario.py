
import os
import ftplib
import io
import calendar
from datetime import timedelta, datetime
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum, F, FloatField, Case, When, Value, ExpressionWrapper
from django.utils import timezone
from produccion.models import RegistroProduccion, Equipo, ProduccionMensual

class Command(BaseCommand):
    help = 'Genera y envía el reporte diario de producción y consumo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Fecha del reporte (YYYY-MM-DD). Por defecto ayer.',
        )
        parser.add_argument(
            '--email',
            type=str,
            nargs='?',
            help='Correo destinatario (anula el .env).',
        )

    def handle(self, *args, **options):
        # 1. Definir fechas
        if options['date']:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date() - timedelta(days=1)
        
        month_start = target_date.replace(day=1)
        
        # Últimos 30 días para promedio (exclusivo para "Otros")
        start_30_days = target_date - timedelta(days=30)

        self.stdout.write(f"Generando reporte para: {target_date}")

        # 2. Consultas Base
        # Todo el mes hasta la fecha objetivo
        qs_month = RegistroProduccion.objects.filter(
            fecha__gte=month_start, 
            fecha__lte=target_date
        )
        
        # Solo el día objetivo
        qs_day = qs_month.filter(fecha=target_date)

        # 3. Datos Punto 1: PROCESO
        # Filtro: operacion='PROCESO' (case insensitive)
        data_proceso = self.get_production_data(target_date, qs_month, filtro_ops=['PROCESO'], label="Proceso")

        # Nuevo: Datos Punto 1b: CARGA
        # Filtro: operacion='CARGA' (case insensitive) - registramos TN cargadas y KPIs igual que Proceso
        data_carga = self.get_production_data(target_date, qs_month, filtro_ops=['CARGA'], label="Carga")

        # 4. Datos Punto 2: CHIPEADO
        # Filtro: 'CHIPEADO', 'CHIPEADO SOBRE CAMION', 'CHIPEADO EN SUELO', etc.
        # Usamos icontains 'CHIPEADO'
        data_chipeado = self.get_production_data(target_date, qs_month, lookup='operacion__icontains', val='CHIPEADO', label="Chipeado")

        # 5. Datos Punto 3: OTROS
        # Excluir PROCESO y CHIPEADO
        # Para "Otros" necesitamos: Total Combustible (Dia, Mes) y Consumo Medio 30 días.
        data_otros = self.get_others_data(target_date, month_start, start_30_days)

        # 6. Datos Punto 4: Horas No Operativas
        data_no_op = self.get_no_op_data(qs_day, qs_month)

        # 7. Generar HTML (incluye Carga)
        html_content = self.generate_html(
            target_date,
            data_proceso,
            data_carga,
            data_chipeado,
            data_otros,
            data_no_op,
        )

        # 8. Enviar Email
        subject = f"Reporte Diario Producción - {target_date.strftime('%d/%m/%Y')}"
        to_email = options['email'] or os.getenv('DAILY_REPORT_TO') or os.getenv('KPI_REPORT_TO')
        
        # Guardar archivo local SIEMPRE para FTP
        filename = f"reporte_{target_date.strftime('%Y%m%d')}.html"
        
        # Subir FTP
        self.upload_ftp(filename, html_content)

        if not to_email:
            self.stdout.write(self.style.WARNING("No se especificó destinatario (arg --email, env DAILY_REPORT_TO o KPI_REPORT_TO)."))
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.stdout.write(f"Archivo guardado localmente: {filename}")
        else:
            msg = EmailMultiAlternatives(
                subject,
                "Se adjunta el reporte diario en formato HTML.",
                None, # from_email (default)
                [e.strip() for e in to_email.split(',')]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            self.stdout.write(self.style.SUCCESS(f"Correo enviado a {to_email}"))

    def upload_ftp(self, filename, content):
        ftp_host = os.environ.get('FTP_HOST')
        ftp_user = os.environ.get('FTP_USER')
        ftp_pass = os.environ.get('FTP_PASSWORD')
        ftp_dir = os.environ.get('FTP_DIR')

        if not all([ftp_host, ftp_user, ftp_pass]):
            self.stdout.write(self.style.WARNING("Saltando carga FTP: Faltan credenciales en .env (FTP_HOST, FTP_USER, FTP_PASSWORD)"))
            return

        try:
            self.stdout.write(f"Conectando a FTP {ftp_host}...")
            ftp = ftplib.FTP(ftp_host)
            ftp.login(ftp_user, ftp_pass)
            
            if ftp_dir:
                try:
                    ftp.cwd(ftp_dir)
                except ftplib.error_perm:
                    self.stdout.write(self.style.WARNING(f"Directorio {ftp_dir} no existe o no accesible. Usando raíz."))
            
            # Convert string content to BytesIO
            bio = io.BytesIO(content.encode('utf-8'))
            
            self.stdout.write(f"Subiendo {filename}...")
            ftp.storbinary(f'STOR {filename}', bio)
            ftp.quit()
            self.stdout.write(self.style.SUCCESS(f"Archivo subido a FTP correctamente: {filename}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error subiendo a FTP: {str(e)}"))

    def get_production_data(self, target_date, qs_month, filtro_ops=None, lookup='operacion__in', val=None, label=""):
        # Construir filtro base
        kwargs = {}
        if filtro_ops:
            kwargs['operacion__in'] = filtro_ops
        elif val:
            kwargs[lookup] = val
        
        # Get expected production data for this period
        period = target_date.strftime('%Y%m')
        month_start = target_date.replace(day=1)
        month_end = self._get_month_end(target_date)
        business_days_total = self._count_weekdays(month_start, month_end)
        business_days_elapsed = self._count_weekdays(month_start, target_date)
        
        # Determine operation key for expected data lookup
        if filtro_ops:
            op_key = filtro_ops[0].upper()
        elif val:
            op_key = val.upper()
        else:
            op_key = None
        
        # Load expected production from ProduccionMensual
        expected_by_equipo = {}
        expected_by_un = {}
        if op_key:
            pm_qs = ProduccionMensual.objects.filter(periodo=period)
            for pm in pm_qs:
                tipo = (pm.tipo_operacion or '').strip().upper()
                if tipo == op_key or (op_key == 'CHIPEADO' and 'CHIPEADO' in tipo):
                    if pm.equipo_id and pm.equipo_id != 477:
                        expected_by_equipo[pm.equipo_id] = {
                            'expected': float(pm.produccion or 0.0),
                            'unit': pm.unidad_produccion or ''
                        }
                    elif pm.unidad_negocio_id:
                        expected_by_un[pm.unidad_negocio_id] = {
                            'expected': float(pm.produccion or 0.0),
                            'qty': float(pm.cantidad_equipo or 1.0),
                            'unit': pm.unidad_produccion or ''
                        }
        # Obtener todos los registros del mes (que incluyen el día)
        month_recs = qs_month.filter(**kwargs)

        # Agrupar por Unidad de Negocio, Equipo
        # Necesitamos saber nombre de UN y Equipo
        # Vamos a iterar sobre los registros y agrupar manualmente en Python para tener control total
        # O usar itertools.groupby pero los datos deben estar ordenados.
        
        # Optimización: traer solo campos necesarios y nombres relacionados
        data = month_recs.select_related('cod_equipo', 'cod_un').only(
            'fecha', 'produccion', 'hr_inicio', 'hr_fin', 'combustible', 
            'cod_equipo__detalle', 'cod_equipo__patente', 'cod_un__nombre'
        )

        structure = {} # { un_nombre: { equipo_nombre: { month_stats, day_stats } } }

        for r in data:
            un_name = r.cod_un.nombre if r.cod_un else "Sin UN"
            eq_name = r.cod_equipo.detalle or r.cod_equipo.patente or "Equipo Desconocido"
            
            if un_name not in structure:
                structure[un_name] = {}
            if eq_name not in structure[un_name]:
                structure[un_name][eq_name] = {
                    'day': {'prod': 0.0, 'horas': 0.0, 'comb': 0.0},
                    'month': {'prod': 0.0, 'horas': 0.0, 'comb': 0.0},
                    'equipo_id': r.cod_equipo.id if r.cod_equipo else None,
                    'un_id': r.cod_un.id if r.cod_un else None
                }
            
            # Valores
            prod = float(r.produccion or 0.0)
            horas = float((r.hr_fin or 0) - (r.hr_inicio or 0))
            comb = float(r.combustible or 0.0)
            
            # Acumular Mes
            structure[un_name][eq_name]['month']['prod'] += prod
            structure[un_name][eq_name]['month']['horas'] += horas
            structure[un_name][eq_name]['month']['comb'] += comb
            
            # Acumular Día si coincide
            if r.fecha == target_date:
                structure[un_name][eq_name]['day']['prod'] += prod
                structure[un_name][eq_name]['day']['horas'] += horas
                structure[un_name][eq_name]['day']['comb'] += comb

        # Procesar estructura para calcular KPIs y totales
        final_data = [] # List of blocks (UN)
        grand_total = {
            'day': {'prod': 0.0, 'horas': 0.0, 'comb': 0.0},
            'month': {'prod': 0.0, 'horas': 0.0, 'comb': 0.0},
            'expected_to_date': 0.0,
            'deviation': 0.0
        }

        for un_name, equipos in structure.items():
            un_block = {
                'name': un_name,
                'rows': [],
                'subtotal': {
                    'day': {'prod': 0.0, 'horas': 0.0, 'comb': 0.0},
                    'month': {'prod': 0.0, 'horas': 0.0, 'comb': 0.0},
                    'expected_to_date': 0.0,
                    'deviation': 0.0
                }
            }
            
            for eq_name, stats in equipos.items():
                # Calcular KPIs por equipo
                eq_id = stats.get('equipo_id')
                un_id = stats.get('un_id')
                
                # Get expected production
                expected_month = 0.0
                if eq_id and eq_id in expected_by_equipo:
                    expected_month = expected_by_equipo[eq_id]['expected']
                elif un_id and un_id in expected_by_un:
                    un_data = expected_by_un[un_id]
                    expected_month = un_data['expected'] / un_data['qty'] if un_data['qty'] > 0 else 0.0
                
                expected_to_date = (
                    expected_month * business_days_elapsed / business_days_total
                    if business_days_total > 0 else 0.0
                )
                
                actual = stats['month']['prod']
                deviation = actual - expected_to_date
                
                row = {
                    'name': eq_name,
                    'day': self._calc_kpis(stats['day']),
                    'month': self._calc_kpis(stats['month']),
                    'expected_to_date': expected_to_date,
                    'deviation': deviation
                }
                un_block['rows'].append(row)
                
                # Sumar a subtotal UN
                for t in ['day', 'month']:
                    un_block['subtotal'][t]['prod'] += stats[t]['prod']
                    un_block['subtotal'][t]['horas'] += stats[t]['horas']
                    un_block['subtotal'][t]['comb'] += stats[t]['comb']
                
                un_block['subtotal']['expected_to_date'] = un_block['subtotal'].get('expected_to_date', 0.0) + expected_to_date
                un_block['subtotal']['deviation'] = un_block['subtotal'].get('deviation', 0.0) + deviation

            # Calcular KPIs Subtotal UN
            un_block['subtotal']['day'] = self._calc_kpis(un_block['subtotal']['day'])
            un_block['subtotal']['month'] = self._calc_kpis(un_block['subtotal']['month'])
            
            final_data.append(un_block)

            # Sumar a total general
            for t in ['day', 'month']:
                grand_total[t]['prod'] += un_block['subtotal'][t]['prod']
                grand_total[t]['horas'] += un_block['subtotal'][t]['horas']
                grand_total[t]['comb'] += un_block['subtotal'][t]['comb']
            grand_total['expected_to_date'] += un_block['subtotal']['expected_to_date']
            grand_total['deviation'] += un_block['subtotal']['deviation']

        # KPIs Total General
        grand_total['day'] = self._calc_kpis(grand_total['day'])
        grand_total['month'] = self._calc_kpis(grand_total['month'])

        return {
            'label': label,
            'units': final_data,
            'total': grand_total
        }

    def _calc_kpis(self, base_data):
        prod = base_data.get('prod', 0.0)
        horas = base_data.get('horas', 0.0)
        comb = base_data.get('comb', 0.0)
        
        return {
            'prod': prod,
            'horas': horas,
            'comb': comb,
            'prod_hr': prod / horas if horas > 0 else 0.0,
            'cons_hr': comb / horas if horas > 0 else 0.0,
            'cons_unit': comb / prod if prod > 0 else 0.0 # L/M3 or L/TN
        }

    def get_others_data(self, target_date, month_start, start_30_days):
        # Determine overall start date
        overall_start = min(month_start, start_30_days)
        
        # Base Queries
        base_qs = RegistroProduccion.objects.exclude(
            operacion__iexact='PROCESO'
        ).exclude(
            operacion__icontains='CHIPEADO'
        ).filter(
            fecha__gte=overall_start,
            fecha__lte=target_date
        ).select_related('cod_equipo', 'cod_un').only(
            'fecha', 'combustible', 'hr_inicio', 'hr_fin',
            'cod_equipo__detalle', 'cod_equipo__patente', 'cod_un__nombre'
        )

        structure = {} 
        # { un_name: { eq_name: { day_fuel: 0, month_fuel: 0, fuel_30: 0, hours_30: 0 } } }

        for r in base_qs:
            un_name = r.cod_un.nombre if r.cod_un else "Sin UN"
            eq_name = r.cod_equipo.detalle or r.cod_equipo.patente or "Equipo Desconocido"
            
            if un_name not in structure:
                structure[un_name] = {}
            if eq_name not in structure[un_name]:
                structure[un_name][eq_name] = {
                    'day_fuel': 0.0, 
                    'month_fuel': 0.0,
                    'day_hours': 0.0,
                    'month_hours': 0.0,
                    'fuel_30': 0.0, 
                    'hours_30': 0.0
                }

            comb = float(r.combustible or 0.0)
            hrs = float((r.hr_fin or 0) - (r.hr_inicio or 0))

            # 30 Days (Always in range because overall_start <= start_30_days)
            # Check date >= start_30_days
            if r.fecha >= start_30_days:
                structure[un_name][eq_name]['fuel_30'] += comb
                structure[un_name][eq_name]['hours_30'] += hrs
            
            # Month
            if r.fecha >= month_start:
                structure[un_name][eq_name]['month_fuel'] += comb
                structure[un_name][eq_name]['month_hours'] += hrs
            
            # Day
            if r.fecha == target_date:
                structure[un_name][eq_name]['day_fuel'] += comb
                structure[un_name][eq_name]['day_hours'] += hrs

        # Build Output List with Subtotals
        final_data = []
        grand_total = {
            'day_fuel': 0.0, 'month_fuel': 0.0, 
            'day_hours': 0.0, 'month_hours': 0.0,
            'fuel_30': 0.0, 'hours_30': 0.0
        }

        for un_name, equipos in structure.items():
            un_block = {
                'name': un_name,
                'rows': [],
                'subtotal': {
                    'day_fuel': 0.0, 'month_fuel': 0.0, 
                    'day_hours': 0.0, 'month_hours': 0.0,
                    'fuel_30': 0.0, 'hours_30': 0.0
                }
            }
            
            for eq_name, stats in equipos.items():
                l30 = stats['fuel_30']
                h30 = stats['hours_30']
                avg = l30 / h30 if h30 > 0 else 0.0
                
                row = {
                    'name': eq_name,
                    'day_fuel': stats['day_fuel'],
                    'month_fuel': stats['month_fuel'],
                    'day_hours': stats['day_hours'],
                    'month_hours': stats['month_hours'],
                    'avg_30': avg
                }
                un_block['rows'].append(row)
                
                # Subtotal
                un_block['subtotal']['day_fuel'] += stats['day_fuel']
                un_block['subtotal']['month_fuel'] += stats['month_fuel']
                un_block['subtotal']['day_hours'] += stats['day_hours']
                un_block['subtotal']['month_hours'] += stats['month_hours']
                un_block['subtotal']['fuel_30'] += l30
                un_block['subtotal']['hours_30'] += h30

            # Calc Subtotal Avg
            s30 = un_block['subtotal']
            un_block['subtotal']['avg_30'] = s30['fuel_30'] / s30['hours_30'] if s30['hours_30'] > 0 else 0.0
            
            final_data.append(un_block)
            
            # Grand Total
            grand_total['day_fuel'] += un_block['subtotal']['day_fuel']
            grand_total['month_fuel'] += un_block['subtotal']['month_fuel']
            grand_total['day_hours'] += un_block['subtotal']['day_hours']
            grand_total['month_hours'] += un_block['subtotal']['month_hours']
            grand_total['fuel_30'] += un_block['subtotal']['fuel_30']
            grand_total['hours_30'] += un_block['subtotal']['hours_30']

        grand_total['avg_30'] = grand_total['fuel_30'] / grand_total['hours_30'] if grand_total['hours_30'] > 0 else 0.0

        return {'units': final_data, 'total': grand_total}

    def get_no_op_data(self, qs_day, qs_month):
        # Group by Equipment
        # Necesitamos saber el nombre del equipo.
        # Anotar por equipo
        
        # Diario: horas no operativas por equipo
        day_stats = qs_day.values('cod_equipo', 'cod_equipo__detalle', 'cod_equipo__patente').annotate(
            hrs=Sum('hrs_no_operativas')
        ).filter(hrs__gt=0).order_by('-hrs')

        # Mensual: horas no operativas por equipo
        month_stats = qs_month.values('cod_equipo').annotate(
            hrs_month=Sum('hrs_no_operativas')
        )

        # También obtener horas trabajadas (prod) sumadas: hr_fin - hr_inicio
        expr = ExpressionWrapper(F('hr_fin') - F('hr_inicio'), output_field=FloatField())
        prod_day_qs = qs_day.values('cod_equipo').annotate(prod_hrs_day=Sum(expr))
        prod_month_qs = qs_month.values('cod_equipo').annotate(prod_hrs_month=Sum(expr))

        month_map = {x['cod_equipo']: float(x['hrs_month'] or 0) for x in month_stats}
        prod_day_map = {x['cod_equipo']: float(x.get('prod_hrs_day') or 0) for x in prod_day_qs}
        prod_month_map = {x['cod_equipo']: float(x.get('prod_hrs_month') or 0) for x in prod_month_qs}
        
        # Agregar equipos que tuvieron horas mensuales pero no diarias? El pedido dice "por equipo, diario y mensual".
        # Si un equipo tuvo 0 horas hoy pero 10 en el mes, ¿debería aparecer? 
        # Normalmente reportes diarios miran la actividad del día. Mostraré los que tuvieron incidente hoy O son top del mes.
        # Para simplificar y cumplir estrictamente listas, mostraré lista completa de equipos con alguna hora no operativa en el mes.
        
        # Incluir equipos que tuvieron horas no operativas o horas productivas
        ids_noop = set([x['cod_equipo'] for x in month_stats if x['hrs_month'] > 0])
        ids_prod = set(prod_month_map.keys())
        all_ids = ids_noop.union(ids_prod)
        final_list = []
        
        # Need map for names for all relevant IDs
        if all_ids:
            equipos = Equipo.objects.filter(id__in=all_ids).values('id', 'detalle', 'patente')
            name_map = {e['id']: (e['detalle'] or e['patente']) for e in equipos}
            
            day_map = {x['cod_equipo']: float(x['hrs'] or 0) for x in day_stats}
            
            for eid in all_ids:
                month_noop = month_map.get(eid, 0.0)
                month_worked = prod_month_map.get(eid, 0.0)
                # Efectividad = horas trabajadas / (trabajadas + no operativas)
                denom = month_worked + month_noop
                eff = (month_worked / denom * 100.0) if denom > 0 else 0.0
                final_list.append({
                    'equipo': name_map.get(eid, f"ID {eid}"),
                    'day': day_map.get(eid, 0.0),
                    'month': month_noop,
                    'worked_month': month_worked,
                    'eff': eff
                })
        
        # Ordenar por horas mes desc
        final_list.sort(key=lambda x: x['month'], reverse=True)
        return final_list

    def _count_weekdays(self, start_date, end_date):
        if end_date < start_date:
            return 0
        count = 0
        cur = start_date
        while cur <= end_date:
            if cur.weekday() < 5:
                count += 1
            cur += timedelta(days=1)
        return count

    def _get_month_end(self, date_obj):
        last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
        return date_obj.replace(day=last_day)

    def generate_html(self, date_obj, d1, d_carga, d2, d3, d4):
        
        style = """
        <style>
            body { font-family: Arial, sans-serif; color: #333; }
            h2 { border-bottom: 2px solid #4CAF50; padding-bottom: 5px; margin-top: 30px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
            th { background-color: #f2f2f2; text-align: center; }
            .left { text-align: left; }
            .header { background-color: #4CAF50; color: white; padding: 10px; margin-bottom: 20px; }
        </style>
        """

        # Tabla 1 & 2 Template
        def render_prod_table(title, data):
            unit = "M3" if data['label'] == "Proceso" else "TN"
            
            rows = ""
            for un_block in data['units']:
                # Subtotal UN Header
                rows += f"""
                <tr style="background-color: #e8f5e9; font-weight: bold;">
                    <td class="left" colspan="12">{un_block['name']}</td>
                </tr>
                """
                # Equipments
                for r in un_block['rows']:
                    rows += f"""
                    <tr>
                        <td class="left" style="padding-left: 20px;">{r['name']}</td>
                        <td>{r['day']['prod']:,.2f}</td>
                        <td>{r['day']['horas']:,.2f}</td>
                        <td>{r['day']['prod_hr']:,.2f}</td>
                        <td>{r['month']['prod']:,.2f}</td>
                        <td>{r['expected_to_date']:,.2f}</td>
                        <td>{r['deviation']:,.2f}</td>
                        <td>{r['month']['horas']:,.2f}</td>
                        <td>{r['month']['prod_hr']:,.2f}</td>
                        <td>{r['month']['comb']:,.2f}</td>
                        <td>{r['month']['cons_hr']:,.2f}</td>
                        <td>{r['month']['cons_unit']:,.2f}</td>
                    </tr>
                    """
                # Subtotal UN Footer
                s = un_block['subtotal']
                rows += f"""
                <tr style="background-color: #f1f8e9; font-style: italic;">
                    <td class="left">Subtotal {un_block['name']}</td>
                    <td>{s['day']['prod']:,.2f}</td>
                    <td>{s['day']['horas']:,.2f}</td>
                    <td>{s['day']['prod_hr']:,.2f}</td>
                    <td>{s['month']['prod']:,.2f}</td>
                    <td>{s.get('expected_to_date', 0.0):,.2f}</td>
                    <td>{s.get('deviation', 0.0):,.2f}</td>
                    <td>{s['month']['horas']:,.2f}</td>
                    <td>{s['month']['prod_hr']:,.2f}</td>
                    <td>{s['month']['comb']:,.2f}</td>
                    <td>{s['month']['cons_hr']:,.2f}</td>
                    <td>{s['month']['cons_unit']:,.2f}</td>
                </tr>
                """

            # Grand Total
            t = data['total']
            rows += f"""
            <tr style="background-color: #c8e6c9; font-weight: bold; border-top: 2px solid #4CAF50;">
                <td class="left">TOTAL GENERAL</td>
                <td>{t['day']['prod']:,.2f}</td>
                <td>{t['day']['horas']:,.2f}</td>
                <td>{t['day']['prod_hr']:,.2f}</td>
                <td>{t['month']['prod']:,.2f}</td>
                <td>{t.get('expected_to_date', 0.0):,.2f}</td>
                <td>{t.get('deviation', 0.0):,.2f}</td>
                <td>{t['month']['horas']:,.2f}</td>
                <td>{t['month']['prod_hr']:,.2f}</td>
                <td>{t['month']['comb']:,.2f}</td>
                <td>{t['month']['cons_hr']:,.2f}</td>
                <td>{t['month']['cons_unit']:,.2f}</td>
            </tr>
            """

            return f"""
            <h2>{title}</h2>
            <table>
                <tr>
                    <th rowspan="2">Equipo / UN</th>
                    <th colspan="3">Diario ({date_obj.strftime('%d/%m')})</th>
                    <th colspan="8">Acumulado Mes</th>
                </tr>
                <tr>
                    <th>Prod ({unit})</th>
                    <th>Horas</th>
                    <th>Prod/Hr</th>
                    <th>Prod ({unit})</th>
                    <th>Esperado</th>
                    <th>Desvío</th>
                    <th>Horas</th>
                    <th>Prod/Hr</th>
                    <th>Consumo (L)</th>
                    <th>L/Hr</th>
                    <th>L/{unit}</th>
                </tr>
                {rows}
            </table>
            """

        # Tabla 3
        # d3 now has 'units' and 'total'.
        rows_d3 = ""
        for un_block in d3['units']:
            rows_d3 += f"""
            <tr style="background-color: #e8f5e9; font-weight: bold;">
                <td class="left" colspan="6">{un_block['name']}</td>
            </tr>
            """
            for r in un_block['rows']:
                rows_d3 += f"""
                <tr>
                    <td class="left" style="padding-left: 20px;">{r['name']}</td>
                    <td>{r['day_hours']:,.2f}</td>
                    <td>{r['day_fuel']:,.2f}</td>
                    <td>{r['month_hours']:,.2f}</td>
                    <td>{r['month_fuel']:,.2f}</td>
                    <td>{r['avg_30']:,.2f}</td>
                </tr>
                """
            # Subtotal
            s = un_block['subtotal']
            rows_d3 += f"""
            <tr style="background-color: #f1f8e9; font-style: italic;">
                <td class="left">Subtotal {un_block['name']}</td>
                <td>{s['day_hours']:,.2f}</td>
                <td>{s['day_fuel']:,.2f}</td>
                <td>{s['month_hours']:,.2f}</td>
                <td>{s['month_fuel']:,.2f}</td>
                <td>{s['avg_30']:,.2f}</td>
            </tr>
            """
        
        # Grand Total
        t3 = d3['total']
        rows_d3 += f"""
        <tr style="background-color: #c8e6c9; font-weight: bold; border-top: 2px solid #4CAF50;">
            <td class="left">TOTAL GENERAL</td>
            <td>{t3['day_hours']:,.2f}</td>
            <td>{t3['day_fuel']:,.2f}</td>
            <td>{t3['month_hours']:,.2f}</td>
            <td>{t3['month_fuel']:,.2f}</td>
            <td>{t3['avg_30']:,.2f}</td>
        </tr>
        """

        table3 = f"""
        <h2>Otros Equipos (Soporte/Vial/Etc)</h2>
        <table>
            <tr>
                <th class="left">Equipo / UN</th>
                <th>Horas Diario</th>
                <th>Consumo Diario (L)</th>
                <th>Horas Mes</th>
                <th>Consumo Mes (L)</th>
                <th>Consumo Medio 30 días (L/Hr)</th>
            </tr>
            {rows_d3}
        </table>
        """

        # Tabla 4
        rows_no_op = ""
        for row in d4:
            rows_no_op += f"""
            <tr>
                <td class="left">{row['equipo']}</td>
                <td>{row['day']:,.2f}</td>
                <td>{row['month']:,.2f}</td>
                <td>{row.get('worked_month', 0.0):,.2f}</td>
                <td>{row.get('eff', 0.0):.1f}%</td>
            </tr>
            """
        
        table4 = f"""
        <h2>Horas No Operativas</h2>
        <table>
            <tr>
                <th class="left">Equipo</th>
                <th>Horas Diario</th>
                <th>Horas Mensual</th>
                <th>Horas Trabajadas Mes</th>
                <th>Efectividad (%)</th>
            </tr>
            {rows_no_op}
        </table>
        """

        html = f"""
        <html>
        <head>{style}</head>
        <body>
            <div class="header">
                <h1>Reporte Diario de Producción: {date_obj.strftime('%d/%m/%Y')}</h1>
            </div>
            {render_prod_table("1. Operación de Proceso", d1)}
            {render_prod_table("2. Carga", d_carga)}
            {render_prod_table("3. Chipeado", d2)}
            {table3}
            {table4}
            <p><small>Generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}</small></p>
        </body>
        </html>
        """
        return html
