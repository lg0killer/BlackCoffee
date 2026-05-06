from django.shortcuts import render
from django.utils import timezone
from django.db import models
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Article, Category, Source
from .forms import PersonalSourceForm
import datetime

@login_required
def manage_sources(request):
    sources = Source.objects.filter(user=request.user)

    if request.method == 'POST':
        form = PersonalSourceForm(request.POST)
        if form.is_valid():
            new_source = form.save(commit=False)
            new_source.user = request.user
            new_source.save()
            return redirect('manage_sources')
    else:
        form = PersonalSourceForm()

    return render(request, 'news/manage_sources.html', {
        'sources': sources,
        'form': form,
    })

@login_required
def delete_source(request, pk):
    source = get_object_or_404(Source, pk=pk, user=request.user)
    if request.method == 'POST':
        source.delete()
    return redirect('manage_sources')

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
