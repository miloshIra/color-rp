from coloring import models as models
from rest_framework import serializers


class PromptSerizalizer(serializers.Serializer):
    class Meta:
        model = models.Prompt
        field = "__all__"

    def create(selg, validated_data):
        return models.Prompt.objects.create(**validated_data)
