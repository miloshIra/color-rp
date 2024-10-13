import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from . import utils as utils
from .abs_models import DateTimeMixin


class Prompt(models.Model, DateTimeMixin):
    prompt = models.CharField(max_length=600, null=True, blank=True)
    user = models.ForeignKey(
        "auth.User",
        related_name="prompts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    images = models.ImageField(_("images"), upload_to=utils.upload_file_lowercase_name)

    def __str__(self):
        return self.prompt or f"Prompt {self.id}"


class Media(models.Model):
    pass
