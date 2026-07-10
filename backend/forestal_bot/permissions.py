import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission


class OpenClawBearerPermission(BasePermission):
    def has_permission(self, request, view):
        configured_token = getattr(settings, "OPENCLAW_INGEST_TOKEN", "")
        if not configured_token:
            return False

        authorization = request.META.get("HTTP_AUTHORIZATION", "")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
            return False

        try:
            supplied_token = parts[1].encode("ascii")
            expected_token = configured_token.encode("ascii")
        except (AttributeError, UnicodeEncodeError):
            return False

        return secrets.compare_digest(supplied_token, expected_token)
