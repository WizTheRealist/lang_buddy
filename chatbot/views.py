from django.shortcuts import render, redirect
from django.conf import settings
from google import genai
from google.genai import types
from .models import Conversation

client = genai.Client(api_key=settings.GEMINI_API_KEY)
# Create your views here.
def chat_view(request):

    ai_reply = None

    if request.method == "POST":
        user_message = (request.POST.get('message'))
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=user_message,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        ai_reply = response.text

        if user_message or ai_reply:
            Conversation.objects.create(
                user_message=user_message,
                ai_reply=ai_reply
            )
        return redirect("chat_view")

    chats = Conversation.objects.all().order_by('created_at')[:10]

    return render(request, 'chat.html', {"chats": chats, "ai_reply": ai_reply})