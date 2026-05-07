from django.urls import path
from . import views

urlpatterns = [
    path('', views.newspaper_frontpage, name='home'),
    path('joke-of-the-day/', views.joke_of_the_day, name='joke_of_the_day'),
    path('previous-jokes/', views.previous_jokes, name='previous_jokes'),
]
