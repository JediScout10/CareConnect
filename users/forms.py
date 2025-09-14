# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, MentalHealthTest, MoodEntry


class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.name = self.cleaned_data['name']
        if commit:
            user.save()
        return user
    
    
class CustomLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class MentalHealthTestForm(forms.ModelForm):
    class Meta:
        model = MentalHealthTest
        fields = ['score']

    def clean_score(self):
        score = self.cleaned_data.get('score')
        print("Cleaned Score:", score)  
        return score

class MoodEntryForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood', 'anxiety_level', 'depression_level', 'stress_level', 
                 'energy_level', 'notes', 'sleep_hours', 'exercise_minutes', 
                 'social_interaction']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'sleep_hours': forms.NumberInput(attrs={
                'min': 0,
                'max': 24,
                'step': 0.5,
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'exercise_minutes': forms.NumberInput(attrs={
                'min': 0,
                'max': 480,
                'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'mood': forms.RadioSelect(attrs={
                'class': 'grid grid-cols-5 gap-4'
            }),
            'anxiety_level': forms.RadioSelect(attrs={
                'class': 'grid grid-cols-4 gap-2'
            }),
            'depression_level': forms.RadioSelect(attrs={
                'class': 'grid grid-cols-4 gap-2'
            }),
            'stress_level': forms.RadioSelect(attrs={
                'class': 'grid grid-cols-4 gap-2'
            }),
            'energy_level': forms.RadioSelect(attrs={
                'class': 'grid grid-cols-4 gap-2'
            }),
            'social_interaction': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        sleep_hours = cleaned_data.get('sleep_hours')
        exercise_minutes = cleaned_data.get('exercise_minutes')

        if sleep_hours is not None and (sleep_hours < 0 or sleep_hours > 24):
            self.add_error('sleep_hours', 'Sleep hours must be between 0 and 24')

        if exercise_minutes is not None and (exercise_minutes < 0 or exercise_minutes > 480):
            self.add_error('exercise_minutes', 'Exercise minutes must be between 0 and 480')

        return cleaned_data


# Standardized Mental Health Assessment Forms

class PHQ9Form(forms.Form):
    """
    Patient Health Questionnaire-9 (PHQ-9) for depression screening
    9 questions with 4-point scale: 0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day
    """
    
    CHOICES = [
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day'),
    ]
    
    # PHQ-9 Questions
    q1 = forms.ChoiceField(
        label="Little interest or pleasure in doing things",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q2 = forms.ChoiceField(
        label="Feeling down, depressed, or hopeless",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q3 = forms.ChoiceField(
        label="Trouble falling or staying asleep, or sleeping too much",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q4 = forms.ChoiceField(
        label="Feeling tired or having little energy",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q5 = forms.ChoiceField(
        label="Poor appetite or overeating",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q6 = forms.ChoiceField(
        label="Feeling bad about yourself - or that you are a failure or have let yourself or your family down",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q7 = forms.ChoiceField(
        label="Trouble concentrating on things, such as reading the newspaper or watching television",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q8 = forms.ChoiceField(
        label="Moving or speaking so slowly that other people could have noticed, or the opposite - being so fidgety or restless that you have been moving around a lot more than usual",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q9 = forms.ChoiceField(
        label="Thoughts that you would be better off dead, or of hurting yourself",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    def calculate_score(self):
        """Calculate total PHQ-9 score"""
        if not self.is_valid():
            return None
        
        score = 0
        for i in range(1, 10):  # q1 to q9
            score += int(self.cleaned_data.get(f'q{i}', 0))
        return score


class GAD7Form(forms.Form):
    """
    Generalized Anxiety Disorder 7-item scale (GAD-7)
    7 questions with 4-point scale: 0=Not at all, 1=Several days, 2=More than half the days, 3=Nearly every day
    """
    
    CHOICES = [
        (0, 'Not at all'),
        (1, 'Several days'),
        (2, 'More than half the days'),
        (3, 'Nearly every day'),
    ]
    
    # GAD-7 Questions
    q1 = forms.ChoiceField(
        label="Feeling nervous, anxious, or on edge",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q2 = forms.ChoiceField(
        label="Not being able to stop or control worrying",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q3 = forms.ChoiceField(
        label="Worrying too much about different things",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q4 = forms.ChoiceField(
        label="Trouble relaxing",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q5 = forms.ChoiceField(
        label="Being so restless that it's hard to sit still",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q6 = forms.ChoiceField(
        label="Becoming easily annoyed or irritable",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q7 = forms.ChoiceField(
        label="Feeling afraid, as if something awful might happen",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    def calculate_score(self):
        """Calculate total GAD-7 score"""
        if not self.is_valid():
            return None
        
        score = 0
        for i in range(1, 8):  # q1 to q7
            score += int(self.cleaned_data.get(f'q{i}', 0))
        return score


class PSS10Form(forms.Form):
    """
    Perceived Stress Scale 10-item version (PSS-10)
    10 questions with 5-point scale: 0=Never, 1=Almost never, 2=Sometimes, 3=Fairly often, 4=Very often
    Note: Questions 4, 5, 7, 8 are reverse-scored
    """
    
    CHOICES = [
        (0, 'Never'),
        (1, 'Almost never'),
        (2, 'Sometimes'),
        (3, 'Fairly often'),
        (4, 'Very often'),
    ]
    
    # PSS-10 Questions
    q1 = forms.ChoiceField(
        label="In the last month, how often have you been upset because of something that happened unexpectedly?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q2 = forms.ChoiceField(
        label="In the last month, how often have you felt that you were unable to control the important things in your life?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q3 = forms.ChoiceField(
        label="In the last month, how often have you felt nervous and 'stressed'?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q4 = forms.ChoiceField(
        label="In the last month, how often have you felt confident about your ability to handle your personal problems?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q5 = forms.ChoiceField(
        label="In the last month, how often have you felt that things were going your way?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q6 = forms.ChoiceField(
        label="In the last month, how often have you found that you could not cope with all the things that you had to do?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q7 = forms.ChoiceField(
        label="In the last month, how often have you been able to control irritations in your life?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q8 = forms.ChoiceField(
        label="In the last month, how often have you felt that you were on top of things?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q9 = forms.ChoiceField(
        label="In the last month, how often have you been angered because of things that were outside of your control?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    q10 = forms.ChoiceField(
        label="In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
        choices=CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    
    def calculate_score(self):
        """Calculate total PSS-10 score with reverse scoring for questions 4, 5, 7, 8"""
        if not self.is_valid():
            return None
        
        score = 0
        reverse_questions = [4, 5, 7, 8]  # Questions that need reverse scoring
        
        for i in range(1, 11):  # q1 to q10
            raw_score = int(self.cleaned_data.get(f'q{i}', 0))
            
            if i in reverse_questions:
                # Reverse score: 0->4, 1->3, 2->2, 3->1, 4->0
                score += (4 - raw_score)
            else:
                score += raw_score
                
        return score


