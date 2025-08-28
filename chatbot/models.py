from django.db import models

# Create your models here.
class Conversation(models.Model):
    CATEGORY_TOPICS = [
        ('travel', 'Travel'),
        ('business', 'Business'),
        ('academic', 'Academic'),
        ('conversational', 'Conversational')
    ]
    user_message = models.TextField()
    ai_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    topics = models.CharField(max_length=20, choices=CATEGORY_TOPICS, null=True, blank=True)
