# meditation\models.py
from django.db import models
from django.utils.timezone import timedelta, timezone
from django.conf import settings

class MeditationSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meditation_sessions')
    duration = models.IntegerField(help_text='Duration in minutes')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)  # Allow null temporarily for migration
    
    class Meta:
        ordering = ['-date', '-created_at']
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username}'s meditation session on {self.date}"

def get_user_stats(user):
    """ Fetch meditation stats for a user. """
    sessions = MeditationSession.objects.filter(user=user)
    
    total_time = sum(session.duration for session in sessions)
    total_sessions = sessions.count()
    
    # Calculate streak
    today = timezone.now().date()
    streak = 0
    last_date = today
    
    # Get all unique dates with sessions
    session_dates = set(session.date for session in sessions)
    
    # Check consecutive days starting from today
    while last_date in session_dates:
        streak += 1
        last_date -= timedelta(days=1)

    return {
        "total_time": total_time,
        "total_sessions": total_sessions,
        "streak": streak
    }
