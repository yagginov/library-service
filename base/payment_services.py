import time
from abc import ABC, abstractmethod

import stripe
from django.conf import settings
from django.urls import reverse

from base.dto import PaymentSessionData


class BasePaymentService(ABC):
    @abstractmethod
    def create_payment_session(self, data: PaymentSessionData):
        raise NotImplementedError

    @abstractmethod
    def is_paid(self, session_id):
        raise NotImplementedError

    @abstractmethod
    def mark_session_as_expired(self, session_id):
        raise NotImplementedError


class StripePaymentService(BasePaymentService):
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_payment_session(self, data: PaymentSessionData):
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": data.product_data.model_dump(),
                        "unit_amount": int(data.unit_amount * 100),
                    },
                    "quantity": data.quantity,
                }
            ],
            mode="payment",
            success_url=f"{settings.SITE_URL}{reverse('payments:payment-success')}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url= f"{settings.SITE_URL}{reverse('payments:payment-cancel')}?session_id={{CHECKOUT_SESSION_ID}}",
            expires_at=int(time.time()) + 1802,
        )
        return session

    def is_paid(self, session_id):
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"

    def mark_session_as_expired(self, session_id):
        session = stripe.checkout.Session.expire(session_id)
        return session


payment_service = StripePaymentService()
