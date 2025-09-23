import json

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

from payments.models import Payment
from base.dto import PaymentData, ProductData
from payments.services.payment import PaymentProcessor

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError:
        return HttpResponse(status=400)

    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return json.jsonify(success=False)

    if event.type == "checkout.session.expired":
        session = event.data.object
        payment = get_object_or_404(Payment, session_id=session.id)
        payment.status = Payment.Status.EXPIRED
        payment.save()
        
    return HttpResponse(status=200)