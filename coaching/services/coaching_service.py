from django.utils import timezone
from django.db.models import Avg, Count, Q
from datetime import timedelta
from typing import Dict, List, Optional

from ..models import (
    CoachingSession, CoachingMessage, CoachingExercise,
    UserExerciseCompletion, CoachingRecommendation,
    CoachingProgressMetric, DailyCheckIn, CoachNote
)


class CoachingService:
    """Service layer for AI Coaching functionality"""
    
    @staticmethod
    def create_session(user, title: str, theme: str = '', description: str = ''):
        """Create a new coaching session"""
        session = CoachingSession.objects.create(
            user=user,
            title=title,
            theme=theme,
            description=description,
            status='active'
        )
        
        CoachingMessage.objects.create(
            session=session,
            sender='ai',
            content=f"Bonjour {user.first_name or user.username}! Je suis votre Coach IA NextMind."
        )
        
        return session
    
    @staticmethod
    def add_message(session, sender: str, content: str, metadata: dict = None):
        """Add a message to the coaching session"""
        message = CoachingMessage.objects.create(
            session=session,
            sender=sender,
            content=content,
            metadata=metadata or {}
        )
        
        session.total_messages += 1
        session.last_interaction = timezone.now()
        session.save()
        
        return message
    
    @staticmethod
    def get_session_history(session, limit: int = 50):
        """Get conversation history for a session"""
        return session.messages.all()[:limit]
    
    @staticmethod
    def assign_exercise(user, exercise, session):
        """Assign an exercise to a user"""
        completion = UserExerciseCompletion.objects.create(
            user=user,
            exercise=exercise,
            session=session,
            status='assigned'
        )
        
        CoachingMessage.objects.create(
            session=session,
            sender='ai',
            content=f"Nouvel exercice: {exercise.title}. Durée: {exercise.estimated_duration} min.",
            metadata={'exercise_id': exercise.id}
        )
        
        return completion
    
    @staticmethod
    def complete_exercise(completion, user_notes='', reflection_responses=None, rating=None):
        """Mark an exercise as completed"""
        completion.status = 'completed'
        completion.completed_at = timezone.now()
        completion.user_notes = user_notes
        completion.reflection_responses = reflection_responses or {}
        completion.rating = rating
        completion.save()
        
        session = completion.session
        session.exercises_completed += 1
        session.save()
    
    @staticmethod
    def record_daily_checkin(user, mood, energy_level, stress_level, notes='', gratitude_entries=None):
        """Record daily check-in"""
        checkin, created = DailyCheckIn.objects.update_or_create(
            user=user,
            date=timezone.now().date(),
            defaults={
                'mood': mood,
                'energy_level': energy_level,
                'stress_level': stress_level,
                'notes': notes,
                'gratitude_entries': gratitude_entries or []
            }
        )
        return checkin
    
    @staticmethod
    def get_recommended_exercises(user, theme=None, limit=5):
        """Get recommended exercises"""
        completed_ids = UserExerciseCompletion.objects.filter(
            user=user, status='completed'
        ).values_list('exercise_id', flat=True)
        
        exercises = CoachingExercise.objects.filter(is_active=True).exclude(id__in=completed_ids)
        
        if theme:
            exercises = exercises.filter(theme=theme)
        
        return exercises.order_by('difficulty_level')[:limit]