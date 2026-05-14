from django.contrib import admin
from django.urls import path, include
from apps.frontend.views import newspaper_frontpage
from .admin_views import force_sync_all

urlpatterns = [
    path('admin/force_sync_all/', force_sync_all, name='force_sync_all'),
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('jokes/', include('apps.dadjokes.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('news/', include('apps.news.urls')),
    path('', include('apps.frontend.urls')),
]
