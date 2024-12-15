from client.client import Client
from coloring import models as color_models
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

    queryset = color_models.Prompt.objects.all()

    def create(self, request, *args, **kwargs):

        response = super().create(request, *args, **kwargs)
        input = request.data["prompt"]

        client_response = Client.get_prompt(input=input)

        if client_response:
            client_data = client_response.json()

        return response
