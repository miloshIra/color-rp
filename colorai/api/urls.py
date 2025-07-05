from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

from .resources import (
    PolarWebhookPurchaseView,
    PolarWebhookSubscriptionView,
    PromptViewset,
    UserViewset,
)

router = SimpleRouter()

# Register the viewset with the router
router.register(r"prompts", PromptViewset, basename="prompt")
router.register(r"users", UserViewset, basename="user")


urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "api/hooks/subscription",
        PolarWebhookSubscriptionView.as_view(),
        name="hook-subscription",
    ),
    path(
        "api/hooks/purchase", PolarWebhookPurchaseView.as_view(), name="hook-purchase"
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
