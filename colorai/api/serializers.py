from coloring import models as models
from rest_framework import serializers


class PromptSerizalizer(serializers.ModelSerializer):
    images = serializers.ImageField(required=False)

    class Meta:
        model = models.Prompt
        fields = ["prompt", "images"]

    # def create(self, validated_data):
    #     print(**validated_data)
    #     print(validated_data["prompt"])
    #     return models.Prompt.objects.create(**validated_data)
