from django.db import IntegrityError, transaction
from rest_framework import status
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
