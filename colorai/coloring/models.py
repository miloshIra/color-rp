import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from . import utils as utils
from .abs_models import DateTimeMixin


class Prompt(models.Model, DateTimeMixin):
    prompt = models.CharField(max_length=600, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="prompts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    images = models.ImageField(_("images"), upload_to="images")

    def __str__(self):
        return self.prompt or f"Prompt {self.id}"


class Media(models.Model):
    pass


class User(AbstractUser):
    """
    User model for the application.
    parameters:
        supabase_id: str
        subscription: Subscription
        username: str
        email: EmailField
        first_name: str
        last_name: str
        is_staff: bool
        is_active: bool
        date_joined: datetime
    """

    supabase_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.username:
            return self.username
        return self.email


class Subscription(models.Model):
    """
    Subscription model for the application.
    """

    is_active = models.BooleanField(default=False)
    date_subscribed = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
