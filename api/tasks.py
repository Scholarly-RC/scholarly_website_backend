from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_contact_us_email_response(to_email, subject, context):
    html_content = render_to_string("emails/contact-us-response.html", context)

    send_mail(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        html_message=html_content,
    )
