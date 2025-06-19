import base64
import hashlib
import hmac
import logging

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from polar_sdk.webhooks import WebhookVerificationError, validate_event

User = get_user_model()

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)


class SupabaseAuthBackend:
    def authenticate(self, request, token=None):
        if not token:
            logger.warning("NO TOKEN")
            return None
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
            )

            user_id = payload.get("sub")
            if not user_id:
                return None

            user, created = User.objects.get_or_create(
                supabase_id=user_id,
                defaults={
                    "email": payload.get("email"),
                    "username": payload.get("email"),
                },
            )

            return user

        except jwt.ExpiredSignatureError:
            logger.warning("Problem is expired")
            return None
        except jwt.InvalidTokenError:
            visitor_id = request.headers.get("X-Visitor-ID")
            logger.warning(request.headers)
            logger.warning(visitor_id)
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(supabase_id=user_id)
        except User.DoesNotExist:
            logger.warning("no user")
            return None


class PolarAuthBackend:
    def verify_polar_webhook_signature(*, request: HttpRequest, body_raw: str) -> dict:

        polar_webhook_secret = settings.POLAR_WEBHOOK_SECRET

        try:
            event = validate_event(
                body=body_raw,
                headers=request.headers,
                secret=polar_webhook_secret,
            )

            return {"success": event}

        except WebhookVerificationError as e:
            logger.error(f"Polar webhook verification failed: {e}")
