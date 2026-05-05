from django.contrib import admin
from django.urls import path
from news.views import newspaper_frontpage

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', newspaper_frontpage, name='home'),
]
