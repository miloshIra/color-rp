import os
import tempfile
from io import BytesIO

import requests
from client.client import Client
from coloring import models as color_models
from coloring.backends import PaddleAuthBackend
from coloring.exceptions import DiscordAlertException, UserNotSubscribedException
from coloring.utils import discord_alert, discord_subscription_stats, discord_user_stats
from django.contrib.auth import get_user_model
from django.core.files import File
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
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from supabase import Client, create_client

from colorai import settings

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
            if request.user.prompts_left > 0:
                input = request.data["prompt"]
                client_response = Client.get_prompt(input=input)
            else:
                return Response(
                    {"error": "User not subscribed or out of prompts"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

                user = User.objects.get(supabase_id=request.user.supabase_id)
                user.prompts_left = user.prompts_left - 1
                user.total_prompts = user.total_prompts + 1
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

    @action(detail=True, methods=["POST"])
    def unsubscribe(self, request, *args, **kwargs):
        user_id = kwargs.get("supabase_id")
        print(user_id)
        user = User.objects.get(supabase_id=user_id)
        print(user)

        cancel_url = f"https://api.paddle.com/subscriptions/{user.sub_id}/cancel"

        payload = {
            "vendor_id": settings.PADDLE_VENDOR_ID,
            "api_key": settings.PADDLE_API_KEY,
            "subscription_id": user.sub_id,
        }

        try:
            response = requests.post(cancel_url, data=payload)
            response_data = response.json()
            print(response_data)

        except Exception as e:
            print(e)

        # user.is_subscribed = False # Add this when unsubscribe starts working.
        # user.save()

        return Response({"response": response_data})

    @action(detail=True, methods=["PATCH"])
    def terms(self, request, *args, **kwargs):
        user_id = kwargs.get("supabase_id")
        print(kwargs.get("supabase_id"))
        user = User.objects.filter(supabase_id=user_id).first()
        print(user)
        user.accepted_terms = True
        user.save()

        return Response({"detail": "User accepted terms"})


@method_decorator(csrf_exempt, name="dispatch")
class PaddleWebhookView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        body_raw = request.body.decode("utf-8")
        signature = request.headers.get("Paddle-Signature")

        check_token = PaddleAuthBackend.verify_token(
            paddle_signature=signature, body_raw=body_raw
        )

        data = request.data.get("data")
        user_id = data["custom_data"]["user_id"]
        subscribed_user = User.objects.filter(supabase_id=user_id).first()

        if check_token.get("success"):

            sub_id = data["id"]
            last_payment_date = data["current_billing_period"]["starts_at"]
            next_payment_date = data["next_billed_at"]

            update_fields = {
                "prompts_left": 500,
                "next_payment_date": next_payment_date,
                "last_payment_date": last_payment_date,
                "sub_id": sub_id,
                "is_subscribed": True,
            }
            for field, value in update_fields.items():
                setattr(subscribed_user, field, value)

            subscribed_user.save()

            discord_subscription_stats(
                discord_webhook_url=settings.DISCORD_SUBS_WEBHOOK,
                user=subscribed_user.email,
                action=request.data.get("event_type"),
            )

            return Response({"user": user_id, "status": "subscribed"})

        return Response(
            {"error": "Subscription failed"}, status=status.HTTP_401_UNAUTHORIZED
        )

    def andle_subscription_action(self, data, user):
        user = user.email
        discord_subscription_stats(
            discord_webhook_url=settings.DISCORD_SUBS_WEBHOOK,
            user=user,
            action=data["event_type"],
        )


data = {
    "data": {
        "id": "sub_01jm7ahxbps9kcr3jhpbaycr46",
        "items": [
            {
                "price": {
                    "id": "pri_01jktyszwt34s1escp4rk8zz0z",
                    "name": "Subscription",
                    "type": "standard",
                    "status": "active",
                    "quantity": {"maximum": 1, "minimum": 1},
                    "tax_mode": "account_setting",
                    "seller_id": "27322",
                    "created_at": "2025-02-11T16:52:17.434851Z",
                    "product_id": "pro_01jktyptn3fjdrt6seb4bb42zs",
                    "unit_price": {"amount": "599", "currency_code": "USD"},
                    "updated_at": "2025-02-13T00:16:22.73792Z",
                    "custom_data": None,
                    "description": "Monthly payment for application usage, includes over 500+ monthly prompts, countless photos generated, unlimited drawings database, generate once print forever.",
                    "import_meta": None,
                    "trial_period": None,
                    "billing_cycle": {"interval": "month", "frequency": 1},
                    "unit_price_overrides": [],
                },
                "status": "active",
                "product": {
                    "id": "pro_01jktyptn3fjdrt6seb4bb42zs",
                    "name": "ColoringAI",
                    "type": "standard",
                    "status": "active",
                    "image_url": None,
                    "seller_id": "27322",
                    "created_at": "2025-02-11T16:50:33.763Z",
                    "updated_at": "2025-02-13T00:16:59.311Z",
                    "custom_data": None,
                    "description": "A subscription to coloring-ai web application that creates coloring drawings for children paint on.",
                    "tax_category": "standard",
                },
                "quantity": 1,
                "recurring": True,
                "created_at": "2025-02-16T12:08:28.79Z",
                "updated_at": "2025-02-16T12:08:28.79Z",
                "trial_dates": None,
                "next_billed_at": "2025-03-16T12:08:27.923808Z",
            }
        ],
        "status": "active",
        "discount": None,
        "paused_at": None,
        "address_id": "add_01jm7ahachmrx94ffwkw7qdtbm",
        "created_at": "2025-02-16T12:08:28.79Z",
        "started_at": "2025-02-16T12:08:27.923808Z",
        "updated_at": "2025-02-16T12:08:28.79Z",
        "business_id": None,
        "canceled_at": None,
        "custom_data": {"user_id": "205d1772-7bd7-4231-8201-245aa838b17f"},
        "customer_id": "ctm_01jkxw6s9rz0vjsbpz7tc6jc3x",
        "import_meta": None,
        "billing_cycle": {"interval": "month", "frequency": 1},
        "currency_code": "USD",
        "next_billed_at": "2025-03-16T12:08:27.923808Z",
        "billing_details": None,
        "collection_mode": "automatic",
        "first_billed_at": "2025-02-16T12:08:27.923808Z",
        "scheduled_change": None,
        "current_billing_period": {
            "ends_at": "2025-03-16T12:08:27.923808Z",
            "starts_at": "2025-02-16T12:08:27.923808Z",
        },
    },
    "event_id": "evt_01jm7ahy1mhnp5y42990maq3cm",
    "event_type": "subscription.activated",
    "occurred_at": "2025-02-16T12:08:29.493055Z",
    "notification_id": "ntf_01jm7ahy61q2pwk2db4na9k3a7",
}
