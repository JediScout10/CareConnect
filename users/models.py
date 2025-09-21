# users\models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField 
from django.conf import settings
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=60, default="Unknown")
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True, null=True)
    action_plan = models.ForeignKey('ActionPlan', null=True, blank=True, on_delete=models.SET_NULL)
    objects = CustomUserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

# Shared choices
MENTAL_STATE_CHOICES = [
    ('Excellent', 'Excellent (16-20)'),
    ('Good', 'Good (11-15)'),
    ('Caution', 'Caution (0-10)'),
]

class MentalHealthTest(models.Model):
    TEST_TYPE_CHOICES = [
        ('PHQ-9', 'PHQ-9 (Depression)'),
        ('GAD-7', 'GAD-7 (Anxiety)'),
        ('PSS', 'PSS (Perceived Stress)'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mental_health_tests')
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES, default='PHQ-9')
    score = models.IntegerField()
    date_taken = models.DateTimeField(auto_now_add=True)
    related_actions = models.ManyToManyField('Action', related_name='tests')
    category = models.CharField(max_length=20, choices=MENTAL_STATE_CHOICES, blank=True)
    phq9_item9_score = models.IntegerField(null=True, blank=True)  # Track suicidal thoughts for caution logic

    def save(self, *args, **kwargs):
        # Set category based on score (legacy compatibility)
        if self.score >= 16:
            self.category = 'Excellent'
        elif 11 <= self.score <= 15:
            self.category = 'Good'
        else:
            self.category = 'Caution'
        
        # Check if this is a new record
        is_new = self.pk is None
        
        # Create the test record first
        super().save(*args, **kwargs)
        
        # Create recommendation based on test type and score (only for new records)
        if is_new:
            try:
                severity = self.get_severity()
                recommendation_type = self.get_recommendation_type(severity)
                
                # Create the recommendation
                TestRecommendation.objects.create(
                    test=self,
                    severity=severity,
                    recommendation_type=recommendation_type
                )
            except Exception as e:
                # Log the error but don't fail the test creation
                print(f"Error creating recommendation: {e}")
                pass

    def get_severity(self):
        """Determine severity level based on test type and score using exact clinical standards"""
        if self.test_type == 'PHQ-9':
            # PHQ-9: 0-4 None/Minimal, 5-9 Mild, 10-14 Moderate, 15-19 Moderately Severe, 20-27 Severe
            if 0 <= self.score <= 4:
                return 'None/Minimal'
            elif 5 <= self.score <= 9:
                return 'Mild'
            elif 10 <= self.score <= 14:
                return 'Moderate'
            elif 15 <= self.score <= 19:
                return 'Moderately Severe'
            elif 20 <= self.score <= 27:
                return 'Severe'
                
        elif self.test_type == 'GAD-7':
            # GAD-7: 0-4 Minimal, 5-9 Mild, 10-14 Moderate, 15-21 Severe
            if 0 <= self.score <= 4:
                return 'Minimal'
            elif 5 <= self.score <= 9:
                return 'Mild'
            elif 10 <= self.score <= 14:
                return 'Moderate'
            elif 15 <= self.score <= 21:
                return 'Severe'
                
        elif self.test_type == 'PSS':
            # PSS-10: 0-13 Low stress, 14-26 Moderate stress, 27-40 High stress
            if 0 <= self.score <= 13:
                return 'Low stress'
            elif 14 <= self.score <= 26:
                return 'Moderate stress'
            elif 27 <= self.score <= 40:
                return 'High stress'
        return 'Moderate'  # Default fallback
    
    def get_recommendation_type(self, severity):
        """Determine recommendation type based on severity"""
        if severity in ['None/Minimal', 'Minimal', 'Low stress', 'Mild']:
            return 'self_care'
        elif severity in ['Moderate', 'Moderate stress', 'Moderately Severe']:
            return 'chatbot'
        else:  # severe or high stress
            return 'counselor'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('users:test_detail', kwargs={'pk': self.pk})

    def needs_caution(self):
        """Determine if caution should be shown based on severity or PHQ-9 item 9"""
        severity = self.get_severity()
        
        # Show caution if in severe range
        if severity in ['Severe', 'High stress']:
            return True
            
        # For PHQ-9, show caution if item 9 (suicidal thoughts) > 0
        if self.test_type == 'PHQ-9' and self.phq9_item9_score and self.phq9_item9_score > 0:
            return True
            
        return False
    
    def get_color_class(self):
        """Get CSS color class based on severity"""
        severity = self.get_severity()
        
        if severity in ['None/Minimal', 'Minimal', 'Low stress']:
            return 'text-green-600 bg-green-100'
        elif severity in ['Mild', 'Moderate', 'Moderate stress', 'Moderately Severe']:
            return 'text-yellow-600 bg-yellow-100'
        else:  # Severe, High stress
            return 'text-red-600 bg-red-100'
    
    def get_display_text(self):
        """Get formatted display text for score and severity"""
        severity = self.get_severity()
        caution_text = " — Caution" if self.needs_caution() else ""
        return f"{self.test_type}: Score {self.score} — {severity}{caution_text}"

    def __str__(self):
        return f"{self.user.email} - {self.test_type} - {self.score} ({self.category})"

class ActionPlan(models.Model):
    category = models.CharField(max_length=20, choices=MENTAL_STATE_CHOICES, unique=True)
    title = models.CharField(max_length=100)
    steps = JSONField()
    
    def __str__(self):
        return f"{self.category} Plan"

class UserAction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'), 
        ('carried', 'Carried Forward'),
        ('archived', 'Archived')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    state_context = models.CharField(max_length=20, choices=MENTAL_STATE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    related_test = models.ForeignKey(
        MentalHealthTest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='actions'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]

    def complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.email} - {self.text} ({self.status})"
    
class UserCompletedAction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action_text = models.CharField(max_length=200)
    state_context = models.CharField(max_length=20, choices=MENTAL_STATE_CHOICES)
    status = models.CharField(
        max_length=10, 
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('carried', 'Carried Forward'),
            ('archived', 'Archived')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    related_test = models.ForeignKey(
        MentalHealthTest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='completed_actions'
    )
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['completed_at']),
        ]

    def save(self, *args, **kwargs):
     status_changed = False
     if self.completed_at and not self.status == 'completed':
        self.status = 'completed'
        status_changed = True
    
     if status_changed:
        super().save(*args, **kwargs, update_fields=['status'])
     else:
        super().save(*args, **kwargs)

    @property
    def test_context(self):
     """Backward compatibility alias"""
     return self.related_test

class Action(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Add any other fields you need
    
    def __str__(self):
        return self.name

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ('very_happy', 'Very Happy 😊'),
        ('happy', 'Happy 🙂'),
        ('neutral', 'Neutral 😐'),
        ('sad', 'Sad 😔'),
        ('very_sad', 'Very Sad 😢'),
    ]

    SYMPTOM_CHOICES = [
        ('none', 'Not at all'),
        ('mild', 'A little'),
        ('moderate', 'Quite a bit'),
        ('severe', 'Very much'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mood_entries')
    date = models.DateField(auto_now_add=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    anxiety_level = models.CharField(max_length=20, choices=SYMPTOM_CHOICES)
    depression_level = models.CharField(max_length=20, choices=SYMPTOM_CHOICES)
    stress_level = models.CharField(max_length=20, choices=SYMPTOM_CHOICES)
    energy_level = models.CharField(max_length=20, choices=SYMPTOM_CHOICES)
    notes = models.TextField(blank=True)
    sleep_hours = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    exercise_minutes = models.IntegerField(null=True, blank=True)
    social_interaction = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.mood}"


class TestRecommendation(models.Model):
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ]
    
    RECOMMENDATION_TYPE_CHOICES = [
        ('self_care', 'Self-Care'),
        ('chatbot', 'Chatbot & Resource Hub'),
        ('counselor', 'Counselor or Helpline'),
    ]
    
    test = models.ForeignKey(MentalHealthTest, on_delete=models.CASCADE, related_name='recommendations')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
    accepted = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.test.user.email} - {self.test.test_type} - {self.severity} - {self.recommendation_type}"


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    test_recommendation = models.ForeignKey(TestRecommendation, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_sessions')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    distress_level = models.IntegerField(null=True, blank=True, help_text="User's self-reported distress level (1-10)")
    
    def __str__(self):
        return f"{self.user.email} - Chat Session {self.started_at}"


class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.session.user.email} - {self.message_type} - {self.timestamp}"


class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('breathing', 'Breathing Technique'),
        ('journaling', 'Journaling Prompt'),
        ('stress_management', 'Stress Management Tip'),
        ('article', 'Article'),
        ('video', 'Video'),
        ('helpline', 'Helpline'),
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    content = models.TextField(help_text="Content, instructions, or URL for the resource")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} ({self.resource_type})"


class ResourceClick(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resource_clicks')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='clicks')
    chat_session = models.ForeignKey(ChatSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='resource_clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.resource.title} - {self.clicked_at}"