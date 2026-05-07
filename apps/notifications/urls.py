from django.urls import path
from . import views

urlpatterns = [
    path('', views.manage_notifications, name='manage_notifications'),
    path('delete/<int:pk>/', views.delete_notification, name='delete_notification'),
]
