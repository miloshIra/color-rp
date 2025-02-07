from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from .backends import SupabaseAuthBackend


class SupabaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]
        backend = SupabaseAuthBackend()
        user = backend.authenticate(request, token)
        if not user:
            raise AuthenticationFailed("Invalid token")
        return (user, None)
