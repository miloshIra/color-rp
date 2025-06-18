import base64
import hashlib
import hmac
import logging

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

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
    def verify_token(
        *, polar_webhook_signature: str, timestamp: str, body_raw: dict
    ) -> dict:

        signature = polar_webhook_signature
        polar_webhook_secret = settings.POLAR_WEBHOOK_SECRET

        # if not timestamp or not signature:
        #     logger.warning("Unable to extract timestamp or signature from signature")
        #     return {"detail": "Unable to extract timestamp or signature from signature"}

        # try:
        #     encoded_secret = base64.b64encode(secret.encode()).decode()
        # except Exception as e:
        #     logger.error(f"Failed to base64 encode secret: {e}")
        #     return {"error": "Invalid secret configuration"}

        # # Standard Webhooks format: timestamp.payload
        # signed_payload = f"{timestamp}.{body_raw}"

        # # Compute HMAC-SHA256 with base64 encoded secret
        # computed_hash = hmac.new(
        #     encoded_secret.encode(), signed_payload.encode(), hashlib.sha256
        # ).hexdigest()

        # # Standard Webhooks signature format
        # expected_signature = f"sha256={computed_hash}"

        # # Compare signatures
        # if not hmac.compare_digest(expected_signature, signature):
        #     logger.warning(
        #         f"Computed signature does not match Polar signature. Expected: {expected_signature}, Got: {signature}"
        #     )
        #     return {"error": "Invalid signature"}

        # logger.info("Webhook signature verified successfully!")
        # return {"success": True}

        # # signed_payload = f"{timestamp}:{body_raw}"
        # # computed_hash = hmac.new(
        # #     secret.encode(), signed_payload.encode(), hashlib.sha256
        # # ).hexdigest()

        # # if not hmac.compare_digest(computed_hash, signature):
        # #     logger.warning("Computed signature does not match Paddle signature")
        # #     return {"error": "Invalid signature"}

        # # logger.info("Subscription accepted :)")
        # # return {"success": True}

        print(polar_webhook_secret)

        encoded_secret = base64.b64encode(polar_webhook_secret.encode()).decode()

        # Step 2: Create the signed payload in Standard Webhooks format
        signed_payload = f"{timestamp}.{body_raw}"

        # Step 3: Compute HMAC-SHA256
        computed_hash = hmac.new(
            encoded_secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()

        # Step 4: Format expected signature with sha256 prefix
        expected_signature = f"sha256={computed_hash}"

        # Step 5: Securely compare signatures
        result = hmac.compare_digest(expected_signature, signature)

        print(result)
        return {"success": result}
