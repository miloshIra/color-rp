import pdb

from django.utils import timezone
from rest_framework.permissions import BasePermission

from .models import Visitor


class LimitedAnonymousAccess(BasePermission):
    message = "You have reached the maximum number of requests. Please click Join and sign up."

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        visitor_id = request.headers.get("X-Visitor-ID")
        if not visitor_id:
            self.message = "Missing visitor ID"
            return False

        print("Are we here ?")
        obj, created = Visitor.objects.get_or_create(visitor_id=visitor_id)
        if obj.request_count >= 20000000:
            return False

        obj.request_count += 1
        obj.last_seen = timezone.now()
        obj.save()
        return True
