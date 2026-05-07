from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db import models
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import datetime

from apps.news.models import Article, Source
from apps.dadjokes.models import Joke, JokeView, JokeRating


def newspaper_frontpage(request):
    # Fetch articles from the last 48 hours for the newspaper view
    recent_time = timezone.now() - datetime.timedelta(hours=48)

    # Filter sources: Global sources (user=None) OR personal sources (user=request.user)
    if request.user.is_authenticated:
        allowed_sources = Source.objects.filter(models.Q(user__isnull=True) | models.Q(user=request.user))
    else:
        allowed_sources = Source.objects.filter(user__isnull=True)

    articles = Article.objects.filter(source__in=allowed_sources, publish_date__gte=recent_time).order_by('-publish_date')

    if not articles.exists():
        # Fallback if publish_date is null or no recent articles
        articles = Article.objects.filter(source__in=allowed_sources).order_by('-created_at')[:50]

    # Group by source for columns/sections
    grouped_articles = {}
    for article in articles:
        source_name = article.source.name
        if source_name not in grouped_articles:
            grouped_articles[source_name] = []
        grouped_articles[source_name].append(article)

    context = {
        'grouped_articles': grouped_articles,
        'today': timezone.now()
    }
    return render(request, 'news/frontpage.html', context)


def joke_of_the_day(request):
    today = timezone.now().date()
    # Find the joke used today
    joke = Joke.objects.filter(date_used=today).first()

    # If not found for today, maybe fallback to the latest one, or None
    if not joke:
        joke = Joke.objects.order_by('-date_used', '-created_at').first()

    # Track view
    if joke and request.user.is_authenticated:
        JokeView.objects.get_or_create(user=request.user, joke=joke)

    # Context
    user_rating = None
    if joke and request.user.is_authenticated:
        rating_obj = JokeRating.objects.filter(user=request.user, joke=joke).first()
        if rating_obj:
            user_rating = 'up' if rating_obj.is_thumbs_up else 'down'

    # Fallback checking
    is_fallback = False
    if joke and joke.date_used != today:
        is_fallback = True
    elif joke and joke.created_at.date() < today and joke.date_used == today:
        # It's an old joke reused today
        is_fallback = True

    # Counts
    view_count = joke.views.count() if joke else 0
    upvotes = joke.ratings.filter(is_thumbs_up=True).count() if joke else 0
    downvotes = joke.ratings.filter(is_thumbs_up=False).count() if joke else 0

    return render(request, 'dadjokes/joke_of_the_day.html', {
        'joke': joke,
        'user_rating': user_rating,
        'is_fallback': is_fallback,
        'view_count': view_count,
        'upvotes': upvotes,
        'downvotes': downvotes
    })


@login_required
def previous_jokes(request):
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in [10, 20, 50]:
        per_page = 10

    jokes_list = Joke.objects.exclude(date_used=timezone.now().date()).order_by('-date_used', '-created_at')

    paginator = Paginator(jokes_list, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dadjokes/previous_jokes.html', {
        'page_obj': page_obj,
        'per_page': per_page
    })
