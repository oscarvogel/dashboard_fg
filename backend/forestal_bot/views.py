from collections.abc import Mapping
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from forestal_bot.models import (
    DailySummaryDelivery,
    DailySummaryGroup,
    DailySummaryRun,
    UNIDENTIFIED_GROUP_NAME,
    WhatsAppGroup,
    WhatsAppMessage,
    WEIGHING_ORGANIZATION_KEY,
    WEIGHING_UNIT_CATALOG,
    WeighingMeasurement,
    WeighingMeasurementRevision,
    WeighingMovement,
)
from forestal_bot.permissions import OpenClawBearerPermission
from forestal_bot.serializers import (
    DailySummaryRunSerializer,
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
