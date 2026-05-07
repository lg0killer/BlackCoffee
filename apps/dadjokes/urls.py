from django.urls import path
from . import views

urlpatterns = [
    path('rate-joke/<int:joke_id>/', views.rate_joke, name='rate_joke'),
]
