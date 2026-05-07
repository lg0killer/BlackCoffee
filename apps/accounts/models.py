from django.db import models
from django.contrib.auth.models import User
import pytz

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    TIMEZONES = tuple(zip(pytz.common_timezones, pytz.common_timezones))
    timezone = models.CharField(max_length=32, choices=TIMEZONES, default='UTC')

    def __str__(self):
        return f"{self.user.username}'s profile"

# Ensure UserProfile gets created automatically when User is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    profile.save()
