from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import DadJokeSettings, Joke, JokeView, JokeRating

@admin.register(DadJokeSettings)
class DadJokeSettingsAdmin(admin.ModelAdmin):
    change_list_template = "admin/dadjokes/dadjokesettings/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch_now/', self.admin_site.admin_view(self.fetch_now), name='dadjokes_fetch_now'),
        ]
        return custom_urls + urls

    def fetch_now(self, request):
        from .tasks import fetch_joke_of_the_day
        fetch_joke_of_the_day.delay()
        messages.success(request, "Fetch Joke of the Day task has been queued.")
        return HttpResponseRedirect("../")


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
