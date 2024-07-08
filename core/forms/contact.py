from django import forms
from core.models import Lesson


class BookLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['subject', 'booking_date', 'start_time', 'end_time']


class ModifyLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['subject', 'booking_date', 'start_time', 'end_time', 'status']


class DeleteLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = []
