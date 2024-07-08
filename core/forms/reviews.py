from django import forms
from ..models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }


class TutorResponseForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['response']
        widgets = {
            'response': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        }
