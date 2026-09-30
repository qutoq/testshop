from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_task(mail, order_id, name):
    subject = "Вы успешно оплатили заказ!"
    message = (
        f"Но, к сожалению, это тестовый магазин, на этом всё. Доставки не будет(\n"
        f"Номер заказа: {order_id}. Покупатель: {name}"
    )
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [mail],
        fail_silently=False,
    )