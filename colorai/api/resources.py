import os
import tempfile
from io import BytesIO

import requests
from django.contrib.auth import get_user_model
from django.core.files import File
from rest_framework import exceptions, generics, pagination, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter as drf_OrderingFilter
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from supabase import Client, create_client

from client.client import Client
from colorai import settings
from coloring import models as color_models
from coloring.exceptions import DiscordAlertException
from coloring.utils import discord_alert

from . import serializers

User = get_user_model()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLIC_KEY)

bucket_name = settings.STORAGE_BUCKET_NAME


class PromptViewset(ModelViewSet):
    lookup_field = "uuid"
    # permission_classes = [permissions.IsLoggedIn]
    serializer_class = serializers.PromptSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        try:
            return color_models.Prompt.objects.filter(user=self.request.user).order_by(
                "-id"
            )
        except Exception as e:
            raise DiscordAlertException(
                message=str(e),
                error=e,
                request=self.request,
            )

    def create(self, request, *args, **kwargs):
        try:

            input = request.data["prompt"]
            client_response = Client.get_prompt(input=input)

            if client_response:
                file_output = client_response[0]
                file_url = file_output.url
                image_response = requests.get(file_url)
                image_file = image_response.content

                image_name = f"{file_url.split('/')[-2]}.{file_url.split('.')[-1]}"

                new_prompt = color_models.Prompt(prompt=input, user=request.user)
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".jpg"
                ) as temp_file:
                    temp_file.write(image_file)
                    temp_file_path = temp_file.name

                with open(temp_file_path, "rb") as image:
                    supabase.storage.from_("images").upload(
                        image_name,
                        image,
                        file_options={
                            "cache-control": "3600",
                            "content-type": "image/jpeg",
                            "upsert": "false",
                        },
                    )
                os.remove(temp_file_path)
                image_url = supabase.storage.from_(bucket_name).get_public_url(
                    image_name
                )
                new_prompt.image_url = image_url
                new_prompt.save()

                serializer = self.get_serializer(new_prompt)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(
                {"Error": "No response from replicate"}, status=status.HTTP_410_GONE
            )
        except Exception as e:
            raise e
            raise DiscordAlertException(
                message="Error in PromptViewset",
                error=e,
                request=request,
            )

    def destroy(self, request, *args, **kwargs):
        try:
            image_url = request.data.get("image_url")

            if not image_url:
                return Response(
                    {"Error": "No image_url provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            prompt = color_models.Prompt.objects.filter(
                user=request.user, image_url=image_url
            ).first()

            image_filter = prompt.image_url[:-1]
            image_name = image_filter.split("/")[-1]

            supabase.storage.from_("images").remove([image_name])
            prompt.delete()

            return Response(
                {"Message": "Prompt and image successfully deleted"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            raise DiscordAlertException(
                message="Error in PromptViewset",
                error=e,
                request=request,
            )


class UserViewset(ModelViewSet):
    serializer_class = serializers.UserSerializer
    permission_classes = [AllowAny]
    lookup_field = "supabase_id"

    def get_queryset(self):
        try:
            return User.objects.filter(supabase_id=self.request.user.supabase_id)

        except Exception as e:
            raise DiscordAlertException(
                message=str(e),
                error=e,
                request=self.request,
            )

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            print(serializer.validated_data)

            if User.objects.filter(email=request.data["email"]).exists():
                return Response(
                    {"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.create_user(**serializer.validated_data)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise DiscordAlertException(
                message=str(e),
                error=e,
                request=request,
            )

    @action(detail=False, methods=["POST"])
    def exists(self, request, *args, **kwargs):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(email=email)
            return Response(
                {"exists": True, "message": "User with this email already exists."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {"exists": False, "message": "User does not exist."},
                status=status.HTTP_200_OK,
            )
