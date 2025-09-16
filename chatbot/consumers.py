import json
import logging
from google import genai
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from google.genai import types
from django.utils import timezone
from .models import Conversation
from datetime import date
from django.conf import settings
from django.db.models import Count



# for logging errors
logger = logging.getLogger(__name__)

# initialize gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def update_user_progress(user, topic):
    """Update user progress after saving a conversation"""
    from .models import UserProgress, DailyActivity
    
    # Get or create user progress
    progress, created = await sync_to_async(UserProgress.objects.get_or_create)(user=user)
    progress.total_messages += 1
    progress.last_activity = timezone.now()
    
    # Update favorite topic - get topic counts
    topic_counts = await sync_to_async(
        lambda: Conversation.objects.filter(user=user).values('topics').annotate(
            count=Count('topics')
        ).order_by('-count').first()
    )()
    
    if topic_counts:
        progress.favorite_topic = topic_counts['topics']
    
    await sync_to_async(progress.save)()
    
    # Update daily activity
    today = date.today()
    daily, created = await sync_to_async(DailyActivity.objects.get_or_create)(
        user=user, 
        date=today,
        defaults={'messages_count': 0, 'topics_practiced': []}
    )
    daily.messages_count += 1
    
    if topic not in daily.topics_practiced:
        daily.topics_practiced.append(topic)
    
    await sync_to_async(daily.save)()

# A websocket class that inherits from a parent websocket class
class ChatConsumer(AsyncWebsocketConsumer):
    
    # initialize websocket connection and authenticate user
    async def connect(self):
        user = self.scope["user"]
        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close()
        else:
            await self.accept()

    # async function that parses data in server and client side
    async def receive(self, text_data):
        from .models import Conversation
        try:
            # load data in json format for the server
            data = json.loads(text_data)
            action = data.get('action', 'send_message')  # default to send_message
            
            # Handle conversation reset
            if action == 'reset_conversation':
                topic = data.get('topics')
                # Clear the conversation from session
                self.scope["session"]["conversation"] = []
                self.scope["session"]["selected_topic"] = topic
                await sync_to_async(self.scope["session"].save)()
                
                # Send confirmation back to client
                await self.send(text_data=json.dumps({
                    "action": "conversation_reset",
                    "topic": topic
                }))
                return
            
            # Handle regular message sending
            if action == 'send_message':
                user_message = data.get('message')
                topic = data.get('topics')

                # Get current conversation from session
                conversation = self.scope["session"].get("conversation", [])
                
                # Check if topic changed from the last stored topic
                last_topic = self.scope["session"].get("selected_topic")
                if last_topic and last_topic != topic:
                    # Topic changed, reset conversation
                    conversation = []
                
                # Add user message to conversation
                conversation.append({"role": "user", "parts": [{"text": user_message}]})
                conversation = conversation[-10:]  # Keep last 10 messages

                # call gemini: model, add session context into "contents",
                # and system instruction
                response = await sync_to_async(client.models.generate_content)(
                    model="gemini-2.0-flash-lite",
                    contents=[m["parts"][0]["text"] for m in conversation],
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0),
                        system_instruction=(
                            f"Your name is John. You are a friendly English Tutor for {topic} conversations. "
                            "Do not greet the learner at the start of every reply. "
                            "Continue naturally from the conversation context. "
                            "Keep responses short, clear, and focused on practicing English."
                        ),
                    )
                )

                # initialize ai response, append to conversation
                # save conversation in session, and save session
                ai_reply = response.text
                conversation.append({"role": "model", "parts": [{"text": ai_reply}]})
                self.scope["session"]["conversation"] = conversation
                self.scope["session"]["selected_topic"] = topic
                await sync_to_async(self.scope["session"].save)()

                # save to database
                if user_message or ai_reply:
                    await sync_to_async(Conversation.objects.create)(
                        user=self.scope["user"],
                        user_message=user_message,
                        ai_reply=ai_reply,
                        topics=topic
                    )

                    await update_user_progress(self.scope["user"], topic)


                # send response to client
                await self.send(text_data=json.dumps({
                    "user_message": user_message,
                    "ai_reply": ai_reply,
                    "topic": topic
                }))

        # catch errors in log
        except Exception as e:
            logger.error(f"Error in ChatConsumer.receive: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "error": "Oops! Something went wrong. Please try again."
            }))

    # disconnect function
    async def disconnect(self, close_code):
        pass