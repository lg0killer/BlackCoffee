from django import forms
from .models import Source

class PersonalSourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ['name', 'url', 'scrape_type']
