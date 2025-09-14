from django import forms

class MeditationForm(forms.Form):
    DURATION_CHOICES = [
        (5, "5 minutes"),
        (10, "10 minutes"),
        (15, "15 minutes"),
    ]
    duration = forms.ChoiceField(choices=DURATION_CHOICES, widget=forms.Select)
