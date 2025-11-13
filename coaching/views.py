from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

# Import helper functions from coach_logic
from .coach_logic import (
    get_user_assessment,
    generate_strict_dialog_reply,
    recommend_exercises,
    recommend_resources,
    conversational_prompt_for_user,
    daily_motivation_for_user,
    human_coach_summary,
)

# Models, serializers, services
from .models import (
    CoachingSession, CoachingMessage, CoachingExercise,
    UserExerciseCompletion, CoachingRecommendation,
    CoachingProgressMetric, DailyCheckIn, CoachNote, AssessmentResult
)
from .serializers import (
    CoachingSessionSerializer, CoachingMessageSerializer,
    CoachingExerciseSerializer, UserExerciseCompletionSerializer,
    CoachingRecommendationSerializer, CoachingProgressMetricSerializer,
    DailyCheckInSerializer, CoachNoteSerializer
)
from .services.coaching_service import CoachingService
try:
    from .services.ai_coach_engine import AICoachEngine
except Exception:
    AICoachEngine = None


@login_required
def dashboard_view(request):
    from django.db.models import Avg
    user = request.user

    stats = {
        'active_sessions': CoachingSession.objects.filter(user=user, status='active').count(),
        'exercises_completed': UserExerciseCompletion.objects.filter(user=user, status='completed').count(),
        'average_mood': 0,
        'average_stress': 0,
    }

    recent_checkins = DailyCheckIn.objects.filter(
        user=user,
        date__gte=timezone.now().date() - timedelta(days=30)
    ).aggregate(
        avg_mood=Avg('mood'),
        avg_stress=Avg('stress_level')
    )

    stats['average_mood'] = round(recent_checkins['avg_mood'] or 0, 1)
    stats['average_stress'] = round(recent_checkins['avg_stress'] or 0, 1)

    try:
        recommended_exercises = CoachingService.get_recommended_exercises(user, limit=3)
    except Exception:
        recommended_exercises = CoachingExercise.objects.filter(is_active=True)[:3]

    assessment = get_user_assessment(request.user)
    coach_training_paths = []  # optional: generate_training_paths(assessment)
    coach_recommended_exercises = recommend_exercises(assessment)
    coach_recommended_resources = recommend_resources(assessment)
    coach_daily_motivation = daily_motivation_for_user(assessment)

    context = {
        'stats': stats,
        'recommended_exercises': recommended_exercises,
        'coach_assessment': assessment,
        'coach_training_paths': coach_training_paths,
        'coach_recommended_exercises': coach_recommended_exercises,
        'coach_recommended_resources': coach_recommended_resources,
        'coach_daily_motivation': coach_daily_motivation,
    }
    return render(request, 'coaching/dashboard.html', context)


@login_required
def chat_view(request):
    """
    Stateful chat view that uses the strict scripted generator.
    """
    user = request.user
    session = CoachingSession.objects.filter(user=user).order_by('-last_interaction').first()
    if not session:
        session = CoachingSession.objects.create(user=user, title="Session Active", theme="general", description="Session par défaut")

    messages_qs = CoachingMessage.objects.filter(session=session).order_by('timestamp')

    assessment = get_user_assessment(user)
    coach_intro = conversational_prompt_for_user(assessment)
    coach_recommended_exercises = recommend_exercises(assessment, max_items=3)
    coach_recommended_resources = recommend_resources(assessment, max_items=3)
    coach_daily_motivation = daily_motivation_for_user(assessment)

    if request.method == "POST":
        user_text = request.POST.get('message', '').strip()
        # debug log
        logger.info("chat POST user=%s state=%s text=%s", user.username, session.session_state, user_text)
        if user_text:
            CoachingMessage.objects.create(session=session, sender='user', content=user_text, metadata={})

            reply_text, actions, new_state = generate_strict_dialog_reply(user, user_text, assessment, current_state=session.session_state)

            CoachingMessage.objects.create(session=session, sender='ai', content=reply_text, metadata={})

            id_to_title = {
                "breath_4_7_8": "Respiration 4-7-8",
                "gratitude_3": "Carnet de gratitude",
                "smart_goal_15": "Objectif SMART 15 minutes",
            }

            for ex_id in actions.get('recommend_exercises', []):
                title = id_to_title.get(ex_id)
                if title:
                    exercise = CoachingExercise.objects.filter(title__icontains=title).first()
                    if exercise:
                        UserExerciseCompletion.objects.get_or_create(user=user, exercise=exercise, session=session, defaults={'status': 'assigned'})
                        CoachingRecommendation.objects.get_or_create(
                            user=user,
                            session=session,
                            title=f"Suggestion d'exercice: {exercise.title}",
                            defaults={
                                'recommendation_type': 'exercise',
                                'description': exercise.instructions[:200] if exercise.instructions else '',
                                'priority': 4,
                                'metadata': {'exercise_id': exercise.id}
                            }
                        )

            for rt in actions.get('recommendation_texts', []):
                CoachingRecommendation.objects.get_or_create(user=user, session=session, title="Recommandation du coach", description=rt, defaults={'recommendation_type': 'resource', 'priority': 3, 'metadata': {}})

            if actions.get('mark_completed'):
                assigned_qs = UserExerciseCompletion.objects.filter(user=user, session=session).exclude(status='completed')
                for comp in assigned_qs:
                    comp.status = 'completed'
                    comp.completed_at = timezone.now()
                    comp.save()
                CoachingRecommendation.objects.get_or_create(user=user, session=session, title="Confirmation: exercices complétés", description="L'utilisateur a indiqué avoir terminé ses exercices.", defaults={'recommendation_type': 'resource', 'priority': 2, 'metadata': {}})

            if new_state and new_state != session.session_state:
                session.session_state = new_state
                session.save(update_fields=['session_state', 'last_interaction'])

            session.last_interaction = timezone.now()
            session.total_messages = CoachingMessage.objects.filter(session=session).count()
            session.save()

            messages_qs = CoachingMessage.objects.filter(session=session).order_by('timestamp')

            context = {
                'messages': messages_qs,
                'coach_assessment': assessment,
                'coach_intro': coach_intro,
                'coach_recommended_exercises': coach_recommended_exercises,
                'coach_recommended_resources': coach_recommended_resources,
                'coach_daily_motivation': coach_daily_motivation,
            }
            return render(request, 'coaching/chat.html', context)

    context = {
        'messages': messages_qs,
        'coach_assessment': assessment,
        'coach_intro': coach_intro,
        'coach_recommended_exercises': coach_recommended_exercises,
        'coach_recommended_resources': coach_recommended_resources,
        'coach_daily_motivation': coach_daily_motivation,
    }
    return render(request, 'coaching/chat.html', context)


@login_required
def exercises_view(request):
    return render(request, 'coaching/exercises.html')


@login_required
def checkin_view(request):
    return render(request, 'coaching/checkin.html')


@login_required
def progress_view(request):
    return render(request, 'coaching/progress.html')


@login_required
def resources_view(request):
    return render(request, 'coaching/resources.html')


@login_required
def exercise_detail_view(request, pk):
    return render(request, 'coaching/exercise_detail.html')


class CoachingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CoachingSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CoachingSession.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        title = request.data.get('title', 'Nouvelle Session de Coaching')
        theme = request.data.get('theme', '')
        description = request.data.get('description', '')

        session = CoachingService.create_session(user=request.user, title=title, theme=theme, description=description)

        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        session = self.get_object()
        content = request.data.get('content', '')
        if not content:
            return Response({'error': 'Message content is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Add user message
        user_message = CoachingService.add_message(session=session, sender='user', content=content)

        # Static fallback response if AI engine absent
        ai_response_content = "Merci pour votre message. Le coach statique a enregistré votre demande."
        if AICoachEngine:
            try:
                ai_response_content = AICoachEngine.generate_response(content, {'theme': session.theme, 'session_id': session.id})
            except Exception:
                pass

        ai_message = CoachingService.add_message(session=session, sender='ai', content=ai_response_content)

        # Optional sentiment analysis
        sentiment_score = 0.0
        sentiment_label = ""
        if AICoachEngine:
            try:
                sentiment = AICoachEngine.analyze_sentiment(content)
                sentiment_score = sentiment.get('score', 0.0)
                sentiment_label = sentiment.get('sentiment', '')
            except Exception:
                pass

        CoachingProgressMetric.objects.create(user=request.user, session=session, metric_name='engagement', metric_value=sentiment_score, metric_context={'sentiment': sentiment_label})

        return Response({'user_message': CoachingMessageSerializer(user_message).data, 'ai_message': CoachingMessageSerializer(ai_message).data})


class CoachingExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CoachingExerciseSerializer
    permission_classes = [IsAuthenticated]
    queryset = CoachingExercise.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        theme = request.query_params.get('theme')
        limit = int(request.query_params.get('limit', 5))
        exercises = CoachingService.get_recommended_exercises(user=request.user, theme=theme, limit=limit)
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        exercise = self.get_object()
        session_id = request.data.get('session_id')
        try:
            session = CoachingSession.objects.get(id=session_id, user=request.user)
        except CoachingSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        completion = CoachingService.assign_exercise(user=request.user, exercise=exercise, session=session)
        serializer = UserExerciseCompletionSerializer(completion)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserExerciseCompletionViewSet(viewsets.ModelViewSet):
    serializer_class = UserExerciseCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserExerciseCompletion.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        completion = self.get_object()
        completion.status = 'in_progress'
        completion.started_at = timezone.now()
        completion.save()
        serializer = self.get_serializer(completion)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        completion = self.get_object()
        user_notes = request.data.get('user_notes', '')
        reflection_responses = request.data.get('reflection_responses', {})
        rating = request.data.get('rating')
        CoachingService.complete_exercise(completion=completion, user_notes=user_notes, reflection_responses=reflection_responses, rating=rating)
        serializer = self.get_serializer(completion)
        return Response(serializer.data)


class DailyCheckInViewSet(viewsets.ModelViewSet):
    serializer_class = DailyCheckInSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DailyCheckIn.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        mood = request.data.get('mood')
        energy_level = request.data.get('energy_level')
        stress_level = request.data.get('stress_level')
        notes = request.data.get('notes', '')
        gratitude_entries = request.data.get('gratitude_entries', [])
        checkin = CoachingService.record_daily_checkin(user=request.user, mood=mood, energy_level=energy_level, stress_level=stress_level, notes=notes, gratitude_entries=gratitude_entries)
        serializer = self.get_serializer(checkin)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        days = int(request.query_params.get('days', 30))
        trends = {'mood': CoachingService.get_progress_data(request.user, 'mood', days), 'energy_level': CoachingService.get_progress_data(request.user, 'energy_level', days), 'stress_level': CoachingService.get_progress_data(request.user, 'stress_level', days)}
        return Response(trends)


class CoachingRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CoachingRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CoachingRecommendation.objects.filter(user=self.request.user, is_acted_upon=False).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=timezone.now()))

    @action(detail=True, methods=['post'])
    def act_upon(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.is_acted_upon = True
        recommendation.save()
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data)


class CoachingDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        user = request.user
        active_sessions = CoachingSession.objects.filter(user=user, status='active').count()
        exercises_completed = UserExerciseCompletion.objects.filter(user=user, status='completed').count()
        recent_checkins = DailyCheckIn.objects.filter(user=user, date__gte=timezone.now().date() - timedelta(days=7)).count()
        avg_metrics = DailyCheckIn.objects.filter(user=user, date__gte=timezone.now().date() - timedelta(days=30)).aggregate(avg_mood=Avg('mood'), avg_energy=Avg('energy_level'), avg_stress=Avg('stress_level'))
        pending_recommendations = CoachingRecommendation.objects.filter(user=user, is_acted_upon=False).count()
        return Response({'active_sessions': active_sessions, 'exercises_completed': exercises_completed, 'check_ins_this_week': recent_checkins, 'average_mood': round(avg_metrics['avg_mood'] or 0, 1), 'average_energy': round(avg_metrics['avg_energy'] or 0, 1), 'average_stress': round(avg_metrics['avg_stress'] or 0, 1), 'pending_recommendations': pending_recommendations})


@require_POST
@login_required
def send_report_to_coach(request):
    user_id = request.POST.get('user_id')
    if str(request.user.id) != str(user_id):
        return HttpResponseForbidden("Invalid user.")
    assessment = get_user_assessment(request.user)
    summary_text = human_coach_summary(assessment)
    CoachNote.objects.create(user=request.user, session=None, generated_by_ai=True, note_type='report', title='Rapport envoyé au coach humain', content=summary_text, priority=3)
    messages.success(request, "Le rapport a été enregistré pour le coach humain.")
    return redirect(request.META.get('HTTP_REFERER', '/coaching/'))