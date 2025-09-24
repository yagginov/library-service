import json

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from notifications.tasks import send_success_payment_notification
from payments.models import Payment

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

    if event.type == "checkout.session.completed":
        session = event.data.object
        payment = get_object_or_404(Payment, session_id=session.id)
        payment.status = Payment.Status.PAID
        payment.save()
        borrowing = payment.borrowing
        user = borrowing.user
        book = borrowing.book
        message = (
            f"Successful payment!\n\n"
            f"User: {user.email}\n"
            f"Book: {book.title}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Amount paid: {payment.money_to_pay}"
        )
        send_success_payment_notification.delay(message)

    if event.type == "checkout.session.expired":
        session = event.data.object
        payment = get_object_or_404(Payment, session_id=session.id)
        payment.status = Payment.Status.EXPIRED
        payment.save()
        
    return HttpResponse(status=200)
