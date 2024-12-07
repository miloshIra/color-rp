from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .resources import PromptViewset

router = SimpleRouter()

# Register the viewset with the router
router.register(r"prompts", PromptViewset, basename="prompt")

urlpatterns = [
    path("api/", include(router.urls)),
]
