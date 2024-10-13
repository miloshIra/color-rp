from rest_framework import serializers

from colorai.coloring import models as models


class PromptSerizalizer(serializers.Serializer):
    class Meta:
        model = models.Prompt
        field = "__all__"
