from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Joke, JokeView, JokeRating

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

@login_required
@require_POST
def rate_joke(request, joke_id):
    joke = get_object_or_404(Joke, id=joke_id)
    rating_type = request.POST.get('rating') # 'up', 'down', or 'none' (unlike)

    if rating_type == 'none':
        JokeRating.objects.filter(user=request.user, joke=joke).delete()
    elif rating_type in ['up', 'down']:
        is_thumbs_up = rating_type == 'up'
        obj, created = JokeRating.objects.update_or_create(
            user=request.user, joke=joke,
            defaults={'is_thumbs_up': is_thumbs_up}
        )

    upvotes = joke.ratings.filter(is_thumbs_up=True).count()
    downvotes = joke.ratings.filter(is_thumbs_up=False).count()

    return JsonResponse({
        'status': 'success',
        'upvotes': upvotes,
        'downvotes': downvotes
    })
