from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

@staff_member_required
def force_sync_all(request):
    try:
        from apps.news.tasks import catchup_scrapers
        catchup_scrapers.delay()
        messages.success(request, "Force sync triggered successfully in the background.")
    except Exception as e:
        logger.error(f"Error triggering force sync: {e}")
        messages.warning(request, "Could not queue sync task. Make sure Celery/Redis are running.")
    return redirect(request.META.get('HTTP_REFERER', 'admin:index'))
