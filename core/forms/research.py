# forms.py
from django import forms
from core.models import Subject

DAYS_OF_WEEK = [
    ('---------', '---------'),
    ('monday', 'Monday'),
    ('tuesday', 'Tuesday'),
    ('wednesday', 'Wednesday'),
    ('thursday', 'Thursday'),
    ('friday', 'Friday'),
    ('saturday', 'Saturday'),
    ('sunday', 'Sunday'),
]


class TutorSearchForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), required=False)
    min_hourly_rate = forms.DecimalField(max_digits=6, decimal_places=2, required=False)
    max_hourly_rate = forms.DecimalField(max_digits=6, decimal_places=2, required=False)
    location = forms.CharField(max_length=255, required=False)
    min_rating = forms.FloatField(min_value=0, max_value=5, required=False)
    available_on_day = forms.ChoiceField(choices=DAYS_OF_WEEK, required=False)
    available_from = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    available_to = forms.TimeField(required=False, widget=forms.TimeInput(format='%H:%M'))
    experience = forms.IntegerField(min_value=0, required=False)

    def clean(self):
        cleaned_data = super().clean()
        available_from = cleaned_data.get("available_from")
        available_to = cleaned_data.get("available_to")
        available_on_day = cleaned_data.get("available_on_day")

        if available_on_day == '---------':
            cleaned_data['available_on_day'] = None

        if available_from and available_to and available_from >= available_to:
            raise forms.ValidationError("Available from time must be before available to time.")

        return cleaned_data
