from dataclasses import dataclass

from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError, OperationalError


FGPY_READONLY_ALIAS = "fgpy_readonly"

EQUIPMENT_RESOLVE_OK = "ok"
EQUIPMENT_RESOLVE_NEEDS_REVIEW = "needs_review"
EQUIPMENT_RESOLVE_UNRESOLVED = "unresolved"
EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE = "external_unavailable"

MAX_EQUIPMENT_CANDIDATES = 10


@dataclass(frozen=True)
class CatalogResult:
    configured: bool
    available: bool
    results: list
    error: str = ""

    def as_dict(self):
        return {
            "configured": self.configured,
            "available": self.available,
            "results": self.results,
            "error": self.error,
        }


@dataclass(frozen=True)
class EquipmentResolution:
    """Outcome of trying to resolve FGPY equipment for a bot payload.

    ``status`` is one of the EQUIPMENT_RESOLVE_* constants.
    ``external_id`` is always a sanitized string or ``None``; it MUST come
    from the FGPY read-only catalog and MUST NOT be derived from Garuhape
    models. ``candidates`` is a list of sanitized catalog dicts (already
    limited to MAX_EQUIPMENT_CANDIDATES) when status is
    ``needs_review``.
    """

    status: str
    external_id: str | None
    display: str
    code: str | None
    candidates: list
    error: str = ""

    def as_dict(self):
        return {
            "status": self.status,
            "external_id": self.external_id,
            "display": self.display,
            "code": self.code,
            "candidates": self.candidates,
            "error": self.error,
        }


def is_fgpy_readonly_configured():
    return (
        getattr(settings, "FGPY_READONLY_DB_ENABLED", False)
        and FGPY_READONLY_ALIAS in connections.databases
    )


def _equipment_row_to_dict(row):
    return {
        "organization_key": "forestal-paraguay",
        "external_id": str(row["id"]),
        "display": row["descripcion"] or "",
        "plate": row["patente"] or "",
        "code": row["codigo_kobo"] or "",
        "type": row["tipo_movil"] or "",
        "active": bool(row["activo"]),
    }


def list_active_equipment(limit=100):
    return search_equipment(query="", active_only=True, limit=limit)


def search_equipment(query="", active_only=True, limit=25):
    if not is_fgpy_readonly_configured():
        return CatalogResult(False, False, [], "not_configured")

    try:
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        limit = 25

    filters = []
    params = []
    if active_only:
        filters.append("e.activo = %s")
        params.append(1)

    text = str(query or "").strip()
    if text:
        text_filters = [
            "e.descripcion LIKE %s",
            "e.patente LIKE %s",
            "e.codigo_kobo LIKE %s",
        ]
        like = f"%{text}%"
        params.extend([like, like, like])
        if text.isdigit():
            text_filters.append("e.id = %s")
            params.append(int(text))
        filters.append("(" + " OR ".join(text_filters) + ")")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    sql = f"""
        SELECT
            e.id,
            e.descripcion,
            e.patente,
            e.codigo_kobo,
            e.activo,
            tm.descripcion AS tipo_movil
        FROM equipos e
        LEFT JOIN tipos_movil tm ON tm.id = e.tipo_movil_id
        {where}
        ORDER BY e.activo DESC, e.descripcion ASC, e.id ASC
        LIMIT %s
    """
    params.append(limit)

    try:
        with connections[FGPY_READONLY_ALIAS].cursor() as cursor:
            cursor.execute(sql, params)
            columns = [column[0] for column in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except (DatabaseError, OperationalError):
        return CatalogResult(True, False, [], "unavailable")

    return CatalogResult(True, True, [_equipment_row_to_dict(row) for row in rows])


def _sanitize_external_id(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sanitize_display(value):
    return str(value or "").strip()


def _sanitize_code(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _search_equipment_safe(query, limit=MAX_EQUIPMENT_CANDIDATES):
    """Wraps search_equipment so the bot never crashes if the external DB
    is misconfigured or unavailable. Returns the CatalogResult untouched.
    """
    return search_equipment(query=query, active_only=True, limit=limit)


def resolve_equipment(external_id=None, equipment_text=""):
    """Resolve an FGPY equipment reference for an incoming bot payload.

    Precedence:
      1. If ``external_id`` is provided, sanitize and return it as the
         authoritative reference (the bot confirmed an FGPY equipment).
      2. Otherwise, if ``equipment_text`` is provided, search the FGPY
         read-only catalog. A single match is accepted; zero or multiple
         matches require human review.
      3. With neither signal, the incident is unresolved.

    The function NEVER falls back to Garuhape models.
    """
    sanitized_id = _sanitize_external_id(external_id)
    sanitized_text = _sanitize_display(equipment_text)

    if sanitized_id:
        return EquipmentResolution(
            status=EQUIPMENT_RESOLVE_OK,
            external_id=sanitized_id,
            display="",
            code=None,
            candidates=[],
        )

    if not sanitized_text:
        return EquipmentResolution(
            status=EQUIPMENT_RESOLVE_UNRESOLVED,
            external_id=None,
            display="",
            code=None,
            candidates=[],
        )

    if not is_fgpy_readonly_configured():
        return EquipmentResolution(
            status=EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE,
            external_id=None,
            display="",
            code=None,
            candidates=[],
            error="not_configured",
        )

    catalog = _search_equipment_safe(sanitized_text, limit=MAX_EQUIPMENT_CANDIDATES)
    if not catalog.available:
        return EquipmentResolution(
            status=EQUIPMENT_RESOLVE_EXTERNAL_UNAVAILABLE,
            external_id=None,
            display="",
            code=None,
            candidates=[],
            error=catalog.error or "unavailable",
        )

    if len(catalog.results) == 1:
        match = catalog.results[0]
        return EquipmentResolution(
            status=EQUIPMENT_RESOLVE_OK,
            external_id=_sanitize_external_id(match.get("external_id")),
            display=_sanitize_display(match.get("display")),
            code=_sanitize_code(match.get("code")),
            candidates=[],
        )

    if not catalog.results:
        return EquipmentResolution(
            status=EQUIPMENT_RESOLVE_NEEDS_REVIEW,
            external_id=None,
            display="",
            code=None,
            candidates=[],
        )

    return EquipmentResolution(
        status=EQUIPMENT_RESOLVE_NEEDS_REVIEW,
        external_id=None,
        display="",
        code=None,
        candidates=catalog.results,
    )
