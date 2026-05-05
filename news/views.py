from django.shortcuts import render
from django.utils import timezone
from .models import Article, Category, Source
import datetime

def newspaper_frontpage(request):
    # Fetch articles from the last 48 hours for the newspaper view
    recent_time = timezone.now() - datetime.timedelta(hours=48)
    articles = Article.objects.filter(publish_date__gte=recent_time).order_by('-publish_date')

    if not articles.exists():
        # Fallback if publish_date is null or no recent articles
        articles = Article.objects.all().order_by('-created_at')[:50]

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
