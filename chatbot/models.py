from django.db import models

# Create your models here.
class Conversation(models.Model):
    user_message = models.TextField()
    ai_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
