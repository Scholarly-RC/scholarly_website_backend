from django.urls import path

from api.views import send_contact_us_email

app_name = "api"

urlpatterns = [
    path("contact-us-email/", send_contact_us_email, name="contact_us_email"),
]
