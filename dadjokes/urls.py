from django.urls import path
from . import views

urlpatterns = [
    path('joke-of-the-day/', views.joke_of_the_day, name='joke_of_the_day'),
    path('previous-jokes/', views.previous_jokes, name='previous_jokes'),
    path('rate-joke/<int:joke_id>/', views.rate_joke, name='rate_joke'),
]
