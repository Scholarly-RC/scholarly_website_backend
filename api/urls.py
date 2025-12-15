from django.urls import path

from api.views import send_contact_us_email, chatbot_query

app_name = "api"

urlpatterns = [
    path("contact-us-email/", send_contact_us_email, name="contact_us_email"),
    path("chatbot/", chatbot_query, name="chatbot"),
]
