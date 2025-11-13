from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CoachingSession(models.Model):
    """Model for tracking coaching sessions between user and AI Coach"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_sessions')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    theme = models.CharField(max_length=100, blank=True)  # stress, assertivité, confiance, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progression tracking
    progress_percentage = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    exercises_completed = models.IntegerField(default=0)

    # Conversation state for the static coach (simple finite-state)
    session_state = models.CharField(max_length=50, default='idle')  # NEW FIELD
    
    class Meta:
        ordering = ['-last_interaction']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class CoachingMessage(models.Model):
    """Model for storing conversation messages"""
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI Coach'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional context
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender} - {self.timestamp}"


class CoachingExercise(models.Model):
    """Model for coaching exercises"""
    EXERCISE_TYPES = [
        ('cbc', 'Cognitive Behavioral Coaching'),
        ('mindfulness', 'Mindfulness & Pleine Conscience'),
        ('smart_goals', 'Objectifs SMART'),
        ('gratitude', 'Journal de Gratitude'),
        ('visualization', 'Visualisation'),
        ('role_play', 'Jeux de Rôle'),
        ('breathing', 'Exercices de Respiration'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    exercise_type = models.CharField(max_length=50, choices=EXERCISE_TYPES)
    theme = models.CharField(max_length=100, blank=True)  # stress, assertivité, etc.
    difficulty_level = models.IntegerField(default=1)  # 1-5
    estimated_duration = models.IntegerField(help_text="Duration in minutes", default=5)
    instructions = models.TextField(blank=True)
    reflection_questions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class UserExerciseCompletion(models.Model):
    """Track user's exercise completions"""
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_completions')
    exercise = models.ForeignKey(CoachingExercise, on_delete=models.CASCADE)
    session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, related_name='exercise_completions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User feedback
    user_notes = models.TextField(blank=True)
    reflection_responses = models.JSONField(default=dict)
    rating = models.IntegerField(null=True, blank=True)  # 1-5
    
    class Meta:
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.title}"


class CoachingRecommendation(models.Model):
    """AI-generated recommendations for users"""
    RECOMMENDATION_TYPES = [
        ('exercise', 'Exercise'),
        ('resource', 'Resource'),
        ('theme', 'Theme'),
        ('break', 'Break Suggestion'),
        ('challenge', 'Challenge'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_recommendations')
    session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, null=True, blank=True)
    recommendation_type = models.CharField(max_length=50, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.IntegerField(default=3)  # 1-5, 5 being highest
    metadata = models.JSONField(default=dict)  # Links to exercises, resources, etc.
    is_acted_upon = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class CoachingProgressMetric(models.Model):
    """Track progress metrics over time"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_metrics')
    session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, null=True, blank=True)
    
    # Metrics
    metric_name = models.CharField(max_length=100)  # stress_level, confidence, motivation, etc.
    metric_value = models.FloatField()
    metric_context = models.JSONField(default=dict)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['metric_name', '-recorded_at']
        indexes = [
            models.Index(fields=['user', 'metric_name', '-recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.metric_name}: {self.metric_value}"


class DailyCheckIn(models.Model):
    """Daily check-in for mood and energy tracking"""
    MOOD_CHOICES = [
        (1, 'Très Mauvais'),
        (2, 'Mauvais'),
        (3, 'Neutre'),
        (4, 'Bon'),
        (5, 'Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_checkins')
    date = models.DateField(default=timezone.now)
    mood = models.IntegerField(choices=MOOD_CHOICES)
    energy_level = models.IntegerField()  # 1-10
    stress_level = models.IntegerField()  # 1-10
    notes = models.TextField(blank=True)
    gratitude_entries = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"


class CoachNote(models.Model):
    """Notes for human coaches about AI interactions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coach_notes')
    session = models.ForeignKey(CoachingSession, on_delete=models.CASCADE, related_name='coach_notes', null=True, blank=True)
    generated_by_ai = models.BooleanField(default=True)
    
    note_type = models.CharField(max_length=50)  # alert, insight, recommendation, etc.
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.IntegerField(default=3)  # 1-5
    
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_notes')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Note for {self.user.username} - {self.title}"


class AssessmentResult(models.Model):
    """
    Static/mock assessment storage for NextMind test results.
    Keeps Big Five, DISC, wellbeing and resilience results and recommendations.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assessments")
    session = models.ForeignKey(CoachingSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessments")
    big_five = models.JSONField(default=dict)        # e.g. {"openness": 18, "conscientiousness": 15, ...}
    disc = models.JSONField(default=dict)            # e.g. {"D": 6, "I": 10, "S": 8, "C": 6}
    wellbeing_score = models.IntegerField(default=0) # 0-30
    resilience_score = models.IntegerField(default=0)# 0-40
    recommendations = models.JSONField(default=list) # array of strings or dicts
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Assessment {self.user.username} @ {self.created_at.isoformat()}"