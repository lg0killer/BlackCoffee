from django.db import models
from django.contrib.auth.models import User

class DadJokeSettings(models.Model):
    retry_limit = models.PositiveIntegerField(default=5, help_text="Number of times to retry fetching a new joke if we receive a duplicate ID.")

    class Meta:
        verbose_name = "Dad Joke Settings"
        verbose_name_plural = "Dad Joke Settings"

    def save(self, *args, **kwargs):
        # Enforce singleton
        if not self.pk and DadJokeSettings.objects.exists():
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return "Dad Joke Settings"

class Joke(models.Model):
    api_id = models.CharField(max_length=100, unique=True, help_text="The ID provided by the icanhazdadjoke API")
    content = models.TextField()
    date_used = models.DateField(null=True, blank=True, help_text="The date this was used as the Joke of the Day")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Joke {self.api_id} (used {self.date_used})"

class JokeView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joke_views')
    joke = models.ForeignKey(Joke, on_delete=models.CASCADE, related_name='views')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'joke')

    def __str__(self):
        return f"{self.user.username} viewed {self.joke.api_id}"

class JokeRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joke_ratings')
    joke = models.ForeignKey(Joke, on_delete=models.CASCADE, related_name='ratings')
    is_thumbs_up = models.BooleanField(help_text="True for thumbs up, False for thumbs down")
    rated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'joke')

    def __str__(self):
        return f"{self.user.username} rated {self.joke.api_id} {'Up' if self.is_thumbs_up else 'Down'}"
