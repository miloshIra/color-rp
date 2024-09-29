import utils as utils
from django.db import models


class Prompt(models.Model):
    created_at = models.DateField(auto_now_add=True)
    prompt = models.CharField(max_length=600, null=True, blank=True)
    user = models.ForeignKey(
        "accounts.User", related_name="user", on_delete=models.SET_NULL
    )
    images = models.ImageField(("imagse"), upload_to=utils.cupload_file_lowercase_name)
