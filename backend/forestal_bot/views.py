from django.db import IntegrityError, transaction
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from forestal_bot.models import WhatsAppMessage
from forestal_bot.permissions import OpenClawBearerPermission
from forestal_bot.serializers import WhatsAppMessageSerializer


class WhatsAppMessageCreateView(APIView):
    authentication_classes = []
    permission_classes = [OpenClawBearerPermission]

    def post(self, request):
        raw_json = dict(request.data)
        serializer = WhatsAppMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = dict(serializer.validated_data)
        identity = {
            field: validated_data.pop(field)
            for field in ("account_id", "group_jid", "message_id")
        }
        defaults = {**validated_data, "raw_json": raw_json}

        try:
            with transaction.atomic():
                message, created = WhatsAppMessage.objects.get_or_create(
                    **identity,
                    defaults=defaults,
                )
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
        queryset = WhatsAppMessage.objects.order_by("-timestamp", "-created_at")

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
