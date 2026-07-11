from dataclasses import dataclass
import re
import unicodedata

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.permissions import BasePermission

from .models import Equipo, EquipoAlias


MAX_ALIAS_LENGTH = 120
_UNICODE_DASHES = dict.fromkeys(
    map(ord, "\u058a\u05be\u1400\u1806\u2010\u2011\u2012\u2013\u2014\u2015\u2e17\u2e1a\u2e3a\u2e3b\u2e40\u301c\u3030\u30a0\ufe31\ufe32\ufe58\ufe63\uff0d"),
    "-",
)
_SEPARATORS = re.compile(r"[\s-]+")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class NormalizedAlias:
    display: str
    normalized: str


@dataclass(frozen=True)
class AliasConfirmationResult:
    alias: EquipoAlias
    created: bool


@dataclass(frozen=True)
class AliasDeactivationResult:
    alias: EquipoAlias
    changed: bool


class AliasConflict(Exception):
    def __init__(self, candidates):
        super().__init__("El alias ya está activo en otro equipo")
        self.candidates = candidates


class CanManageEquipoAliases(BasePermission):
    message = "No tiene permiso para confirmar aliases de equipos."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (
                user.is_staff
                or user.is_superuser
                or user.has_perm("produccion.change_equipoalias")
            )
        )


class IsEquipoAliasAdmin(BasePermission):
    message = "Solo un administrador puede desactivar aliases de equipos."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or user.is_superuser)
        )


def score_equipo_match(*, equipo, normalized_query, aliases):
    fields = (
        ("patente", equipo.patente, 1.0, 0.8),
        ("alias", None, 1.0, 0.8),
        ("modelo_normalizado", equipo.modelo_normalizado, 0.95, 0.8),
        ("codigo_fg", equipo.codigo_fg, 0.95, 0.8),
        ("detalle", equipo.detalle, None, 0.6),
    )
    best = None
    for match_type, value, exact_score, partial_score in fields:
        values = aliases if match_type == "alias" else (value,)
        for candidate in values:
            if not candidate:
                continue
            try:
                candidate_key = normalize_alias(candidate).normalized
            except ValidationError:
                continue
            score = None
            if exact_score is not None and candidate_key == normalized_query:
                score = exact_score
            elif normalized_query in candidate_key:
                score = partial_score
            if score is not None and (best is None or score > best[1]):
                best = (match_type, score)
    return best


def effective_equipo_aliases(*, equipo, records):
    known_keys = {record.alias_normalizado for record in records}
    aliases = [record.alias_display for record in records if record.activo]
    active_keys = {
        record.alias_normalizado for record in records if record.activo
    }
    for value in equipo.aliases or []:
        if not isinstance(value, str):
            continue
        try:
            legacy = normalize_alias(value)
        except ValidationError:
            continue
        if legacy.normalized in known_keys or legacy.normalized in active_keys:
            continue
        aliases.append(legacy.display)
        active_keys.add(legacy.normalized)
    aliases.sort(key=lambda value: (value.casefold(), value))
    return aliases


def normalize_alias(value):
    if not isinstance(value, str):
        raise ValidationError("El alias debe ser texto")

    display = unicodedata.normalize("NFKC", value).translate(_UNICODE_DASHES)
    display = _WHITESPACE.sub(" ", display).strip()
    if not display:
        raise ValidationError("El alias no puede estar vacío")
    if len(display) > MAX_ALIAS_LENGTH:
        raise ValidationError(
            f"El alias no puede superar {MAX_ALIAS_LENGTH} caracteres"
        )

    comparable = unicodedata.normalize("NFKD", display.casefold())
    comparable = "".join(
        character
        for character in comparable
        if unicodedata.category(character) != "Mn"
    )
    normalized = _SEPARATORS.sub("", comparable)
    if not normalized:
        raise ValidationError("El alias no puede estar vacío")

    return NormalizedAlias(display=display, normalized=normalized)


def _conflict_candidates(normalized, exclude_equipo_id=None):
    conflicts = EquipoAlias.objects.filter(
        alias_activo_key=normalized,
        activo=True,
    )
    if exclude_equipo_id is not None:
        conflicts = conflicts.exclude(equipo_id=exclude_equipo_id)
    rows = conflicts.order_by("equipo__patente", "equipo_id").values(
        "equipo_id",
        "equipo__patente",
        "equipo__detalle",
    )
    return [
        {
            "equipo_id": row["equipo_id"],
            "patente": row["equipo__patente"],
            "detalle": row["equipo__detalle"],
        }
        for row in rows
    ]


def sync_equipo_alias_cache(equipo_id, removed_normalized_keys=()):
    aliases = list(
        EquipoAlias.objects.filter(equipo_id=equipo_id, activo=True)
        .order_by("alias_display", "id")
        .values_list("alias_display", flat=True)
    )
    active_keys = {
        normalize_alias(alias).normalized
        for alias in aliases
    }
    removed_keys = set(removed_normalized_keys)
    legacy_aliases = Equipo.objects.filter(pk=equipo_id).values_list(
        "aliases", flat=True
    ).get() or []
    for legacy_alias in legacy_aliases:
        if not isinstance(legacy_alias, str):
            continue
        try:
            legacy = normalize_alias(legacy_alias)
        except ValidationError:
            continue
        if legacy.normalized in active_keys or legacy.normalized in removed_keys:
            continue
        aliases.append(legacy.display)
        active_keys.add(legacy.normalized)
    aliases.sort(key=lambda value: (value.casefold(), value))
    Equipo.objects.filter(pk=equipo_id).update(aliases=aliases)
    return aliases


@transaction.atomic
def confirm_equipo_alias(
    *,
    equipo,
    alias,
    origen,
    confirmado_por,
    metadata=None,
):
    normalized = normalize_alias(alias)
    if origen not in EquipoAlias.Origen.values:
        raise ValidationError("Origen de alias inválido")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValidationError("metadata debe ser un objeto")

    Equipo.objects.select_for_update().get(pk=equipo.pk)
    conflicts = _conflict_candidates(normalized.normalized, equipo.pk)
    if conflicts:
        raise AliasConflict(conflicts)

    existing = EquipoAlias.objects.select_for_update().filter(
        equipo=equipo,
        alias_normalizado=normalized.normalized,
    ).first()
    if existing and existing.activo:
        sync_equipo_alias_cache(equipo.pk)
        return AliasConfirmationResult(alias=existing, created=False)

    now = timezone.now()
    if existing:
        existing.alias_display = normalized.display
        existing.alias_activo_key = normalized.normalized
        existing.activo = True
        existing.origen = origen
        existing.confirmado_por = confirmado_por
        existing.confirmado_at = now
        existing.metadata = metadata
        try:
            with transaction.atomic():
                existing.save(
                    update_fields=(
                        "alias_display",
                        "alias_activo_key",
                        "activo",
                        "origen",
                        "confirmado_por",
                        "confirmado_at",
                        "metadata",
                        "updated_at",
                    )
                )
        except IntegrityError as error:
            raise AliasConflict(
                _conflict_candidates(normalized.normalized, equipo.pk)
            ) from error
        alias_record = existing
        created = False
    else:
        try:
            with transaction.atomic():
                alias_record = EquipoAlias.objects.create(
                    equipo=equipo,
                    alias_display=normalized.display,
                    alias_normalizado=normalized.normalized,
                    alias_activo_key=normalized.normalized,
                    activo=True,
                    origen=origen,
                    confirmado_por=confirmado_por,
                    confirmado_at=now,
                    metadata=metadata,
                )
        except IntegrityError as error:
            raise AliasConflict(
                _conflict_candidates(normalized.normalized, equipo.pk)
            ) from error
        created = True

    sync_equipo_alias_cache(equipo.pk)
    return AliasConfirmationResult(alias=alias_record, created=created)


@transaction.atomic
def deactivate_equipo_alias(*, alias_record):
    locked = EquipoAlias.objects.select_for_update().get(pk=alias_record.pk)
    changed = locked.activo
    if changed:
        locked.activo = False
        locked.alias_activo_key = None
        locked.save(update_fields=("activo", "alias_activo_key", "updated_at"))
        sync_equipo_alias_cache(
            locked.equipo_id,
            removed_normalized_keys=(locked.alias_normalizado,),
        )
    alias_record.activo = locked.activo
    alias_record.alias_activo_key = locked.alias_activo_key
    return AliasDeactivationResult(alias=locked, changed=changed)
