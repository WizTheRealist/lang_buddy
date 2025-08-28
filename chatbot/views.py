import logging
from django.shortcuts import render, redirect
from django.conf import settings
from google import genai
from google.genai import types
from .models import Conversation
from django.contrib import messages

logger = logging.getLogger(__name__)    # for logging errors

client = genai.Client(api_key=settings.GEMINI_API_KEY)
# Create your views here.
def chat_view(request):

    ai_reply = None
    selected_topic = None

    if request.method == "POST":
        user_message = request.POST.get('message')
        topic = request.POST.get('topics')
        selected_topic = topic

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=user_message,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    system_instruction=(f"Your name is John. You are a friendly English Tutor for {topic} conversations."
                                        "Do not greet the learner at the start of every reply."
                                        "Continue naturally from the conversation context."
                                        "Keep responses short, clear, and focused on practicing English.")
                ),
            )
            ai_reply = response.text

            # create database to store messages
            if user_message or ai_reply:
                Conversation.objects.create(
                    user_message=user_message,
                    ai_reply=ai_reply,
                    topics=topic
                )
                # persist chosen topic across the redirect
                request.session['selected_topic'] = topic

            return redirect("chat_view")
        
        except Exception as e:
            logger.error(f"Error in chat_view: {e}", exc_info=True)                 # error log with traceback
            messages.error(request, "Oops! Something went wrong please try again.") # user_friendly feedback
            ai_reply = "Sorry, I couldn't process your request."

    else:
        # GET: restore the previously chosen topic from session (if any)
        selected_topic = request.session.get('selected_topic')
    
    # display the last ten converstions by date
    chats = Conversation.objects.all().order_by('created_at')[:10]

    return render(request, 'chat.html', {
        "chats": chats,
        "ai_reply": ai_reply,
        "topics": selected_topic
        })