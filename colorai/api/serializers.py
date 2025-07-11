from rest_framework import serializers

from coloring import models as models


class PromptSerializer(serializers.ModelSerializer):
    images = serializers.ImageField(required=False)

    class Meta:
        model = models.Prompt
        fields = ["prompt", "uuid", "image_url", "images"]


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    supabase_id = serializers.CharField(required=True)
    username = serializers.CharField(default="new user")

    class Meta:
        model = models.User
        fields = [
            "email",
            "supabase_id",
            "username",
            "first_name",
            "last_name",
            "id",
            "is_active",
            "date_joined",
            "is_subscribed",
            "prompts_left",
            "accepted_terms",
            "polar_customer_id",
        ]
