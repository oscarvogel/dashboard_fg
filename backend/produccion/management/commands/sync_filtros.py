"""
sync_filtros — feature/equipo-aliases (2026-07-08)

Pull desde la API REST de Forestal Garuhapé (`/api/filtros`) y actualiza
`produccion.Equipo` con metadata derivada (modelo_normalizado,
ultima_sync_filtros).

Reglas firmes (Oscar 2026-07-08):
  - NO se crean Equipos nuevos desde la API. Si un equipo de la API no
    matchea por `detalle` exacto contra `produccion.Equipo.detalle`,
    se loguea como WARNING y se suma a la lista de huerfanos.
  - Solo se actualizan campos derivados:
      * modelo_normalizado (inferido desde `detalle`)
      * ultima_sync_filtros (timestamp)
  - `aliases` NO se toca (es input humano).

Uso:
  python manage.py sync_filtros
  python manage.py sync_filtros --dry-run

Auth de la API FG (orden de prioridad):
  1. Env vars del sistema (FG_API_URL, FG_USER, FG_PASSWORD)
  2. Archivo apuntado por env var FG_ENV_PATH (formato .env)
  3. Fallback: ./backend/.env (cwd del proceso)
"""

import os
import re
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

import urllib.request
import urllib.parse
import json

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from produccion.models import Equipo


# --------------------------------------------------------------------------
# Helpers — extracción de metadata desde el string `detalle`
# --------------------------------------------------------------------------

# Patrones para inferir modelo. Ajustables a medida que aparezcan equipos.
_RE_FABRICANTE_MODELO = re.compile(
    r'\b(JOHN DEERE|HYUNDAI|KOMATSU|PONSSE|PONSEE|CATERPILLAR|CAT|VOLVO|IVECO|'
    r'HITACHI|KOBELCO|NEW HOLLAND|HOLLAND|CAS|CHIPERA|BRUNO|PETERSON|SDLG|'
    r'BUFFALO|FELLER|FORWARDER|HARVESTER|MOTONIVELADORA|MOTONIVE|SKIDDER|'
    r'PROCESADOR|FELLER|FORWA|PROCE|CHIPE|MOTON|SKIDD|FELLE|GRUA)\b',
    re.IGNORECASE,
)

_RE_NORM_PREFIX = re.compile(r'^(F|WA)\b', re.IGNORECASE)


def inferir_modelo_normalizado(detalle: str) -> str:
    """Extrae marca+modelo del string `detalle` (ej:
    'Forwarder PONSSE BUFFALO KING - Nº 1' -> 'Ponsse Buffalo King').
    Si no puede, devuelve string vacio.
    """
    if not detalle:
        return ''
    s = detalle.strip()
    # Quito prefijo "Camion", "Forwarder", "Feller", etc. hasta el primer modelo conocido.
    matches = _RE_FABRICANTE_MODELO.findall(s)
    if not matches:
        return ''
    # Heuristica simple: tomar el primer fabricante + todo lo que sigue
    # hasta "-" o fin.
    first = matches[0]
    idx = s.upper().find(first.upper())
    if idx < 0:
        return ''
    tail = s[idx:].split('-')[0].strip().rstrip('-').rstrip()
    # Normalizar "PONSEE" -> "Ponsse" (typo comun en el sistema viejo).
    tail = re.sub(r'\bPONSEE\b', 'Ponsse', tail)
    tail = re.sub(r'\bJOHN DEERE\b', 'John Deere', tail, flags=re.IGNORECASE)
    return tail


# --------------------------------------------------------------------------
# Cliente a la API REST de FG (sin dependencias, igual a fg_client.py)
# --------------------------------------------------------------------------
#
# Resolution de credenciales (en orden de prioridad):
#   1. Variables del ambiente del sistema (os.environ)
#   2. Archivo apuntado por env var FG_ENV_PATH (sobrescribe cualquier valor previo)
#   3. .env en cwd del proceso (fallback razonable)
#
# Esto desacopla del filesystem de la Mac mini donde se desarrollo el feature.
# En server prod: o se exportan las variables, o se apunta FG_ENV_PATH a un
# archivo .env con FG_API_URL/FG_USER/FG_PASSWORD.


def load_fg_env():
    env = dict(os.environ)
    fg_env_path = os.environ.get('FG_ENV_PATH')
    if fg_env_path:
        p = Path(fg_env_path)
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                env[k.strip()] = v.strip().strip('"').strip("'")
    else:
        # Fallback al .env del cwd (no al path hardcoded de Oscar/Mac-mini)
        cwd_env = Path.cwd() / '.env'
        if cwd_env.exists():
            for line in cwd_env.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def fetch_filtros(api_url: str, jwt: str, start: str, end: str):
    url = f"{api_url.rstrip('/')}/api/filtros/?start_date={start}&end_date={end}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {jwt}'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fg_login(api_url: str, user: str, password: str):
    url = f"{api_url.rstrip('/')}/api/login-empleado/"
    body = json.dumps({'dni': user, 'password': password}).encode('utf-8')
    req = urllib.request.Request(
        url, data=body, headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    return payload['access']


# --------------------------------------------------------------------------
# Comando
# --------------------------------------------------------------------------


class Command(BaseCommand):
    help = 'Sync metadata desde la API REST de Forestal Garuhapé (/api/filtros).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Solo loguea lo que haría, no escribe la DB.',
        )
        parser.add_argument(
            '--days', type=int, default=30,
            help='Rango de fechas para /api/filtros (default: últimos 30 días).',
        )

    def handle(self, *args, **opts):
        dry = opts['dry_run']
        days = opts['days']

        env = load_fg_env()
        api_url = env.get('FG_API_URL')
        user = env.get('FG_USER')
        password = env.get('FG_PASSWORD')
        if not (api_url and user and password):
            self.stderr.write(self.style.ERROR(
                'Faltan FG_API_URL/FG_USER/FG_PASSWORD en ~/.openclaw/service-env/equipos-api-rest.env'
            ))
            sys.exit(1)

        end = date.today()
        start = end - timedelta(days=days)
        self.stdout.write(f"[sync_filtros] Login en {api_url}...")
        jwt = fg_login(api_url, user, password)
        self.stdout.write(self.style.SUCCESS("[sync_filtros] Login OK"))
        self.stdout.write(f"[sync_filtros] /api/filtros?start_date={start}&end_date={end}")
        filtros = fetch_filtros(api_url, jwt, start.isoformat(), end.isoformat())
        equipos_api = [e for e in (filtros.get('equipos') or []) if e]
        self.stdout.write(f"[sync_filtros] API devolvió {len(equipos_api)} equipos")

        # Matchear por detalle EXACTO (case-insensitive).
        # La API devuelve detalle_equipo limpio; la DB local puede tenerlo
        # con mayusculas distintas.
        # NOTE (2026-07-08): usamos .values_list/.values para bypass del bug
        # pre-existente `idUnidadNegocio` (db_column en el modelo es
        # inconsistente con la columna real en SQLite dev). Fix en otro PR.
        # Ver MEMORY.md / bitacora.
        existentes = {
            row['detalle'].strip(): row
            for row in Equipo.objects.values('id', 'detalle', 'modelo_normalizado', 'ultima_sync_filtros').iterator()
            if row.get('detalle')
        }
        existentes_lower = {k.lower(): v for k, v in existentes.items()}

        matched, huerfanos = [], []
        for detalle_api in equipos_api:
            d = detalle_api.strip()
            row = existentes.get(d) or existentes_lower.get(d.lower())
            if row:
                matched.append((row, d))
            else:
                huerfanos.append(d)

        self.stdout.write(self.style.SUCCESS(
            f"[sync_filtros] Matched: {len(matched)} | Huerfanos (no auto-creados): {len(huerfanos)}"
        ))

        if huerfanos:
            self.stdout.write(self.style.WARNING(
                "[sync_filtros] Huerfanos (no se crean; añadir manual si querés):"
            ))
            for h in huerfanos[:10]:
                self.stdout.write(f"  - {h!r}")
            if len(huerfanos) > 10:
                self.stdout.write(f"  ... y {len(huerfanos) - 10} más")

        if dry:
            self.stdout.write(self.style.WARNING("[sync_filtros] DRY-RUN, sin cambios."))
            return

        ahora = timezone.now()
        actualizados = 0
        with transaction.atomic():
            for row, detalle_api in matched:
                modelo = inferir_modelo_normalizado(detalle_api)
                updates = {}
                if modelo and modelo != (row.get('modelo_normalizado') or ''):
                    updates['modelo_normalizado'] = modelo
                if row.get('ultima_sync_filtros') != ahora:
                    updates['ultima_sync_filtros'] = ahora
                if updates:
                    Equipo.objects.filter(pk=row['id']).update(**updates)
                    actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f"[sync_filtros] Done. Actualizados: {actualizados}"
        ))
