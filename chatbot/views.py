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

    selected_topic = request.session.get("selected_topic")
    
    # use sliding window to display the last ten converstions for selected topic by date
    if selected_topic:
        chats = Conversation.objects.filter(
            user=request.user,
            topics=selected_topic
        ).order_by('-created_at')[:10]
    else:
        chats = Conversation.objects.filter(
            user=request.user
            ).order_by('-created_at')[:10]
    
    # Reverse for chronological order
    chats = chats[::-1]

    return render(request, 'chat.html', {
        "chats": chats,
        "topics": selected_topic
        })

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

@login_required
def update_session_topic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic')
            
            if topic:
                # Update session with new topic
                request.session['selected_topic'] = topic
                request.session.save()  # Force save the session
                
                return JsonResponse({
                    'success': True, 
                    'topic': topic
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'No topic provided'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


from django.db.models import Count
from datetime import date, timedelta, timezone
from .models import UserProgress, DailyActivity

@login_required
def dashboard_view(request):
    """
    Display user's learning progress dashboard with statistics and recent activity.
    """
    try:
    # Get or create user progress
        progress, created = UserProgress.objects.get_or_create(user=request.user)
        
        # Get recent activity (last 7 days)
        seven_days_ago = date.today() - timedelta(days=7)
        recent_activity = DailyActivity.objects.filter(
            user=request.user,
            date__gte=seven_days_ago
        ).order_by('-date')
        
        # Get topic statistics
        topic_stats = Conversation.objects.filter(user=request.user).values('topics').annotate(
            count=Count('topics')
        ).order_by('-count')
        
        # Calculate this week's messages
        week_messages = sum(activity.messages_count for activity in recent_activity)
        
        context = {
            'progress': progress,
            'recent_activity': recent_activity,
            'topic_stats': topic_stats,
            'week_messages': week_messages,
        }

    except Exception as e:
        # Log the error and show a user-friendly message
        logger.error(f"Dashboard error for user {request.user.id}: {e}")
        messages.error(request, "Unable to load dashboard. Please try again.")
        return redirect('chat_view')
    
    return render(request, 'dashboard.html', context)

