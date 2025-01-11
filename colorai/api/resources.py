from io import BytesIO

import requests
from client.client import Client
from coloring import models as color_models
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
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from . import serializers


class PromptViewset(ModelViewSet):
    lookup_field = "uuid"
    # permission_classes = [permissions.IsLoggedIn]
    serializer_class = serializers.PromptSerizalizer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    queryset = color_models.Prompt.objects.all().order_by("-id")

    def create(self, request, *args, **kwargs):

        input = request.data["prompt"]

        # return Response({"Aladin": "Great success!"}, status=status.HTTP_200_OK)
        client_response = Client.get_prompt(input=input)

        if client_response:
            file_output = client_response[0]
            file_url = file_output.url
            print(file_url)
            image_response = requests.get(file_url)
            image_file = BytesIO(image_response.content)
            image_name = file_url.split("/")[-1]
            # file_data = file_output.file
            # file_name = file_output.filename

            new_prompt = color_models.Prompt(prompt=input)

            new_prompt.images.save(image_name, File(image_file), save=True)

            return Response({"file_url": file_url}, status=status.HTTP_200_OK)

        return Response(
            {"Error": "No response from replicate"}, status=status.HTTP_410_GONE
        )
