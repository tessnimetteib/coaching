from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sessions', views.CoachingSessionViewSet, basename='coaching-session')
router.register(r'exercises', views.CoachingExerciseViewSet, basename='coaching-exercise')
router.register(r'completions', views.UserExerciseCompletionViewSet, basename='exercise-completion')
router.register(r'checkins', views.DailyCheckInViewSet, basename='daily-checkin')
router.register(r'recommendations', views.CoachingRecommendationViewSet, basename='recommendation')
router.register(r'dashboard', views.CoachingDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('chat/', views.chat_view, name='chat'),
    path('exercises/', views.exercises_view, name='exercises'),
    path('exercises/<int:pk>/', views.exercise_detail_view, name='exercise_detail'),
    path('checkin/', views.checkin_view, name='checkin'),
    path('progress/', views.progress_view, name='progress'),
    path('resources/', views.resources_view, name='resources'),
    path('send_report/', views.send_report_to_coach, name='send_report_to_coach'),
    path('api/', include(router.urls)),
]