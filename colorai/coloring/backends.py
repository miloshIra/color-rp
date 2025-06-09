import hashlib
import hmac

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class SupabaseAuthBackend:
    def authenticate(self, request, token=None):
        if not token:
            print("NO TOKEN")
            return None

        try:
            print("What ?")
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
            print("Problem is expired")
            return None
        except jwt.InvalidTokenError:
            visitor_id = request.headers.get("X-Visitor-ID")
            print(request.headers)
            print(visitor_id)
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(supabase_id=user_id)
        except User.DoesNotExist:
            print("no user asshole!?")
            return None


class PaddleAuthBackend:
    def verify_token(*, paddle_signature, body_raw):
        signature_parts = paddle_signature.split(";")
        secret = settings.PADDLE_SECRET
        if len(signature_parts) != 2:
            return {"error": "Invalid signiture"}

        timestamp = signature_parts[0].split("=")[1]
        signature = signature_parts[1].split("=")[1]

        if not timestamp or not signature:
            print("Unable to extract timestamp or signature from signature")
            return {"error": "Unable to extract timestamp or signature from signature"}

        signed_payload = f"{timestamp}:{body_raw}"
        computed_hash = hmac.new(
            secret.encode(), signed_payload.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, signature):
            print("Computed signature does not match Paddle signature")
            return {"error": "Invalid signature"}

        return {"success": True}
