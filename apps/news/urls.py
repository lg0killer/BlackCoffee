from django.urls import path
from . import views

urlpatterns = [
    path('manage-sources/', views.manage_sources, name='manage_sources'),
    path('delete-source/<int:pk>/', views.delete_source, name='delete_source'),
]
