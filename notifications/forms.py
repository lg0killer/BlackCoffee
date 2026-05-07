from django import forms
from .models import NotificationPreference

class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ['platform', 'time_of_day', 'is_active']
        widgets = {
            'time_of_day': forms.TimeInput(format='%H:%M', attrs={'type': 'time'})
        }
