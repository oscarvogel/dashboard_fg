from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal
import hashlib
import hmac
import json
import os
import re
import unicodedata
import uuid

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import FileResponse
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from forestal_bot.models import (
    DailySummaryDelivery,
    DailySummaryGroup,
    DailySummaryRun,
    FUEL_ORGANIZATION_KEY,
    FUEL_ORIGIN_GROUP_KEY,
    FuelReport,
    FuelReportEvidence,
    FuelReportRevision,
    FuelReportSourceMessage,
    FgpyDriver,
    FgpyVehicle,
    UNIDENTIFIED_GROUP_NAME,
    WhatsAppGroup,
    WhatsAppMessage,
    WEIGHING_ORGANIZATION_KEY,
    WEIGHING_UNIT_CATALOG,
    WeighingMeasurement,
    WeighingMeasurementRevision,
    WeighingMovement,
)
from forestal_bot.permissions import (
    OpenClawBearerPermission,
    OpenClawOrAuthenticatedPermission,
    OpenClawOrJWTAuthentication,
)
from forestal_bot.serializers import (
    DailySummaryRunSerializer,
    FgpyDriverSerializer,
    FgpyVehicleSerializer,
    FuelReportSerializer,
    WhatsAppGroupSerializer,
    WhatsAppMessageSerializer,
    WhatsAppOwnerMessageSerializer,
    WeighingMeasurementSerializer,
    WeighingMovementSerializer,
    normalize_plate,
)


class DailySummaryListCreateView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request):
        queryset = DailySummaryRun.objects.prefetch_related(
            "groups", "deliveries"
        ).all()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        for name, value in (("date_from", date_from), ("date_to", date_to)):
            if value is not None:
                try:
                    parsed = serializers.DateField().run_validation(value)
                except serializers.ValidationError as exc:
                    raise serializers.ValidationError({name: exc.detail}) from exc
                queryset = queryset.filter(
                    **{f"operational_date__{'gte' if name == 'date_from' else 'lte'}": parsed}
                )
        if request.query_params.get("group_key"):
            queryset = queryset.filter(groups__group_key=request.query_params["group_key"])
        if request.query_params.get("status"):
            queryset = queryset.filter(status=request.query_params["status"])
        if request.query_params.get("channel"):
            queryset = queryset.filter(deliveries__channel=request.query_params["channel"])

        limit_value = request.query_params.get("limit", "100")
        try:
            limit = int(limit_value)
        except (TypeError, ValueError):
            limit = 0
        if limit <= 0:
            raise serializers.ValidationError(
                {"limit": ["A positive integer is required."]}
            )
        queryset = queryset.distinct()[: min(limit, 500)]
        return Response(DailySummaryRunSerializer(queryset, many=True).data)

    def post(self, request):
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError(
                {"non_field_errors": ["Expected a JSON object."]}
            )
        serializer = DailySummaryRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        groups = data.pop("groups")
        deliveries = data.pop("deliveries", [])
        idempotency_key = data.pop("idempotency_key")

        with transaction.atomic():
            run, created = DailySummaryRun.objects.update_or_create(
                idempotency_key=idempotency_key,
                defaults=data,
            )
            DailySummaryGroup.objects.filter(run=run).delete()
            DailySummaryGroup.objects.bulk_create(
                [DailySummaryGroup(run=run, **group) for group in groups]
            )
            for delivery in deliveries:
                identity = {
                    "run": run,
                    "channel": delivery.pop("channel"),
                    "recipient_name": delivery.pop("recipient_name"),
                }
                DailySummaryDelivery.objects.update_or_create(
                    **identity,
                    defaults=delivery,
                )

        run = DailySummaryRun.objects.prefetch_related("groups", "deliveries").get(pk=run.pk)
        return Response(
            {"created": created, "summary": DailySummaryRunSerializer(run).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DailySummaryDetailView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request, pk):
        try:
            run = DailySummaryRun.objects.prefetch_related(
                "groups", "deliveries"
            ).get(pk=pk)
        except DailySummaryRun.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(DailySummaryRunSerializer(run).data)


def movement_with_relations():
    return WeighingMovement.objects.prefetch_related(
        "measurements__revisions"
    )


def calculated_nets(movement):
    return WeighingMovementSerializer.nets_for(movement)


def validate_completion(movement):
    if not movement.official_scale:
        raise serializers.ValidationError(
            {"official_scale": ["Debe declararse la báscula oficial."]}
        )
    net = calculated_nets(movement).get(movement.official_scale)
    if net is None:
        raise serializers.ValidationError(
            {"measurements": ["Faltan tara o bruto de la báscula oficial."]}
        )
    if net <= 0:
        raise serializers.ValidationError(
            {"net_kg": ["El neto de un movimiento completo debe ser positivo."]}
        )
    return net


class WeighingMovementListCreateView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request):
        queryset = movement_with_relations().filter(
            organization_key=WEIGHING_ORGANIZATION_KEY
        )
        filters = {
            "organization_key": "organization_key",
            "plate": "plate_normalized__icontains",
            "driver": "driver_name__icontains",
            "status": "status",
            "origin_group_key": "origin_group_key",
        }
        for parameter, field in filters.items():
            value = request.query_params.get(parameter)
            if value:
                if parameter == "plate":
                    value = normalize_plate(value)
                queryset = queryset.filter(**{field: value})
        for parameter, lookup in (
            ("date_from", "operational_date__gte"),
            ("date_to", "operational_date__lte"),
        ):
            value = request.query_params.get(parameter)
            if value:
                try:
                    parsed = serializers.DateField().run_validation(value)
                except serializers.ValidationError as exc:
                    raise serializers.ValidationError({parameter: exc.detail}) from exc
                queryset = queryset.filter(**{lookup: parsed})
        return Response(WeighingMovementSerializer(queryset, many=True).data)

    def post(self, request):
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError(
                {"non_field_errors": ["Se esperaba un objeto JSON."]}
            )
        serializer = WeighingMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        asserted_net = data.pop("net_kg", None)
        idempotency_key = data.pop("idempotency_key")
        data["plate_normalized"] = normalize_plate(data.get("plate_original", ""))
        with transaction.atomic():
            movement = WeighingMovement.objects.select_for_update().filter(
                idempotency_key=idempotency_key
            ).first()
            created = movement is None
            if movement is None:
                movement = WeighingMovement.objects.create(
                    idempotency_key=idempotency_key, **data
                )
            else:
                if data.get("status") == "pendiente" and movement.status != "pendiente":
                    data["status"] = movement.status
                for field, value in data.items():
                    setattr(movement, field, value)
                movement.save()
            movement = movement_with_relations().get(pk=movement.pk)
            if asserted_net is not None:
                if not movement.official_scale:
                    raise serializers.ValidationError(
                        {"net_kg": ["Requiere una báscula oficial declarada."]}
                    )
                calculated = calculated_nets(movement).get(movement.official_scale)
                if calculated is None or asserted_net != calculated:
                    raise serializers.ValidationError(
                        {"net_kg": ["No coincide con bruto menos tara."]}
                    )
            if movement.status == "completo":
                validate_completion(movement)
        return Response(
            {
                "created": created,
                "movement": WeighingMovementSerializer(movement).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WeighingMovementDetailView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request, pk):
        try:
            movement = movement_with_relations().get(
                pk=pk, organization_key=WEIGHING_ORGANIZATION_KEY
            )
        except WeighingMovement.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(WeighingMovementSerializer(movement).data)


class WeighingMeasurementUpsertView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def post(self, request, pk):
        try:
            movement = WeighingMovement.objects.get(
                pk=pk, organization_key=WEIGHING_ORGANIZATION_KEY
            )
        except WeighingMovement.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = WeighingMeasurementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        asserted_net = data.pop("net_kg", None)
        idempotency_key = data["idempotency_key"]

        with transaction.atomic():
            replay = WeighingMeasurementRevision.objects.select_related(
                "measurement"
            ).filter(idempotency_key=idempotency_key).first()
            if replay:
                expected = {
                    key: data.get(key, "")
                    for key in (
                        "weight_kg",
                        "source",
                        "evidence_id",
                        "message_id",
                        "measured_at",
                        "correction_reason",
                    )
                }
                actual = {key: getattr(replay, key) for key in expected}
                if (
                    expected != actual
                    or replay.measurement.movement_id != movement.pk
                    or replay.measurement.scale != data["scale"]
                    or replay.measurement.kind != data["kind"]
                ):
                    return Response(
                        {"detail": "idempotency_key ya fue usada con otro contenido."},
                        status=status.HTTP_409_CONFLICT,
                    )
                measurement = replay.measurement
                created = False
            else:
                identity = {
                    "movement": movement,
                    "scale": data["scale"],
                    "kind": data["kind"],
                }
                measurement = WeighingMeasurement.objects.select_for_update().filter(
                    **identity
                ).first()
                created = measurement is None
                if measurement is None:
                    measurement = WeighingMeasurement(**identity)
                measurement.idempotency_key = idempotency_key
                for field in (
                    "weight_kg",
                    "source",
                    "evidence_id",
                    "message_id",
                    "measured_at",
                    "correction_reason",
                ):
                    setattr(measurement, field, data.get(field, ""))
                measurement.save()
                revision = measurement.revisions.count() + 1
                WeighingMeasurementRevision.objects.create(
                    measurement=measurement,
                    revision=revision,
                    **{
                        field: getattr(measurement, field)
                        for field in (
                            "idempotency_key",
                            "weight_kg",
                            "source",
                            "evidence_id",
                            "message_id",
                            "measured_at",
                            "correction_reason",
                        )
                    },
                )

            refreshed = movement_with_relations().get(pk=movement.pk)
            nets = calculated_nets(refreshed)
            calculated = nets.get(data["scale"])
            if asserted_net is not None and (
                calculated is None or asserted_net != calculated
            ):
                raise serializers.ValidationError(
                    {"net_kg": ["No coincide con bruto menos tara."]}
                )
            if refreshed.status == "completo":
                validate_completion(refreshed)
            if (
                refreshed.status == "pendiente"
                and refreshed.official_scale
                and nets.get(refreshed.official_scale, 0) > 0
            ):
                refreshed.status = "completo"
                refreshed.save(update_fields=["status", "updated_at"])
                refreshed = movement_with_relations().get(pk=movement.pk)

        return Response(
            {
                "created": created,
                "replayed": replay is not None,
                "measurement": WeighingMeasurementSerializer(measurement).data,
                "movement": WeighingMovementSerializer(refreshed).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WeighingMovementCompleteView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def post(self, request, pk):
        try:
            movement = movement_with_relations().get(
                pk=pk, organization_key=WEIGHING_ORGANIZATION_KEY
            )
        except WeighingMovement.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        official_scale = request.data.get("official_scale", movement.official_scale)
        if official_scale:
            try:
                movement.official_scale = serializers.ChoiceField(
                    choices=("felber", "forestal_paraguay", "otro")
                ).run_validation(official_scale)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError(
                    {"official_scale": exc.detail}
                ) from exc
        validate_completion(movement)
        movement.status = "completo"
        movement.save(update_fields=["official_scale", "status", "updated_at"])
        movement = movement_with_relations().get(pk=movement.pk)
        return Response(WeighingMovementSerializer(movement).data)


def period_start(value, period):
    if period == "daily":
        return value
    if period == "weekly":
        return value - timedelta(days=value.weekday())
    return value.replace(day=1)


def empty_weighing_totals():
    return {
        "complete_count": 0,
        "pending_count": 0,
        "observed_count": 0,
        "cancelled_count": 0,
        "effective_net_kg": 0,
        "effective_net_tonnes": "0.000",
        "scale_totals_kg": {},
        "differences_kg": {
            "felber_minus_forestal_paraguay": {
                "tara": 0,
                "bruto": 0,
                "neto": 0,
            }
        },
        "included_movements": [],
        "excluded_movements": [],
    }


def build_weighing_buckets(movements, period):
    buckets = {}
    for movement in movements:
        key = period_start(movement.operational_date, period)
        bucket = buckets.setdefault(
            key,
            {"period_start": key, **empty_weighing_totals()},
        )
        status_key = {
            "completo": "complete_count",
            "pendiente": "pending_count",
            "observado": "observed_count",
            "anulado": "cancelled_count",
        }[movement.status]
        bucket[status_key] += 1
        if movement.status != "completo":
            bucket["excluded_movements"].append(str(movement.pk))
            continue
        nets = calculated_nets(movement)
        official_net = nets.get(movement.official_scale)
        if official_net is None or official_net <= 0:
            bucket["excluded_movements"].append(str(movement.pk))
            continue
        bucket["included_movements"].append(str(movement.pk))
        bucket["effective_net_kg"] += official_net
        for scale, net in nets.items():
            bucket["scale_totals_kg"][scale] = (
                bucket["scale_totals_kg"].get(scale, 0) + net
            )
        values = {
            (item.scale, item.kind): item.weight_kg
            for item in movement.measurements.all()
        }
        differences = bucket["differences_kg"][
            "felber_minus_forestal_paraguay"
        ]
        for kind in ("tara", "bruto"):
            if ("felber", kind) in values and (
                "forestal_paraguay",
                kind,
            ) in values:
                differences[kind] += (
                    values[("felber", kind)]
                    - values[("forestal_paraguay", kind)]
                )
        if "felber" in nets and "forestal_paraguay" in nets:
            differences["neto"] += (
                nets["felber"] - nets["forestal_paraguay"]
            )

    results = []
    for key in sorted(buckets):
        bucket = buckets[key]
        bucket["effective_net_tonnes"] = weighing_tonnes(
            bucket["effective_net_kg"]
        )
        results.append(bucket)
    return results


def weighing_tonnes(weight_kg):
    return str(
        (Decimal(weight_kg) / Decimal("1000")).quantize(Decimal("0.001"))
    )


def aggregate_weighing_buckets(buckets):
    totals = empty_weighing_totals()
    for bucket in buckets:
        for field in (
            "complete_count",
            "pending_count",
            "observed_count",
            "cancelled_count",
            "effective_net_kg",
        ):
            totals[field] += bucket[field]
        for scale, weight in bucket["scale_totals_kg"].items():
            totals["scale_totals_kg"][scale] = (
                totals["scale_totals_kg"].get(scale, 0) + weight
            )
        target_differences = totals["differences_kg"][
            "felber_minus_forestal_paraguay"
        ]
        source_differences = bucket["differences_kg"][
            "felber_minus_forestal_paraguay"
        ]
        for kind in ("tara", "bruto", "neto"):
            target_differences[kind] += source_differences[kind]
        totals["included_movements"].extend(bucket["included_movements"])
        totals["excluded_movements"].extend(bucket["excluded_movements"])
    totals["effective_net_tonnes"] = weighing_tonnes(
        totals["effective_net_kg"]
    )
    return totals


class WeighingSummaryView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        if period not in {"daily", "weekly", "monthly"}:
            raise serializers.ValidationError(
                {"period": ["Valores permitidos: daily, weekly, monthly."]}
            )
        group_by = request.query_params.get("group_by")
        if group_by not in (None, "", "origin_group_key"):
            raise serializers.ValidationError(
                {
                    "group_by": [
                        "El único valor permitido es origin_group_key."
                    ]
                }
            )
        queryset = movement_with_relations().filter(
            organization_key=WEIGHING_ORGANIZATION_KEY
        )
        parsed_dates = {}
        for parameter, lookup in (
            ("date_from", "operational_date__gte"),
            ("date_to", "operational_date__lte"),
        ):
            value = request.query_params.get(parameter)
            if value:
                try:
                    value = serializers.DateField().run_validation(value)
                except serializers.ValidationError as exc:
                    raise serializers.ValidationError({parameter: exc.detail}) from exc
                parsed_dates[parameter] = value
                queryset = queryset.filter(**{lookup: value})
        origin_group_key = request.query_params.get("origin_group_key")
        if origin_group_key:
            queryset = queryset.filter(origin_group_key=origin_group_key)
        if group_by != "origin_group_key":
            return Response(
                {
                    "period": period,
                    "results": build_weighing_buckets(queryset, period),
                }
            )

        selected_unit_keys = (
            [origin_group_key]
            if origin_group_key in WEIGHING_UNIT_CATALOG
            else list(WEIGHING_UNIT_CATALOG)
            if not origin_group_key
            else []
        )
        movements_by_unit = {key: [] for key in selected_unit_keys}
        for movement in queryset:
            if movement.origin_group_key in movements_by_unit:
                movements_by_unit[movement.origin_group_key].append(movement)

        units = []
        for unit_key in selected_unit_keys:
            buckets = build_weighing_buckets(
                movements_by_unit[unit_key], period
            )
            units.append(
                {
                    "origin_group_key": unit_key,
                    "display_name": WEIGHING_UNIT_CATALOG[unit_key][
                        "display_name"
                    ],
                    **aggregate_weighing_buckets(buckets),
                    "buckets": buckets,
                }
            )
        total_buckets = []
        for unit in units:
            total_buckets.extend(unit["buckets"])
        return Response(
            {
                "organization_key": WEIGHING_ORGANIZATION_KEY,
                "period": period,
                "date_from": parsed_dates.get("date_from"),
                "date_to": parsed_dates.get("date_to"),
                "units": units,
                "totals": aggregate_weighing_buckets(total_buckets),
            }
        )


def resolve_message_group(validated_data):
    account_id = validated_data["account_id"]
    group_jid = validated_data["group_jid"]
    incoming_name = validated_data.get("group_name", "").strip()
    group, _ = WhatsAppGroup.objects.get_or_create(
        account_id=account_id,
        jid=group_jid,
        defaults={"name": incoming_name or UNIDENTIFIED_GROUP_NAME},
    )
    if incoming_name and group.name in ("", UNIDENTIFIED_GROUP_NAME):
        group.name = incoming_name
        group.save(update_fields=["name", "updated_at"])
    return group


def prepare_transcription_defaults(defaults):
    if defaults.get("transcription_status") == "completed":
        defaults["transcribed_at"] = timezone.now()
        defaults["transcription_error"] = ""
    return defaults


def prepare_image_analysis_defaults(defaults):
    if defaults.get("image_analysis_status") == "completed":
        defaults["image_analyzed_at"] = timezone.now()
        defaults["image_analysis_error"] = ""
    return defaults


def update_existing_transcription(message, validated_data):
    if message.transcription_status == "completed" and message.transcription:
        return

    incoming_status = validated_data.get("transcription_status", "")
    update_fields = []
    if incoming_status in ("pending", "processing"):
        message.transcription_status = incoming_status
        update_fields.append("transcription_status")
    elif incoming_status == "failed":
        message.transcription_status = "failed"
        message.transcription_error = validated_data.get("transcription_error", "")
        message.transcribed_at = None
        update_fields.extend(
            ["transcription_status", "transcription_error", "transcribed_at"]
        )
    elif incoming_status == "completed":
        message.transcription = validated_data["transcription"]
        message.transcription_status = "completed"
        message.transcription_error = ""
        message.transcribed_at = timezone.now()
        update_fields.extend(
            [
                "transcription",
                "transcription_status",
                "transcription_error",
                "transcribed_at",
            ]
        )
    if update_fields:
        message.save(update_fields=update_fields)


def update_existing_image_analysis(message, validated_data):
    if message.image_analysis_status == "completed" and message.image_description:
        return

    incoming_status = validated_data.get("image_analysis_status", "")
    update_fields = []
    if incoming_status in ("pending", "processing"):
        message.image_analysis_status = incoming_status
        update_fields.append("image_analysis_status")
    elif incoming_status == "failed":
        message.image_analysis_status = "failed"
        message.image_analysis_error = validated_data.get("image_analysis_error", "")
        message.image_analyzed_at = None
        update_fields.extend(
            ["image_analysis_status", "image_analysis_error", "image_analyzed_at"]
        )
    elif incoming_status == "completed":
        message.image_description = validated_data["image_description"]
        message.image_analysis_status = "completed"
        message.image_analysis_error = ""
        message.image_analyzed_at = timezone.now()
        update_fields.extend(
            [
                "image_description",
                "image_analysis_status",
                "image_analysis_error",
                "image_analyzed_at",
            ]
        )
    if update_fields:
        message.save(update_fields=update_fields)


class WhatsAppMessageCreateView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def post(self, request):
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError(
                {"non_field_errors": ["Expected a JSON object."]}
            )
        raw_json = dict(request.data)
        serializer = WhatsAppMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = dict(serializer.validated_data)
        identity = {
            field: validated_data.pop(field)
            for field in ("account_id", "group_jid", "message_id")
        }
        defaults = prepare_image_analysis_defaults(
            prepare_transcription_defaults(
                {**validated_data, "raw_json": raw_json}
            )
        )

        try:
            with transaction.atomic():
                group = resolve_message_group({**identity, **validated_data})
                message, created = WhatsAppMessage.objects.get_or_create(
                    **identity,
                    defaults={**defaults, "group": group},
                )
                if not created and message.group_id is None:
                    message.group = group
                    message.save(update_fields=["group"])
                if not created:
                    update_existing_transcription(message, validated_data)
                    update_existing_image_analysis(message, validated_data)
        except IntegrityError:
            message = WhatsAppMessage.objects.get(**identity)
            created = False

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                "created": created,
                "message": WhatsAppMessageSerializer(message).data,
            },
            status=response_status,
        )


class WhatsAppMessageRecentView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request):
        queryset = WhatsAppMessage.objects.select_related("group").order_by(
            "-timestamp", "-created_at"
        )

        group_jid = request.query_params.get("group_jid")
        if group_jid is not None:
            queryset = queryset.filter(group_jid=group_jid)

        since = request.query_params.get("since")
        if since is not None:
            try:
                since = serializers.DateTimeField().run_validation(since)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"since": exc.detail}) from exc
            queryset = queryset.filter(timestamp__gte=since)

        limit_value = request.query_params.get("limit", "100")
        try:
            limit = int(limit_value)
        except (TypeError, ValueError):
            limit = 0
        if limit <= 0:
            raise serializers.ValidationError(
                {"limit": ["A positive integer is required."]}
            )
        limit = min(limit, 500)

        return Response(WhatsAppMessageSerializer(queryset[:limit], many=True).data)


class WhatsAppGroupListCreateView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def get(self, request):
        queryset = WhatsAppGroup.objects.all()
        account_id = request.query_params.get("account_id")
        if account_id is not None:
            queryset = queryset.filter(account_id=account_id)
        active = request.query_params.get("active")
        if active is not None:
            try:
                active = serializers.BooleanField().run_validation(active)
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"active": exc.detail}) from exc
            queryset = queryset.filter(active=active)
        return Response(WhatsAppGroupSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = WhatsAppGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WhatsAppGroupDetailView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def patch(self, request, pk):
        try:
            group = WhatsAppGroup.objects.get(pk=pk)
        except WhatsAppGroup.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = WhatsAppGroupSerializer(group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class WhatsAppOwnerMessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = WhatsAppMessage.objects.select_related("group").order_by(
            "-timestamp", "-created_at"
        )
        account_id = request.query_params.get("account_id")
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        limit_value = request.query_params.get("limit", "100")
        try:
            limit = int(limit_value)
        except (TypeError, ValueError):
            limit = 0
        if limit <= 0:
            raise serializers.ValidationError(
                {"limit": ["A positive integer is required."]}
            )
        limit = min(limit, 500)
        return Response(
            WhatsAppOwnerMessageSerializer(queryset[:limit], many=True).data
        )


FUEL_CRITICAL_FIELDS = ("vehicle", "liters", "odometer_total")
FUEL_CONFIDENCE_FIELDS = {
    "vehicle",
    "driver",
    "liters",
    "odometer_total",
    "odometer_partial",
    "event_at",
    "station",
    "receipt_number",
    "amount",
    "unit_price",
}
FUEL_INCONSISTENCY_CODES = {
    "missing_vehicle",
    "missing_liters",
    "missing_odometer",
    "low_confidence_vehicle",
    "low_confidence_liters",
    "low_confidence_odometer",
    "odometer_regression",
    "duplicate_receipt",
    "duplicate_evidence",
    "possible_duplicate_fuel_event",
    "event_date_mismatch",
    "possible_capacity_exceeded",
}
FUEL_EDITABLE_FIELDS = {
    "event_at",
    "vehicle",
    "driver",
    "liters",
    "odometer_total",
    "odometer_partial",
    "station",
    "receipt_number",
    "fuel_type",
    "amount",
    "currency",
    "unit_price",
    "review_notes",
}


class FuelReportPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


def _fuel_scoped_queryset():
    return FuelReport.objects.filter(
        organization_key=FUEL_ORGANIZATION_KEY,
        origin_group_key=FUEL_ORIGIN_GROUP_KEY,
    ).select_related("vehicle", "driver", "reviewed_by")


def _parse_json_value(data, key, default):
    value = data.get(key, default)
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise serializers.ValidationError({key: ["Invalid JSON."]}) from exc
    return value


def _validate_scope(data):
    organization = data.get("organization_key")
    group = data.get("origin_group_key")
    if organization != FUEL_ORGANIZATION_KEY:
        raise serializers.ValidationError(
            {"organization_key": ["Only forestal-paraguay is accepted."]}
        )
    if group != FUEL_ORIGIN_GROUP_KEY:
        raise serializers.ValidationError(
            {"origin_group_key": ["Only choferes-fgpy is accepted."]}
        )


def _actual_mime(upload):
    header = upload.read(16)
    upload.seek(0)
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if header.startswith(b"%PDF-"):
        return "application/pdf", ".pdf"
    raise serializers.ValidationError(
        {"evidence_files": ["Only valid JPEG, PNG, WebP or PDF files are accepted."]}
    )


def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "pk"):
        return value.pk
    return str(value)


def _derive_fuel_inconsistencies(values, proposed):
    codes = [code for code in proposed if code in FUEL_INCONSISTENCY_CODES]
    confidence = values.get("field_confidence") or {}
    threshold = Decimal(str(getattr(settings, "FUEL_FIELD_CONFIDENCE_THRESHOLD", "0.80")))
    missing_codes = {
        "vehicle": "missing_vehicle",
        "liters": "missing_liters",
        "odometer_total": "missing_odometer",
    }
    low_codes = {
        "vehicle": "low_confidence_vehicle",
        "liters": "low_confidence_liters",
        "odometer_total": "low_confidence_odometer",
    }
    for field in FUEL_CRITICAL_FIELDS:
        if values.get(field) in (None, ""):
            codes.append(missing_codes[field])
        field_value = confidence.get(field)
        if field_value is not None and Decimal(str(field_value)) < threshold:
            codes.append(low_codes[field])

    vehicle = values.get("vehicle")
    odometer = values.get("odometer_total")
    event_at = values.get("event_at")
    if vehicle and odometer is not None:
        previous = (
            _fuel_scoped_queryset()
            .filter(vehicle=vehicle, status__in=["confirmed", "corrected"])
            .exclude(odometer_total=None)
        )
        if event_at:
            previous = previous.filter(Q(event_at__lt=event_at) | Q(event_at=None))
        previous = previous.order_by("-event_at", "-created_at").first()
        if previous and odometer < previous.odometer_total:
            codes.append("odometer_regression")

    receipt = values.get("receipt_number", "").strip()
    if receipt and _fuel_scoped_queryset().filter(receipt_number=receipt).exists():
        codes.append("duplicate_receipt")
    if vehicle and event_at and _fuel_scoped_queryset().filter(
        vehicle=vehicle,
        event_at__date=event_at.date(),
        liters=values.get("liters"),
    ).exists():
        codes.append("possible_duplicate_fuel_event")
    return list(dict.fromkeys(codes))


def _normalize_catalog_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def _catalog_source_message(raw_id):
    if raw_id in (None, ""):
        return None
    try:
        return WhatsAppMessage.objects.get(
            pk=raw_id, group_jid="120363420163225425@g.us"
        )
    except WhatsAppMessage.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"initial_source_message": ["Must exist in Choferes FGPY."]}
        ) from exc


def _protected_sender_identifier(raw_value):
    value = str(raw_value or "").strip()
    if not value:
        return ""
    key = getattr(settings, "FGPY_IDENTITY_HASH_KEY", "")
    if not key:
        raise serializers.ValidationError(
            {
                "whatsapp_sender_identifier": [
                    "Protected identity storage is not configured."
                ]
            }
        )
    return hmac.new(
        key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _catalog_existing_by_key(model, proposal_key):
    return model.objects.filter(
        organization_key=FUEL_ORGANIZATION_KEY, proposal_key=proposal_key
    ).first()


def _catalog_identity_matches(instance, values, kind):
    fields = (
        (
            "original_plate",
            "normalized_plate",
            "internal_code",
            "description",
            "make",
            "model",
        )
        if kind == "vehicle"
        else (
            "reported_name",
            "normalized_name",
            "external_identifier",
            "whatsapp_sender_identifier_hash",
        )
    )
    return (
        instance.initial_source_message_id
        == getattr(values.get("initial_source_message"), "pk", None)
        and all(getattr(instance, field) == values.get(field, "") for field in fields)
    )


def _catalog_idempotency_response(instance, values, kind, serializer_class):
    if _catalog_identity_matches(instance, values, kind):
        return Response(serializer_class(instance).data, status=status.HTTP_200_OK)
    return Response(
        {"detail": "The proposal key is already associated with different data."},
        status=status.HTTP_409_CONFLICT,
    )


class FgpyCatalogListCreateView(APIView):
    authentication_classes = [OpenClawOrJWTAuthentication]
    permission_classes = [OpenClawOrAuthenticatedPermission]
    model = None
    serializer_class = None
    kind = None

    def get(self, request):
        queryset = self.model.objects.filter(organization_key=FUEL_ORGANIZATION_KEY)
        status_value = request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)
        active = request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(
                active=serializers.BooleanField().run_validation(active)
            )
        query = request.query_params.get("q", "").strip()
        if query:
            if self.kind == "vehicle":
                queryset = queryset.filter(
                    Q(original_plate__icontains=query)
                    | Q(normalized_plate__icontains=_normalize_catalog_text(query).replace(" ", ""))
                    | Q(internal_code__icontains=query)
                    | Q(description__icontains=query)
                )
            else:
                queryset = queryset.filter(
                    Q(reported_name__icontains=query)
                    | Q(normalized_name__icontains=_normalize_catalog_text(query))
                    | Q(external_identifier__icontains=query)
                )
        return Response(self.serializer_class(queryset, many=True).data)

    def post(self, request):
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError({"non_field_errors": ["Expected an object."]})
        if request.data.get("organization_key") != FUEL_ORGANIZATION_KEY:
            raise serializers.ValidationError(
                {"organization_key": ["Only forestal-paraguay is accepted."]}
            )
        is_bot = request.auth == "openclaw"
        proposal_key = str(request.data.get("proposal_key", "")).strip()
        if is_bot and not proposal_key:
            raise serializers.ValidationError(
                {"proposal_key": ["The bot must provide an idempotency key."]}
            )
        source_message = _catalog_source_message(
            request.data.get("initial_source_message")
        )
        common = {
            "organization_key": FUEL_ORGANIZATION_KEY,
            "proposal_key": proposal_key or None,
            "initial_source_message": source_message,
            "created_via": "bot" if is_bot else "user",
            "created_by": None if is_bot else request.user,
            "status": "pending",
            "confirmed_aliases": [],
        }
        if self.kind == "vehicle":
            original = str(request.data.get("original_plate", "")).strip()
            values = {
                **common,
                "original_plate": original,
                "normalized_plate": _normalize_catalog_text(original).replace(" ", ""),
                "internal_code": str(request.data.get("internal_code", "")).strip(),
                "description": str(request.data.get("description", "")).strip(),
                "make": str(request.data.get("make", "")).strip(),
                "model": str(request.data.get("model", "")).strip(),
            }
            if not original and not values["description"] and not values["internal_code"]:
                raise serializers.ValidationError(
                    {"original_plate": ["Provide a plate, internal code or description."]}
                )
        else:
            reported_name = str(request.data.get("reported_name", "")).strip()
            if not reported_name:
                raise serializers.ValidationError(
                    {"reported_name": ["This field is required."]}
                )
            values = {
                **common,
                "reported_name": reported_name,
                "normalized_name": _normalize_catalog_text(reported_name),
                "external_identifier": str(request.data.get("external_identifier", "")).strip(),
                "whatsapp_sender_identifier_hash": _protected_sender_identifier(
                    request.data.get("whatsapp_sender_identifier", "")
                ),
            }
        if proposal_key:
            existing = _catalog_existing_by_key(self.model, proposal_key)
            if existing:
                return _catalog_idempotency_response(
                    existing, values, self.kind, self.serializer_class
                )
        try:
            with transaction.atomic():
                instance = self.model.objects.create(**values)
        except IntegrityError:
            if not proposal_key:
                raise
            winner = _catalog_existing_by_key(self.model, proposal_key)
            if winner is None:
                raise
            return _catalog_idempotency_response(
                winner, values, self.kind, self.serializer_class
            )
        return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)


class FgpyCatalogDetailView(APIView):
    authentication_classes = [OpenClawOrJWTAuthentication]
    permission_classes = [OpenClawOrAuthenticatedPermission]
    model = None
    serializer_class = None
    kind = None

    def patch(self, request, pk):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "A dashboard user is required."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            instance = self.model.objects.get(
                pk=pk, organization_key=FUEL_ORGANIZATION_KEY
            )
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        action = request.data.get("action", "correct")
        if action not in {"correct", "confirm", "deactivate"}:
            raise serializers.ValidationError({"action": ["Invalid action."]})
        allowed = (
            {"original_plate", "internal_code", "description", "make", "model"}
            if self.kind == "vehicle"
            else {"reported_name", "external_identifier"}
        )
        changes = request.data.get("changes", {})
        if not isinstance(changes, Mapping) or set(changes) - allowed:
            raise serializers.ValidationError({"changes": ["Contains unsupported fields."]})
        for field_name, value in changes.items():
            setattr(instance, field_name, str(value or "").strip())
        if self.kind == "vehicle" and "original_plate" in changes:
            instance.normalized_plate = _normalize_catalog_text(
                instance.original_plate
            ).replace(" ", "")
        if self.kind == "driver" and "reported_name" in changes:
            instance.normalized_name = _normalize_catalog_text(instance.reported_name)
        if action == "confirm":
            aliases = request.data.get("confirmed_aliases", [])
            if not isinstance(aliases, list) or any(not isinstance(x, str) for x in aliases):
                raise serializers.ValidationError(
                    {"confirmed_aliases": ["Expected a list of strings."]}
                )
            if self.kind == "vehicle" and not instance.normalized_plate:
                raise serializers.ValidationError(
                    {"original_plate": ["A normalized plate is required to confirm."]}
                )
            instance.confirmed_aliases = list(dict.fromkeys(x.strip() for x in aliases if x.strip()))
            instance.status = "confirmed"
            instance.confirmed_by = request.user
            instance.confirmed_at = timezone.now()
        elif action == "deactivate":
            instance.status = "inactive"
            instance.active = False
        try:
            instance.save()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"non_field_errors": ["A confirmed entry already uses that identity."]}
            ) from exc
        return Response(self.serializer_class(instance).data)


class FgpyVehicleListCreateView(FgpyCatalogListCreateView):
    model = FgpyVehicle
    serializer_class = FgpyVehicleSerializer
    kind = "vehicle"


class FgpyVehicleDetailView(FgpyCatalogDetailView):
    model = FgpyVehicle
    serializer_class = FgpyVehicleSerializer
    kind = "vehicle"


class FgpyDriverListCreateView(FgpyCatalogListCreateView):
    model = FgpyDriver
    serializer_class = FgpyDriverSerializer
    kind = "driver"


class FgpyDriverDetailView(FgpyCatalogDetailView):
    model = FgpyDriver
    serializer_class = FgpyDriverSerializer
    kind = "driver"


def _fuel_existing_by_key(idempotency_key):
    return _fuel_scoped_queryset().filter(idempotency_key=idempotency_key).first()


def _fuel_idempotency_response(report, source_ids, request):
    existing_ids = set(report.source_links.values_list("message_id", flat=True))
    if existing_ids != set(source_ids):
        return Response(
            {"detail": "The idempotency key is already associated with other messages."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(
        FuelReportSerializer(report, context={"request": request}).data,
        status=status.HTTP_200_OK,
    )


def _delete_stored_files(names):
    for name in names:
        try:
            default_storage.delete(name)
        except Exception:
            # Preserve the original database/storage exception. Operators can
            # still detect a storage cleanup failure without exposing paths.
            continue


class FuelReportListCreateView(APIView):
    authentication_classes = [OpenClawOrJWTAuthentication]
    permission_classes = [OpenClawOrAuthenticatedPermission]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request):
        queryset = _fuel_scoped_queryset().prefetch_related(
            "source_links__message__group", "evidence_files", "revisions__user"
        )
        for query_name, field_name in (
            ("organization_key", "organization_key"),
            ("origin_group_key", "origin_group_key"),
            ("vehicle", "vehicle_id"),
            ("driver", "driver_id"),
            ("status", "status"),
        ):
            value = request.query_params.get(query_name)
            if value:
                queryset = queryset.filter(**{field_name: value})
        date_value = request.query_params.get("date")
        if date_value:
            parsed = serializers.DateField().run_validation(date_value)
            queryset = queryset.filter(event_at__date=parsed)
        pending = request.query_params.get("pending_review")
        if pending is not None:
            pending = serializers.BooleanField().run_validation(pending)
            queryset = queryset.filter(status="requires_review") if pending else queryset.exclude(
                status="requires_review"
            )
        paginator = FuelReportPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(
            FuelReportSerializer(page, many=True, context={"request": request}).data
        )

    def post(self, request):
        if request.auth != "openclaw":
            return Response(
                {"detail": "This operation requires the bot integration token."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not isinstance(request.data, Mapping):
            raise serializers.ValidationError({"non_field_errors": ["Expected an object."]})
        data = request.data
        _validate_scope(data)
        idempotency_key = serializers.CharField(max_length=128).run_validation(
            data.get("idempotency_key")
        )
        source_messages = _parse_json_value(data, "source_messages", [])
        if not isinstance(source_messages, list) or not source_messages:
            raise serializers.ValidationError(
                {"source_messages": ["At least one source message is required."]}
            )
        source_ids = [item.get("message_id") for item in source_messages]
        if any(value is None for value in source_ids) or len(source_ids) != len(set(source_ids)):
            raise serializers.ValidationError(
                {"source_messages": ["message_id values are required and must be unique."]}
            )
        existing = _fuel_existing_by_key(idempotency_key)
        if existing:
            return _fuel_idempotency_response(existing, source_ids, request)

        messages = {
            message.id: message
            for message in WhatsAppMessage.objects.filter(
                id__in=source_ids, group_jid="120363420163225425@g.us"
            )
        }
        if set(messages) != set(source_ids):
            raise serializers.ValidationError(
                {"source_messages": ["Every message must exist in Choferes FGPY."]}
            )
        roles = {value for value, _ in FuelReportSourceMessage._meta.get_field("role").choices}
        for item in source_messages:
            if item.get("role") not in roles:
                raise serializers.ValidationError(
                    {"source_messages": [f"Invalid role for message {item['message_id']}."]}
                )

        field_confidence = _parse_json_value(data, "field_confidence", {})
        if not isinstance(field_confidence, dict) or set(field_confidence) - FUEL_CONFIDENCE_FIELDS:
            raise serializers.ValidationError(
                {"field_confidence": ["Contains unsupported field names."]}
            )
        for key, value in field_confidence.items():
            number = Decimal(str(value))
            if number < 0 or number > 1:
                raise serializers.ValidationError(
                    {"field_confidence": [f"{key} must be between 0 and 1."]}
                )

        def optional(field, value):
            raw = data.get(field)
            return None if raw in (None, "") else value.run_validation(raw)

        vehicle = optional(
            "vehicle",
            serializers.PrimaryKeyRelatedField(
                queryset=FgpyVehicle.objects.filter(
                    organization_key=FUEL_ORGANIZATION_KEY, active=True
                )
            ),
        )
        driver = optional(
            "driver",
            serializers.PrimaryKeyRelatedField(
                queryset=FgpyDriver.objects.filter(
                    organization_key=FUEL_ORGANIZATION_KEY, active=True
                )
            ),
        )
        values = {
            "organization_key": FUEL_ORGANIZATION_KEY,
            "origin_group_key": FUEL_ORIGIN_GROUP_KEY,
            "idempotency_key": idempotency_key,
            "event_at": optional("event_at", serializers.DateTimeField()),
            "vehicle": vehicle,
            "driver": driver,
            "liters": optional("liters", serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))),
            "odometer_total": optional("odometer_total", serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))),
            "odometer_partial": optional("odometer_partial", serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))),
            "station": data.get("station", ""),
            "receipt_number": data.get("receipt_number", ""),
            "fuel_type": data.get("fuel_type", ""),
            "amount": optional("amount", serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0"))),
            "currency": data.get("currency", ""),
            "unit_price": optional("unit_price", serializers.DecimalField(max_digits=14, decimal_places=4, min_value=Decimal("0"))),
            "overall_confidence": optional("overall_confidence", serializers.DecimalField(max_digits=5, decimal_places=4, min_value=Decimal("0"), max_value=Decimal("1"))),
            "field_confidence": field_confidence,
            "original_extraction": _parse_json_value(data, "original_extraction", {}),
            "review_notes": "",
        }
        proposed = _parse_json_value(data, "inconsistencies", [])
        if not isinstance(proposed, list):
            raise serializers.ValidationError({"inconsistencies": ["Expected a list."]})
        values["inconsistencies"] = _derive_fuel_inconsistencies(values, proposed)
        values["status"] = (
            "requires_review"
            if values["inconsistencies"] or any(values.get(name) is None for name in FUEL_CRITICAL_FIELDS)
            else "received"
        )

        uploads = request.FILES.getlist("evidence_files")
        evidence_types = _parse_json_value(data, "evidence_types", [])
        evidence_message_ids = _parse_json_value(data, "evidence_message_ids", [])
        if uploads and evidence_types and len(evidence_types) != len(uploads):
            raise serializers.ValidationError({"evidence_types": ["Must match uploaded files."]})
        max_size = int(getattr(settings, "FUEL_EVIDENCE_MAX_BYTES", 10 * 1024 * 1024))
        prepared_uploads = []
        seen_hashes = set()
        for index, upload in enumerate(uploads):
            if upload.size > max_size:
                raise serializers.ValidationError({"evidence_files": ["A file exceeds the size limit."]})
            mime_type, extension = _actual_mime(upload)
            digest = hashlib.sha256()
            for chunk in upload.chunks():
                digest.update(chunk)
            upload.seek(0)
            sha256 = digest.hexdigest()
            if sha256 in seen_hashes:
                raise serializers.ValidationError({"evidence_files": ["Duplicate evidence in request."]})
            seen_hashes.add(sha256)
            upload.name = f"{uuid.uuid4().hex}{extension}"
            evidence_type = evidence_types[index] if evidence_types else "other"
            message_id = evidence_message_ids[index] if index < len(evidence_message_ids) else None
            if evidence_type not in {"receipt", "dashboard", "combined", "other"}:
                raise serializers.ValidationError({"evidence_types": ["Invalid evidence type."]})
            if message_id is not None and message_id not in messages:
                raise serializers.ValidationError(
                    {"evidence_message_ids": ["Must refer to a source message."]}
                )
            prepared_uploads.append(
                (upload, mime_type, sha256, evidence_type, message_id)
            )
        existing_hashes = set(FuelReportEvidence.objects.filter(
            report__organization_key=FUEL_ORGANIZATION_KEY,
            report__origin_group_key=FUEL_ORIGIN_GROUP_KEY,
            sha256__in=seen_hashes,
        ).values_list("sha256", flat=True))
        if existing_hashes:
            values["inconsistencies"] = list(
                dict.fromkeys([*values["inconsistencies"], "duplicate_evidence"])
            )
            values["status"] = "requires_review"
            prepared_uploads = [
                item for item in prepared_uploads if item[2] not in existing_hashes
            ]

        stored_names = []
        try:
            with transaction.atomic():
                report = FuelReport.objects.create(**values)
                FuelReportSourceMessage.objects.bulk_create(
                    [
                        FuelReportSourceMessage(
                            report=report,
                            message=messages[item["message_id"]],
                            role=item["role"],
                            position=item.get("position", index),
                        )
                        for index, item in enumerate(source_messages)
                    ]
                )
                date_path = timezone.localdate().strftime("%Y/%m")
                for index, (upload, mime_type, sha256, evidence_type, message_id) in enumerate(prepared_uploads):
                    stored_name = default_storage.save(
                        f"forestal_bot/fuel/{date_path}/{upload.name}", upload
                    )
                    stored_names.append(stored_name)
                    FuelReportEvidence.objects.create(
                        report=report,
                        source_message=messages.get(message_id),
                        evidence_type=evidence_type,
                        file=stored_name,
                        mime_type=mime_type,
                        size=upload.size,
                        sha256=sha256,
                        position=index,
                    )
        except IntegrityError:
            _delete_stored_files(stored_names)
            winner = _fuel_existing_by_key(idempotency_key)
            if winner is None:
                raise
            return _fuel_idempotency_response(winner, source_ids, request)
        except Exception:
            _delete_stored_files(stored_names)
            raise
        return Response(
            FuelReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class FuelReportDetailView(APIView):
    authentication_classes = [OpenClawOrJWTAuthentication]
    permission_classes = [OpenClawOrAuthenticatedPermission]

    def get_object(self, pk):
        return _fuel_scoped_queryset().prefetch_related(
            "source_links__message__group", "evidence_files", "revisions__user"
        ).get(pk=pk)

    def get(self, request, pk):
        try:
            report = self.get_object(pk)
        except FuelReport.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(FuelReportSerializer(report, context={"request": request}).data)

    def patch(self, request, pk):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "A dashboard user is required for review."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            report = self.get_object(pk)
        except FuelReport.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        action = request.data.get("action")
        if action not in {"confirm", "correct", "reject"}:
            raise serializers.ValidationError(
                {"action": ["Use confirm, correct or reject."]}
            )
        reason = str(request.data.get("reason", "")).strip()
        changes = request.data.get("changes", {})
        if not isinstance(changes, Mapping):
            raise serializers.ValidationError({"changes": ["Expected an object."]})
        if set(changes) - FUEL_EDITABLE_FIELDS:
            raise serializers.ValidationError({"changes": ["Contains unsupported fields."]})
        if action in {"correct", "reject"} and not reason:
            raise serializers.ValidationError({"reason": ["A reason is required."]})
        if action != "correct" and changes:
            raise serializers.ValidationError({"changes": ["Only correct accepts changes."]})

        relation_fields = {
            "vehicle": serializers.PrimaryKeyRelatedField(
                queryset=FgpyVehicle.objects.filter(
                    organization_key=FUEL_ORGANIZATION_KEY, active=True
                ),
                allow_null=True,
            ),
            "driver": serializers.PrimaryKeyRelatedField(
                queryset=FgpyDriver.objects.filter(
                    organization_key=FUEL_ORGANIZATION_KEY, active=True
                ),
                allow_null=True,
            ),
        }
        decimal_fields = {
            "liters": serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True, min_value=Decimal("0.01")),
            "odometer_total": serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True, min_value=Decimal("0")),
            "odometer_partial": serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True, min_value=Decimal("0")),
            "amount": serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True, min_value=Decimal("0")),
            "unit_price": serializers.DecimalField(max_digits=14, decimal_places=4, allow_null=True, min_value=Decimal("0")),
        }
        with transaction.atomic():
            report = FuelReport.objects.select_for_update().get(pk=report.pk)
            changed = False
            for field_name, raw_value in changes.items():
                if field_name in relation_fields:
                    value = relation_fields[field_name].run_validation(raw_value)
                elif field_name in decimal_fields:
                    value = decimal_fields[field_name].run_validation(raw_value)
                elif field_name == "event_at":
                    value = serializers.DateTimeField(allow_null=True).run_validation(raw_value)
                else:
                    value = str(raw_value or "")
                previous = getattr(report, field_name)
                if previous != value:
                    FuelReportRevision.objects.create(
                        report=report,
                        field_name=field_name,
                        previous_value=_json_safe(previous),
                        new_value=_json_safe(value),
                        reason=reason,
                        user=request.user,
                        correction_source="human_correction",
                    )
                    setattr(report, field_name, value)
                    changed = True

            resolved_by_human = {
                "vehicle": {"missing_vehicle", "low_confidence_vehicle"},
                "liters": {"missing_liters", "low_confidence_liters"},
                "odometer_total": {
                    "missing_odometer",
                    "low_confidence_odometer",
                    "odometer_regression",
                },
            }
            resolved_codes = set()
            for field_name in changes:
                resolved_codes.update(resolved_by_human.get(field_name, set()))
            if resolved_codes:
                report.inconsistencies = [
                    code for code in report.inconsistencies if code not in resolved_codes
                ]

            now = timezone.now()
            if action == "reject":
                new_status = "rejected"
                source = "human_rejection"
            elif action == "confirm":
                missing = [field for field in FUEL_CRITICAL_FIELDS if getattr(report, field) is None]
                low = {
                    "low_confidence_vehicle",
                    "low_confidence_liters",
                    "low_confidence_odometer",
                }.intersection(report.inconsistencies)
                if missing or low:
                    raise serializers.ValidationError(
                        {"action": ["Critical pending or low-confidence fields prevent confirmation."]}
                    )
                new_status = "confirmed"
                source = "human_confirmation"
                report.confirmed_at = now
            else:
                new_status = "corrected" if changed else "requires_review"
                source = "human_correction"
            FuelReportRevision.objects.create(
                report=report,
                field_name="status",
                previous_value=report.status,
                new_value=new_status,
                reason=reason,
                user=request.user,
                correction_source=source,
            )
            report.status = new_status
            report.review_notes = reason or report.review_notes
            report.reviewed_by = request.user
            report.reviewed_at = now
            report.save()
        return Response(
            FuelReportSerializer(self.get_object(pk), context={"request": request}).data
        )


class FuelReportEvidenceDownloadView(APIView):
    authentication_classes = [OpenClawOrJWTAuthentication]
    permission_classes = [OpenClawOrAuthenticatedPermission]

    def get(self, request, pk, evidence_id):
        try:
            evidence = FuelReportEvidence.objects.select_related("report").get(
                pk=evidence_id,
                report_id=pk,
                report__organization_key=FUEL_ORGANIZATION_KEY,
                report__origin_group_key=FUEL_ORIGIN_GROUP_KEY,
            )
        except FuelReportEvidence.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        response = FileResponse(
            evidence.file.open("rb"),
            content_type=evidence.mime_type,
            as_attachment=False,
            filename=os.path.basename(evidence.file.name),
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response
