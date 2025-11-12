from django.contrib import admin
from .models import (
    CoachingSession, CoachingMessage, CoachingExercise,
    UserExerciseCompletion, CoachingRecommendation,
    CoachingProgressMetric, DailyCheckIn, CoachNote
)


@admin.register(CoachingSession)
class CoachingSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'theme', 'status', 'progress_percentage', 'started_at']
    list_filter = ['status', 'theme', 'started_at']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['started_at', 'last_interaction', 'total_messages', 'exercises_completed']


@admin.register(CoachingMessage)
class CoachingMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'sender', 'timestamp', 'is_read']
    list_filter = ['sender', 'timestamp', 'is_read']
    search_fields = ['content', 'session__user__username']
    readonly_fields = ['timestamp']


@admin.register(CoachingExercise)
class CoachingExerciseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'exercise_type', 'theme', 'difficulty_level', 'estimated_duration', 'is_active']
    list_filter = ['exercise_type', 'theme', 'difficulty_level', 'is_active']
    search_fields = ['title', 'description']


@admin.register(UserExerciseCompletion)
class UserExerciseCompletionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'exercise', 'session', 'status', 'rating', 'assigned_at', 'completed_at']
    list_filter = ['status', 'assigned_at', 'completed_at']
    search_fields = ['user__username', 'exercise__title']
    readonly_fields = ['assigned_at']


@admin.register(CoachingRecommendation)
class CoachingRecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'recommendation_type', 'title', 'priority', 'is_acted_upon', 'created_at']
    list_filter = ['recommendation_type', 'priority', 'is_acted_upon', 'created_at']
    search_fields = ['user__username', 'title', 'description']


@admin.register(CoachingProgressMetric)
class CoachingProgressMetricAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session', 'metric_name', 'metric_value', 'recorded_at']
    list_filter = ['metric_name', 'recorded_at']
    search_fields = ['user__username', 'metric_name']


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'date', 'mood', 'energy_level', 'stress_level']
    list_filter = ['date', 'mood']
    search_fields = ['user__username', 'notes']


@admin.register(CoachNote)
class CoachNoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session', 'note_type', 'title', 'priority', 'is_reviewed', 'created_at']
    list_filter = ['note_type', 'priority', 'is_reviewed', 'generated_by_ai', 'created_at']
    search_fields = ['user__username', 'title', 'content']