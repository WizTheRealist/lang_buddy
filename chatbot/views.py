import logging
from django import forms
from django.shortcuts import render, redirect
from django.conf import settings
from google import genai
from google.genai import types
from .models import Conversation
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)    # for logging errors

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Create your views here.

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("chat_view")
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {"form": form})


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "login.html"  # adjust to match your template


@login_required
def chat_view(request):

    ai_reply = None
    selected_topic = None

    if request.method == "POST":
        user_message = request.POST.get('message')
        topic = request.POST.get('topics')
        selected_topic = topic

        try:
            # store conversation in a session, append user_message, and use the last 10 user messages to build context
            conversation = request.session.get("conversation", [])
            conversation.append({"role": "user", "parts": [{"text": user_message}]})
            conversation = conversation[-10:]

            # instructions for Gemini on how to generate content
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=[m["parts"][0]["text"] for m in conversation],       # build conversation context from user_message line 52
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    system_instruction=(f"Your name is John. You are a friendly English Tutor for {topic} conversations."
                                        "Do not greet the learner at the start of every reply."
                                        "Continue naturally from the conversation context."
                                        "Keep responses short, clear, and focused on practicing English.")
                ),
            )
            # generate AI response, append AI response to conversation, store AI response in session for conversation context
            ai_reply = response.text
            conversation.append({"role": "model", "parts": [{"text": ai_reply}]})
            request.session["conversation"] = conversation

            # create database to store user records, topics, and messages
            if user_message or ai_reply:
                Conversation.objects.create(
                    user=request.user,
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
    
    # use sliding window to display the last ten converstions by date
    chats = Conversation.objects.filter(user=request.user).order_by('-created_at')[:10]
    chats = chats[::-1]

    return render(request, 'chat.html', {
        "chats": chats,
        "ai_reply": ai_reply,
        "topics": selected_topic
        })