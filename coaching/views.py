from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """Dashboard view"""
    from .models import CoachingSession, UserExerciseCompletion, DailyCheckIn, CoachingExercise
    from django.db.models import Avg
    from datetime import timedelta
    from django.utils import timezone
    
    user = request.user
    
    # Get stats
    stats = {
        'active_sessions': CoachingSession.objects.filter(user=user, status='active').count(),
        'exercises_completed': UserExerciseCompletion.objects.filter(user=user, status='completed').count(),
        'average_mood': 0,
        'average_stress': 0,
    }
    
    # Get recent check-ins
    recent_checkins = DailyCheckIn.objects.filter(
        user=user,
        date__gte=timezone.now().date() - timedelta(days=30)
    ).aggregate(
        avg_mood=Avg('mood'),
        avg_stress=Avg('stress_level')
    )
    
    stats['average_mood'] = round(recent_checkins['avg_mood'] or 0, 1)
    stats['average_stress'] = round(recent_checkins['avg_stress'] or 0, 1)
    
    # Get recommended exercises
    from .services import CoachingService
    recommended_exercises = CoachingService.get_recommended_exercises(user, limit=3)
    
    context = {
        'stats': stats,
        'recommended_exercises': recommended_exercises,
    }
    
    return render(request, 'coaching/dashboard.html', context)

@login_required
def chat_view(request):
    """Chat view (placeholder)"""
    return render(request, 'coaching/chat.html')

@login_required
def exercises_view(request):
    """Exercises list view (placeholder)"""
    return render(request, 'coaching/exercises.html')

@login_required
def checkin_view(request):
    """Daily check-in view (placeholder)"""
    return render(request, 'coaching/checkin.html')

@login_required
def progress_view(request):
    """Progress view (placeholder)"""
    return render(request, 'coaching/progress.html')

@login_required
def resources_view(request):
    """Resources view (placeholder)"""
    return render(request, 'coaching/resources.html')

@login_required
def exercise_detail_view(request, pk):
    """Exercise detail view (placeholder)"""
    return render(request, 'coaching/exercise_detail.html')

from .models import (
    CoachingSession, CoachingMessage, CoachingExercise,
    UserExerciseCompletion, CoachingRecommendation,
    CoachingProgressMetric, DailyCheckIn, CoachNote
)
from .serializers import (
    CoachingSessionSerializer, CoachingMessageSerializer,
    CoachingExerciseSerializer, UserExerciseCompletionSerializer,
    CoachingRecommendationSerializer, CoachingProgressMetricSerializer,
    DailyCheckInSerializer, CoachNoteSerializer
)
from .services.coaching_service import CoachingService
from .services.ai_coach_engine import AICoachEngine


class CoachingSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing coaching sessions"""
    serializer_class = CoachingSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CoachingSession.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new coaching session"""
        title = request.data.get('title', 'Nouvelle Session de Coaching')
        theme = request.data.get('theme', '')
        description = request.data.get('description', '')
        
        session = CoachingService.create_session(
            user=request.user,
            title=title,
            theme=theme,
            description=description
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a coaching session"""
        session = self.get_object()
        content = request.data.get('content', '')
        
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user message
        user_message = CoachingService.add_message(
            session=session,
            sender='user',
            content=content
        )
        
        # Generate AI response
        context = {
            'theme': session.theme,
            'session_id': session.id,
            'user_profile': {}  # Add user profile data when available
        }
        
        ai_response_content = AICoachEngine.generate_response(content, context)
        
        ai_message = CoachingService.add_message(
            session=session,
            sender='ai',
            content=ai_response_content
        )
        
        # Analyze sentiment
        sentiment = AICoachEngine.analyze_sentiment(content)
        
        # Record metric
        CoachingProgressMetric.objects.create(
            user=request.user,
            session=session,
            metric_name='engagement',
            metric_value=sentiment['score'],
            metric_context={'sentiment': sentiment['sentiment']}
        )
        
        return Response({
            'user_message': CoachingMessageSerializer(user_message).data,
            'ai_message': CoachingMessageSerializer(ai_message).data
        })
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a session"""
        session = self.get_object()
        messages = CoachingService.get_session_history(session)
        serializer = CoachingMessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a session as completed"""
        session = self.get_object()
        session.status = 'completed'
        session.completed_at = timezone.now()
        session.save()
        
        # Generate completion note for coach
        CoachingService.generate_coach_note(
            user=request.user,
            session=session,
            note_type='completion',
            title='Session terminée',
            content=f"Session '{session.title}' terminée. "
                   f"Total messages: {session.total_messages}, "
                   f"Exercices complétés: {session.exercises_completed}",
            priority=2
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get progress data for a session"""
        session = self.get_object()
        
        # Update progress
        progress_percentage = CoachingService.update_session_progress(session)
        
        # Get metrics
        metrics = CoachingProgressMetric.objects.filter(
            user=request.user,
            session=session
        ).values('metric_name').annotate(
            avg_value=Avg('metric_value'),
            count=Count('id')
        )
        
        return Response({
            'progress_percentage': progress_percentage,
            'total_messages': session.total_messages,
            'exercises_completed': session.exercises_completed,
            'metrics': list(metrics),
            'sentiment_analysis': CoachingService.analyze_session_sentiment(session)
        })


class CoachingExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for coaching exercises"""
    serializer_class = CoachingExerciseSerializer
    permission_classes = [IsAuthenticated]
    queryset = CoachingExercise.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Get recommended exercises for the user"""
        theme = request.query_params.get('theme')
        limit = int(request.query_params.get('limit', 5))
        
        exercises = CoachingService.get_recommended_exercises(
            user=request.user,
            theme=theme,
            limit=limit
        )
        
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign an exercise to the user"""
        exercise = self.get_object()
        session_id = request.data.get('session_id')
        
        try:
            session = CoachingSession.objects.get(id=session_id, user=request.user)
        except CoachingSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        completion = CoachingService.assign_exercise(
            user=request.user,
            exercise=exercise,
            session=session
        )
        
        serializer = UserExerciseCompletionSerializer(completion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserExerciseCompletionViewSet(viewsets.ModelViewSet):
    """ViewSet for user exercise completions"""
    serializer_class = UserExerciseCompletionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserExerciseCompletion.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark exercise as started"""
        completion = self.get_object()
        completion.status = 'in_progress'
        completion.started_at = timezone.now()
        completion.save()
        
        serializer = self.get_serializer(completion)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark exercise as completed with feedback"""
        completion = self.get_object()
        
        user_notes = request.data.get('user_notes', '')
        reflection_responses = request.data.get('reflection_responses', {})
        rating = request.data.get('rating')
        
        CoachingService.complete_exercise(
            completion=completion,
            user_notes=user_notes,
            reflection_responses=reflection_responses,
            rating=rating
        )
        
        serializer = self.get_serializer(completion)
        return Response(serializer.data)


class DailyCheckInViewSet(viewsets.ModelViewSet):
    """ViewSet for daily check-ins"""
    serializer_class = DailyCheckInSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DailyCheckIn.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create or update daily check-in"""
        mood = request.data.get('mood')
        energy_level = request.data.get('energy_level')
        stress_level = request.data.get('stress_level')
        notes = request.data.get('notes', '')
        gratitude_entries = request.data.get('gratitude_entries', [])
        
        checkin = CoachingService.record_daily_checkin(
            user=request.user,
            mood=mood,
            energy_level=energy_level,
            stress_level=stress_level,
            notes=notes,
            gratitude_entries=gratitude_entries
        )
        
        serializer = self.get_serializer(checkin)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trends for check-in metrics"""
        days = int(request.query_params.get('days', 30))
        
        trends = {
            'mood': CoachingService.get_progress_data(request.user, 'mood', days),
            'energy_level': CoachingService.get_progress_data(request.user, 'energy_level', days),
            'stress_level': CoachingService.get_progress_data(request.user, 'stress_level', days),
        }
        
        return Response(trends)


class CoachingRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for coaching recommendations"""
    serializer_class = CoachingRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CoachingRecommendation.objects.filter(
            user=self.request.user,
            is_acted_upon=False
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now())
        )
    
    @action(detail=True, methods=['post'])
    def act_upon(self, request, pk=None):
        """Mark recommendation as acted upon"""
        recommendation = self.get_object()
        recommendation.is_acted_upon = True
        recommendation.save()
        
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data)


class CoachingDashboardViewSet(viewsets.ViewSet):
    """ViewSet for coaching dashboard data"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overview dashboard data"""
        user = request.user
        
        # Active sessions
        active_sessions = CoachingSession.objects.filter(
            user=user,
            status='active'
        ).count()
        
        # Total exercises completed
        exercises_completed = UserExerciseCompletion.objects.filter(
            user=user,
            status='completed'
        ).count()
        
        # Recent check-ins
        recent_checkins = DailyCheckIn.objects.filter(
            user=user,
            date__gte=timezone.now().date() - timedelta(days=7)
        ).count()
        
        # Average mood/stress
        avg_metrics = DailyCheckIn.objects.filter(
            user=user,
            date__gte=timezone.now().date() - timedelta(days=30)
        ).aggregate(
            avg_mood=Avg('mood'),
            avg_energy=Avg('energy_level'),
            avg_stress=Avg('stress_level')
        )
        
        # Pending recommendations
        pending_recommendations = CoachingRecommendation.objects.filter(
            user=user,
            is_acted_upon=False
        ).count()
        
        return Response({
            'active_sessions': active_sessions,
            'exercises_completed': exercises_completed,
            'check_ins_this_week': recent_checkins,
            'average_mood': round(avg_metrics['avg_mood'] or 0, 1),
            'average_energy': round(avg_metrics['avg_energy'] or 0, 1),
            'average_stress': round(avg_metrics['avg_stress'] or 0, 1),
            'pending_recommendations': pending_recommendations
        })