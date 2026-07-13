from collections.abc import Mapping

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
)
from forestal_bot.permissions import OpenClawBearerPermission
from forestal_bot.serializers import (
    DailySummaryRunSerializer,
    WhatsAppGroupSerializer,
    WhatsAppMessageSerializer,
    WhatsAppOwnerMessageSerializer,
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
