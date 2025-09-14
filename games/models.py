from django.db import models
from django.conf import settings

class Game(models.Model):
    GAME_TYPES = [
        ('memory', 'Memory Game'),
        ('puzzle', 'Puzzle'),
        ('breathing', 'Breathing Exercise'),
        ('meditation', 'Meditation Game'),
    ]

    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    game_type = models.CharField(max_length=20, choices=GAME_TYPES)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS)
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_game_type_display()})"

class GameSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)  # Duration in seconds
    completed = models.BooleanField(default=False)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        return f"{self.user.email} - {self.game.name} ({self.played_at})"

class GameProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    high_score = models.IntegerField(default=0)
    total_sessions = models.IntegerField(default=0)
    total_duration = models.IntegerField(default=0)  # Total duration in seconds
    last_played = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'game']

    def __str__(self):
        return f"{self.user.email} - {self.game.name} (High Score: {self.high_score})"
