from django_q.tasks import async_task
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.tasks import send_contact_us_email_response
from django.conf import settings


@api_view(["POST"])
def send_contact_us_email(request):
    to_email = request.data.get("email")
    subject = request.data.get("subject")
    full_name = request.data.get("full_name")
    context = {
        "recipient_name": full_name,
        "website_url": settings.FRONTEND_URL,
        "logo_url": settings.LOGO_URL,
    }
    async_task(
        "api.tasks.send_contact_us_email_response",
        to_email,
        subject,
        context,
        save=False,
    )
    return Response({"message": "Email successfully processed."})
