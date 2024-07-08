from django import forms
from django.core.exceptions import ValidationError

from ..models import Tutor, TutorAvailability, Profile, Subject
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext_lazy as _


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['birth_date', 'gender', 'location', 'address', 'phone', 'is_tutor']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter your location'}),
            'address': forms.TextInput(attrs={'placeholder': 'Enter your address'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'is_tutor': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class TutorEditForm(forms.ModelForm):
    class Meta:
        model = Tutor
        fields = ['subjects', 'hourly_rate', 'qualifications', 'experience', 'bio']
        widgets = {
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super(TutorEditForm, self).__init__(*args, **kwargs)
        self.fields['subjects'].widget = forms.CheckboxSelectMultiple()
        self.fields['subjects'].queryset = Subject.objects.all()
        for field in self.fields.values():
            field.required = False


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class TutorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TutorAvailability
        fields = ['tutor', 'day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
            'day_of_week': forms.TextInput(attrs={'placeholder': 'e.g., Monday'}),
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'is_available': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        tutor = kwargs.pop('tutor', None)
        super().__init__(*args, **kwargs)
        if tutor:
            self.fields['tutor'].initial = tutor
            self.fields['tutor'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        tutor = cleaned_data.get('tutor')
        day_of_week = cleaned_data.get('day_of_week')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if self.instance.pk is None:
            if TutorAvailability.objects.filter(tutor=tutor, day_of_week=day_of_week, start_time=start_time,
                                                end_time=end_time).exists():
                raise ValidationError(_('Availability with this Tutor, Day of week, Start time, and End time already '
                                        'exists.'))

        return cleaned_data
