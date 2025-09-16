from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Conversation(models.Model):
    CATEGORY_TOPICS = [
        ('travel', 'Travel'),
        ('business', 'Business'),
        ('academic', 'Academic'),
        ('conversational', 'Conversational')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_message = models.TextField()
    ai_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    topics = models.CharField(max_length=20, choices=CATEGORY_TOPICS, null=True, blank=True)

    def __str__(self):
        return f"Chat by {self.user.username} at {self.created_at}"
    
class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_messages = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    favorite_topic = models.CharField(max_length=20, null=True, blank=True)
    streak_days = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Progress"

class DailyActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    messages_count = models.IntegerField(default=0)
    topics_practiced = models.JSONField(default=list)  # Store list of topics used today
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date')
            ]
