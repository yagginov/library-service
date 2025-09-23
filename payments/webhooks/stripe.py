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
        borrowing = payment.borrowing
        book = borrowing.book

        rent_day = (borrowing.expected_return_date - borrowing.borrow_date).days

        payment_data = PaymentData()
        payment_data.product_data = ProductData(
            name=book.title,
            description=f"author: {book.author}",
        )
        payment_data.price = book.daily_fee
        payment_data.rent_days = rent_day

        _ = PaymentProcessor.create_payment_by_borrowing(borrowing, payment_data)
        
    return HttpResponse(status=200)