import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Order
from .task import send_email_task

stripe.api_key = settings.STRIPE_SECRET_KEY

def new_stripe_session(line_items, discount, tax, order, page_url):
    discounts = []
    if discount:
        add_coupon(discount)
        discounts = [{'coupon': discount.id}]

    session = stripe.checkout.Session.create(
        line_items=line_items,
        discounts=discounts,
        mode='payment',
        metadata={"order_id": order.id},
        success_url=f"{settings.DOMAIN}/success/",
        cancel_url=f"{settings.DOMAIN}{page_url}",
    )
    return session

def add_coupon(discount):
    try:
        stripe.Coupon.create(
            duration="once",
            id=str(discount.id),
            percent_off=discount.percent_off,
            name=discount.name
        )
    except stripe.error.InvalidRequestError:
        pass

def add_tax(tax):
    if tax and not tax.stripe_id:
        tax_rate = stripe.TaxRate.create(
            display_name=tax.name,
            percentage=tax.value,
            inclusive=True
        )
        tax.stripe_id = tax_rate.id
        tax.save(update_fields=['stripe_id'])

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.SECRET_WEBHOOK
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session["customer_details"]["email"]
        customer_name = session["customer_details"]["name"]
        order_id = session["metadata"]["order_id"]
        
        order = Order.objects.get(id=order_id)
        order.paid = True
        order.save()
        
        send_email_task.delay(customer_email, order_id, customer_name)

    return HttpResponse(status=200)