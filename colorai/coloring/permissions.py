import pdb

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from .models import Visitor


class LimitedAnonymousAccess(BasePermission):
    message = "Maximum number of trail requests reached. Please click Join and sign up."

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        visitor_id = request.headers.get("X-Visitor-ID")
        if not visitor_id:
            self.message = "Missing visitor ID"
            raise PermissionDenied(self.message)

        try:
            obj, created = Visitor.objects.get_or_create(visitor_id=visitor_id)
        except Exception as e:
            self.message = "Visitor tracking error"

        if obj.request_count >= 2:
            raise PermissionDenied(self.message)

        obj.request_count += 1
        obj.last_seen = timezone.now()
        obj.save()
        return True
