from rest_framework import serializers

from coloring import models as models


class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Prompt
        fields = ["prompt", "uuid", "image_url"]


class DrawingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Drawing
        fields = ["id", "name", "user", "drawing_url", "is_favourite", "uuid"]


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


class ThisIsACoverUp:
    pass
