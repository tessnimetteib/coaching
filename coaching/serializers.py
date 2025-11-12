from rest_framework import serializers
from .models import (
    CoachingSession, CoachingMessage, CoachingExercise,
    UserExerciseCompletion, CoachingRecommendation,
    CoachingProgressMetric, DailyCheckIn, CoachNote
)


class CoachingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingMessage
        fields = ['id', 'sender', 'content', 'metadata', 'timestamp', 'is_read']
        read_only_fields = ['id', 'timestamp']


class CoachingSessionSerializer(serializers.ModelSerializer):
    recent_messages = serializers.SerializerMethodField()
    
    class Meta:
        model = CoachingSession
        fields = [
            'id', 'title', 'description', 'theme', 'status',
            'started_at', 'last_interaction', 'completed_at',
            'progress_percentage', 'total_messages', 'exercises_completed',
            'recent_messages'
        ]
        read_only_fields = ['id', 'started_at', 'last_interaction', 'total_messages']
    
    def get_recent_messages(self, obj):
        messages = obj.messages.all()[:10]
        return CoachingMessageSerializer(messages, many=True).data


class CoachingExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingExercise
        fields = [
            'id', 'title', 'description', 'exercise_type', 'theme',
            'difficulty_level', 'estimated_duration', 'instructions',
            'reflection_questions', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserExerciseCompletionSerializer(serializers.ModelSerializer):
    exercise = CoachingExerciseSerializer(read_only=True)
    exercise_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserExerciseCompletion
        fields = [
            'id', 'exercise', 'exercise_id', 'session', 'status',
            'assigned_at', 'started_at', 'completed_at',
            'user_notes', 'reflection_responses', 'rating'
        ]
        read_only_fields = ['id', 'assigned_at']


class CoachingRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingRecommendation
        fields = [
            'id', 'recommendation_type', 'title', 'description',
            'priority', 'metadata', 'is_acted_upon',
            'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class CoachingProgressMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachingProgressMetric
        fields = [
            'id', 'session', 'metric_name', 'metric_value',
            'metric_context', 'recorded_at'
        ]
        read_only_fields = ['id', 'recorded_at']


class DailyCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyCheckIn
        fields = [
            'id', 'date', 'mood', 'energy_level', 'stress_level',
            'notes', 'gratitude_entries', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CoachNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachNote
        fields = [
            'id', 'session', 'generated_by_ai', 'note_type',
            'title', 'content', 'priority', 'is_reviewed',
            'reviewed_by', 'reviewed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']