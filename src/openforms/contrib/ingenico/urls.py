from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from .views import (
    ClientSessionAPIView,
    CreateCheckoutAPIView,
    IngenicoProtoDevView,
    ReturnFromCheckoutAPIView,
    WebhookAPIView,
)

app_name = "ingenico"

urlpatterns = [
    path(
        "dev/",
        include(
            [
                path(
                    "proto",
                    IngenicoProtoDevView.as_view(),
                    name="'dev",
                ),
                path(
                    "api/session",
                    # TODO remove csrf_exempt
                    csrf_exempt(ClientSessionAPIView.as_view()),
                    name="'api_session",
                ),
                path(
                    "api/checkout/return",
                    # TODO remove csrf_exempt
                    csrf_exempt(ReturnFromCheckoutAPIView.as_view()),
                    name="'api_checkout_return",
                ),
                path(
                    "api/checkout",
                    # TODO remove csrf_exempt
                    csrf_exempt(CreateCheckoutAPIView.as_view()),
                    name="'api_checkout",
                ),
                path(
                    "api/webhook",
                    # TODO remove csrf_exempt
                    csrf_exempt(WebhookAPIView.as_view()),
                    name="'api_webhook",
                ),
            ]
        ),
    )
]
