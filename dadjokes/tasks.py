import requests
import datetime
from django.utils import timezone
from celery import shared_task
from .models import Joke, DadJokeSettings

@shared_task
def fetch_joke_of_the_day():
    settings = DadJokeSettings.objects.first()
    retry_limit = settings.retry_limit if settings else 5

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'BlackCoffee Project (https://github.com/yourusername/blackcoffee)'
    }

    today = timezone.now().date()

    # Check if a joke is already fetched for today
    if Joke.objects.filter(date_used=today).exists():
        return "Joke already fetched for today."

    attempts = 0
    new_joke_found = False

    while attempts < retry_limit:
        attempts += 1
        try:
            response = requests.get('https://icanhazdadjoke.com/', headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            joke_id = data.get('id')
            joke_content = data.get('joke')

            if joke_id and joke_content:
                # Check if we already have this joke
                if not Joke.objects.filter(api_id=joke_id).exists():
                    Joke.objects.create(
                        api_id=joke_id,
                        content=joke_content,
                        date_used=today
                    )
                    new_joke_found = True
                    break
        except requests.RequestException as e:
            print(f"Error fetching joke: {e}")
            continue

    if not new_joke_found:
        # Fallback to the oldest joke we have (least recently used)
        oldest_joke = Joke.objects.order_by('date_used', 'created_at').first()
        if oldest_joke:
            # Create a duplicate entry for today or update its date_used?
            # It's better to update its date_used so it cycles. But wait, if we update its date_used,
            # we lose the history of when it was *first* used.
            # Alternatively, we could create a new daily record or just update it.
            # Let's just update the date_used so it becomes the current joke of the day.
            oldest_joke.date_used = today
            oldest_joke.save()
            return f"Fallback to oldest joke: {oldest_joke.api_id}"
        else:
            # We have absolutely no jokes in the DB and failed to fetch.
            # Store a temporary error joke or just do nothing.
            return "Failed to fetch any joke and database is empty."

    return "New joke fetched successfully."
