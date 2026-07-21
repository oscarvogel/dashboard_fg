import secrets

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication


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


def has_openclaw_token(request):
    configured_token = getattr(settings, "OPENCLAW_INGEST_TOKEN", "")
    authorization = request.META.get("HTTP_AUTHORIZATION", "")
    parts = authorization.split()
    if not configured_token or len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    try:
        return secrets.compare_digest(
            parts[1].encode("ascii"), configured_token.encode("ascii")
        )
    except (AttributeError, UnicodeEncodeError):
        return False


class OpenClawOrJWTAuthentication(BaseAuthentication):
    """Accept the integration bearer without making it a Django user."""

    def authenticate(self, request):
        if has_openclaw_token(request):
            return (AnonymousUser(), "openclaw")
        return JWTAuthentication().authenticate(request)


class OpenClawOrAuthenticatedPermission(BasePermission):
    def has_permission(self, request, view):
        return request.auth == "openclaw" or bool(
            request.user and request.user.is_authenticated
        )
