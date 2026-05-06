from django.db import models
from django.contrib.auth.models import User

class NotificationPreference(models.Model):
    PLATFORM_CHOICES = [
        ('email', 'Email'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='email')

    # Store time as HH:MM format (24 hour)
    time_of_day = models.TimeField(help_text="The local time of day to send the notification (based on your profile timezone)")

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'platform', 'time_of_day')

    def __str__(self):
        return f"{self.user.username} - {self.get_platform_display()} at {self.time_of_day}"

class NotificationLog(models.Model):
    preference = models.ForeignKey(NotificationPreference, on_delete=models.CASCADE)
    date_sent = models.DateField()
    status = models.CharField(max_length=50)

    class Meta:
        unique_together = ('preference', 'date_sent')
