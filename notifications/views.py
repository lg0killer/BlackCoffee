from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import NotificationPreference
from .forms import NotificationPreferenceForm

@login_required
def manage_notifications(request):
    preferences = NotificationPreference.objects.filter(user=request.user)

    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST)
        if form.is_valid():
            pref = form.save(commit=False)
            pref.user = request.user
            # Check if this combination already exists
            if not NotificationPreference.objects.filter(user=pref.user, platform=pref.platform, time_of_day=pref.time_of_day).exists():
                pref.save()
            return redirect('manage_notifications')
    else:
        form = NotificationPreferenceForm()

    return render(request, 'notifications/manage.html', {
        'preferences': preferences,
        'form': form,
    })

@login_required
def delete_notification(request, pk):
    pref = get_object_or_404(NotificationPreference, pk=pk, user=request.user)
    if request.method == 'POST':
        pref.delete()
    return redirect('manage_notifications')
