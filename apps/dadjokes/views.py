from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Joke, JokeRating

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
