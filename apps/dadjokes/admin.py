from django.contrib import admin
from .models import DadJokeSettings, Joke, JokeView, JokeRating

@admin.register(DadJokeSettings)
class DadJokeSettingsAdmin(admin.ModelAdmin):
    pass

@admin.register(Joke)
class JokeAdmin(admin.ModelAdmin):
    list_display = ('api_id', 'date_used', 'created_at')
    search_fields = ('content', 'api_id')
    list_filter = ('date_used',)

@admin.register(JokeView)
class JokeViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'joke', 'viewed_at')

@admin.register(JokeRating)
class JokeRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'joke', 'is_thumbs_up', 'rated_at')
