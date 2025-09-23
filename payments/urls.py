from django.urls import include, path
from rest_framework import routers

from payments.views import PaymentViewSet
from payments.webhooks.stripe import stripe_webhook

router = routers.DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns =[
    path("", include(router.urls)),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
]

app_name="payments"
