import base64
import logging
import os
import tempfile
from io import BytesIO

import requests
from client.client import RepliateClient
from coloring import models as color_models
from coloring.backends import PolarAuthBackend
from coloring.exceptions import DiscordAlertException, UserNotSubscribedException
from coloring.permissions import LimitedAnonymousAccess
from coloring.utils import discord_alert, discord_subscription_stats, discord_user_stats
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from colorai import settings
from supabase import Client, create_client

from . import serializers

User = get_user_model()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLIC_KEY)
logger = logging.getLogger(__name__)
bucket_name = settings.STORAGE_BUCKET_NAME


class PromptViewset(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [LimitedAnonymousAccess]
    serializer_class = serializers.PromptSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            try:
                return color_models.Prompt.objects.filter(
                    user=self.request.user
                ).order_by("-id")
            except Exception as e:
                raise DiscordAlertException(
                    message=str(e),
                    error=e,
                    request=self.request,
                )

        elif visitor := self.request.headers.get("X-Visitor-ID"):
            try:
                return color_models.Prompt.object.filter(visitor=visitor).order_by(
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
            if request.user.is_authenticated:
                if (
                    request.user.prompts_left > 0
                    and request.user.is_subscribed
                    or request.user.free_prompts > 0
                ):
                    input = request.data["prompt"]
                    client_response = RepliateClient.get_prompt(input=input)
                else:
                    return Response(
                        {
                            "detail": "No subscription or out of prompts! Click Subscribe on the top right to continue!"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            elif request.user.is_anonymous:
                input = request.data["prompt"]
                client_response = RepliateClient.get_prompt(input=input)
            else:
                return Response(
                    {
                        "detail": "No subscription or out of prompts! Click Subscribe on the top right to continue!"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if client_response:
                file_output = client_response[0]
                file_url = file_output.url
                image_response = requests.get(file_url)
                image_file = image_response.content

                image_name = f"{file_url.split('/')[-2]}.{file_url.split('.')[-1]}"
                visitor = request.headers.get("X-Visitor-ID")
                new_prompt = color_models.Prompt(
                    prompt=input,
                    user=request.user if request.user.is_authenticated else None,
                    visitor=visitor if request.user.is_anonymous else None,
                )
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

                if request.user.is_authenticated:
                    user = User.objects.get(supabase_id=request.user.supabase_id)
                    user.prompts_left = user.prompts_left - 1
                    user.total_prompts = user.total_prompts + 1
                    user.free_prompts = user.free_prompts - 1
                    user.save()

                serializer = self.get_serializer(new_prompt)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(
                {"Error": "No response from model, try later"},
                status=status.HTTP_410_GONE,
            )

        except Exception as e:
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
                {"message": "Prompt and image successfully deleted"},
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

    @action(detail=False, methods=["GET"])
    def explore(self, request, *args, **kwargs):
        try:
            prompts = color_models.Prompt.objects.all()
            serializer = self.get_serializer(prompts, many=True)
            return Response(serializer.data)
        except Exception as e:
            raise DiscordAlertException(
                message="Error in PromptViewset",
                error=e,
                request=request,
            )


class DrawingViewSet(ModelViewSet):
    lookup_field = "uuid"
    serializer_class = serializers.DrawingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        try:
            return color_models.Drawing.objects.filter(user=self.request.user.id)
        except Exception as e:
            raise DiscordAlertException(
                message=str(e),
                error=e,
                request=self.request,
            )

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                return Response({"Error": "Error saving drawing, no drawing provided"})

            base64_image = data.get("image")

            if not base64_image:
                return Response({"Error": "Missing name or image"}, status=400)

            if "," in base64_image:
                base64_image = base64_image.split(",")[1]

            try:
                image = base64.b64decode(base64_image)
            except Exception:
                return Response({"Error": "Invalid base64 image"}, status=400)

            new_drawing = color_models.Drawing(user=request.user)
            name = "drawing_" + str(new_drawing.uuid)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(image)
                temp_file_path = temp_file.name

            with open(temp_file_path, "rb") as image_file:
                supabase.storage.from_("images").upload(
                    name,
                    image_file,
                    file_options={
                        "cache-control": "3600",
                        "content-type": "image/jpeg",
                        "upsert": "false",
                    },
                )

            os.remove(temp_file_path)
            drawing_url = supabase.storage.from_(bucket_name).get_public_url(name)
            new_drawing.drawing_url = drawing_url
            new_drawing.name = name
            new_drawing.save()

            serializer = self.get_serializer(new_drawing)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            raise DiscordAlertException(
                message="Error in PromptViewset",
                error=e,
                request=request,
            )

    def destroy(self, request, *args, **kwargs):
        try:

            instance = self.get_object()
            if not instance:
                return Response(
                    {"Error": "No drawing found with that uuid"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            image_name = "drawing_" + str(instance.uuid)
            supabase.storage.from_("images").remove([image_name])
            instance.delete()

            return Response(
                {"message": "Drawing successfully deleted"},
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

        return Response({"response": response_data})

    @action(detail=True, methods=["PATCH"])
    def terms(self, request, *args, **kwargs):
        user_id = kwargs.get("supabase_id")
        user = User.objects.filter(supabase_id=user_id).first()
        user.accepted_terms = True
        user.save()

        return Response({"detail": "User accepted terms"})


@method_decorator(csrf_exempt, name="dispatch")
class PolarWebhookSubscriptionView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        body_raw = request.body.decode("utf-8")
        payment_type = request.data.get("type")
        data = request.data.get("data")

        check_token = PolarAuthBackend.verify_polar_webhook_signature(
            request=request, body_raw=body_raw, payment_type=payment_type
        )

        data = request.data.get("data")
        user_id = data.get("metadata").get("user_id")
        subscribed_user = User.objects.filter(supabase_id=user_id).first()

        if check_token.get("success"):

            sub_id = data.get("id")
            polar_customer_id = data.get("customer_id")
            last_payment_date = data.get("current_period_start")
            next_payment_date = data.get("current_period_end")

            update_fields = {
                "prompts_left": 500,
                "next_payment_date": next_payment_date,
                "last_payment_date": last_payment_date,
                "sub_id": sub_id,
                "is_subscribed": True,
                "polar_customer_id": polar_customer_id,
            }

            for field, value in update_fields.items():
                setattr(subscribed_user, field, value)

            subscribed_user.save()

            discord_subscription_stats(
                discord_webhook_url=settings.DISCORD_SUBS_WEBHOOK,
                user=subscribed_user.email,
                action=request.data.get("type"),
            )

            return Response({"user": user_id, "status": "subscribed"})

        return Response(
            {"error": "Subscription failed"}, status=status.HTTP_401_UNAUTHORIZED
        )


@method_decorator(csrf_exempt, name="dispatch")
class PolarWebhookPurchaseView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        body_raw = request.body.decode("utf-8")
        data = request.data.get("data")
        payment_type = request.data.get("type")

        check_token = PolarAuthBackend.verify_polar_webhook_signature(
            request=request, body_raw=body_raw, payment_type=payment_type
        )

        data = request.data.get("data")
        user_id = data.get("metadata").get("user_id")
        user = User.objects.filter(supabase_id=user_id).first()

        try:
            if check_token.get("success"):
                logger.warning("in token check")
                sub_id = data.get("id")
                polar_customer_id = data.get("customer_id")

                update_fields = {
                    "prompts_left": 100,
                    "sub_id": sub_id,
                    "is_subscribed": True,
                    "polar_customer_id": polar_customer_id,
                }

                for field, value in update_fields.items():
                    setattr(user, field, value)

                user.save()

                discord_subscription_stats(
                    discord_webhook_url=settings.DISCORD_SUBS_WEBHOOK,
                    user=user.email,
                    action=request.data.get("type"),
                )

                return Response({"user": user_id, "status": "subscribed"})

        except Exception as e:
            raise DiscordAlertException(
                message=str(e),
                error=e,
                request=request,
            )

        return Response(
            {"error": "Subscription failed"}, status=status.HTTP_401_UNAUTHORIZED
        )


def _i_dont_even_know_how_to_write_code():
    """This is here to remind you how bad you are,
    you can never delete it, cause you will never be good.
    it's harsh but it's true. I did good today, maybe.
    """
    pass
