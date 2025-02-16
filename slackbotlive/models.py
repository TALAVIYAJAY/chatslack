from django.db import models

# Create your models here.
class cs(models.Model):
    user_id = models.CharField(max_length=255)
    user_input = models.TextField()
    bot_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversation'  # Custom table name