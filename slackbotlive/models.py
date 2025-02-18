from django.db import models

# Create your models here.
class cs(models.Model):
    user_id = models.CharField(max_length=255)  # Stores the user ID
    channel_id = models.CharField(max_length=255)  # Stores the channel ID
    user_input = models.TextField()  # Stores the user's message
    bot_response = models.TextField()  # Stores the bot's response
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for the record

    class Meta:
        db_table = 'conversation'  # Custom table name