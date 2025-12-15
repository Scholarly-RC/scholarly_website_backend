from django_q.tasks import async_task
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from api.tasks import send_contact_us_email_response
from api.rag.chatbot import get_chatbot
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


@api_view(["POST"])
def chatbot_query(request):
    """
    Chatbot API endpoint for querying the scholarly data.
    
    Request body:
        {
            "question": "user question here"
        }
    
    Response:
        {
            "answer": "generated answer",
            "sources": ["source chunk 1", "source chunk 2", ...]
        }
    """
    question = request.data.get("question")
    
    if not question:
        return Response(
            {"error": "Question field is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(question, str) or not question.strip():
        return Response(
            {"error": "Question must be a non-empty string"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        chatbot = get_chatbot()
        result = chatbot.query(question.strip())
        
        return Response({
            "answer": result["answer"],
            "sources": result.get("sources", [])
        })
    except ValueError as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ValueError in chatbot_query: {str(e)}\n{error_trace}")
        return Response(
            {"error": str(e), "details": error_trace if settings.DEBUG else None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Exception in chatbot_query: {str(e)}\n{error_trace}")
        return Response(
            {"error": f"An error occurred while processing your question: {str(e)}", "details": error_trace if settings.DEBUG else None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
