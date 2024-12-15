from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .resources import PromptViewset

router = SimpleRouter()

# Register the viewset with the router
router.register(r"prompts", PromptViewset, basename="prompt")

urlpatterns = [
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
