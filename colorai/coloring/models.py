import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
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
    visitor = models.UUIDField(null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    image_url = models.URLField(_("image URL"), max_length=500, null=True, blank=True)
    images = models.ImageField(_("images"), upload_to="images", null=True, blank=True)

    def __str__(self):
        return self.prompt or f"Prompt {self.id}"


class Media(models.Model):
    pass


class User(AbstractUser):
    """
    User model for the application.
    parameters:
        supabase_id: str
        sub_id: str
        username: str
        email: EmailField
        first_name: str
        last_name: str
        is_staff: bool
        is_active: bool
        date_joined: datetime
        promts_left: int
        last_payment_date: DateTime
        next_payment_date: DateTime
        billing_period: str
        is_subscribed: bool
        polar_customer_id: str
    """

    supabase_id = models.CharField(max_length=255, null=True, blank=True)
    prompts_left = models.IntegerField(default=2)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_payment_date = models.DateTimeField(null=True, blank=True)
    billing_period = models.CharField(null=True, blank=True, default="monthy")
    is_subscribed = models.BooleanField(default=False)
    total_prompts = models.IntegerField(default=0)
    accepted_terms = models.BooleanField(default=False)
    sub_id = models.CharField(null=True, blank=True)
    polar_customer_id = models.CharField(null=True, blank=True)
    free_prompts = models.IntegerField(default=3)

    def __str__(self):
        if self.username:
            return self.username
        return self.email

    class Meta:
        indexes = [models.Index(fields=["supabase_id"])]


class Visitor(models.Model):
    visitor_id = models.CharField(max_length=255, null=True, blank=True)
    request_count = models.PositiveBigIntegerField(default=0)
    last_seen = models.DateTimeField(default=timezone.now)


class Drawing(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(
        User, related_name="drawings", blank=True, null=True, on_delete=models.CASCADE
    )
    prompt = models.ForeignKey(
        Prompt, related_name="drawings", blank=True, null=True, on_delete=models.CASCADE
    )
    drawing_url = models.URLField(_("image URL"), max_length=500, null=True, blank=True)
    is_favourite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# class Subscription(models.Model):
#     """
#     Subscription model for the application.
#     """

#     is_active = models.BooleanField(default=False)
#     date_subscribed = models.DateTimeField(null=True, blank=True)
#     valid_until = models.DateTimeField(null=True, blank=True)
