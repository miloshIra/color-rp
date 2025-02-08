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
            print("ExpiredSignatureError")
            return None
        except jwt.InvalidTokenError:
            print("InvalidTokenError")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(supabase_id=user_id)
        except User.DoesNotExist:
            return None
