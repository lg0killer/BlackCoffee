from django.contrib import admin
from django.urls import path, include
from news.views import newspaper_frontpage

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('jokes/', include('dadjokes.urls')),
    path('notifications/', include('notifications.urls')),
    path('news/', include('news.urls')),
    path('', newspaper_frontpage, name='home'),
]
