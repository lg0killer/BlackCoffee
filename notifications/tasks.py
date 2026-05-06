from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from .models import NotificationPreference, NotificationLog
from dadjokes.models import Joke
import pytz

@shared_task
def process_notifications():
    # 1. Check current UTC time
    now_utc = timezone.now()

    # 2. Get today's Joke of the Day
    # Note: 'today' in this context means UTC today, as Joke of the day is fetched at midnight UTC.
    today_utc = now_utc.date()
    joke = Joke.objects.filter(date_used=today_utc).first()

    if not joke:
        joke = Joke.objects.order_by('-date_used', '-created_at').first()

    if not joke:
        return "No jokes available to send."

    # 3. Find active preferences
    preferences = NotificationPreference.objects.filter(is_active=True)

    sent_count = 0

    for pref in preferences:
        # Check if already sent today for this preference
        if NotificationLog.objects.filter(preference=pref, date_sent=today_utc).exists():
            continue

        # Determine user's current local time
        try:
            user_tz = pytz.timezone(pref.user.userprofile.timezone)
        except Exception:
            user_tz = pytz.UTC

        user_local_time = now_utc.astimezone(user_tz)

        # We want to check if the user's local time matches the preference time
        # Since this task runs every minute, we check if hour and minute match
        if user_local_time.hour == pref.time_of_day.hour and user_local_time.minute == pref.time_of_day.minute:

            # Send Notification based on platform
            if pref.platform == 'email' and pref.user.email:
                try:
                    send_mail(
                        'Joke of the Day - BlackCoffee',
                        f'Your joke of the day:\n\n{joke.content}',
                        'noreply@blackcoffee.local', # Change to your actual from email
                        [pref.user.email],
                        fail_silently=False,
                    )
                    NotificationLog.objects.create(preference=pref, date_sent=today_utc, status='Success')
                    sent_count += 1
                except Exception as e:
                    NotificationLog.objects.create(preference=pref, date_sent=today_utc, status=f'Failed: {str(e)}')

    return f"Processed notifications. Sent: {sent_count}"
