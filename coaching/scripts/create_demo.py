"""
Run this inside Django shell:
python manage.py shell -c "exec(open('coaching/scripts/create_demo.py').read())"
This script creates:
 - demo_user (username: demo_user / password: demo1234) if not present
 - an AssessmentResult for demo_user
 - a CoachingSession and two CoachingMessage entries
 - two example CoachingExercise entries
 - a CoachingRecommendation entry
"""
from django.contrib.auth import get_user_model
from coaching.models import (
    AssessmentResult, CoachingSession, CoachingMessage,
    CoachingExercise, CoachingRecommendation
)

User = get_user_model()

username = "demo_user"
password = "demo1234"
email = "demo@example.com"

u, created = User.objects.get_or_create(username=username, defaults={"email": email, "first_name": "Demo"})
if created:
    u.set_password(password)
    u.save()
    print(f"Created user {username} with password {password}")
else:
    print(f"User {username} already exists")

# Create AssessmentResult if not exists
assessment_defaults = {
    "big_five": {"openness":20,"conscientiousness":17,"extraversion":12,"agreeableness":21,"stability":14},
    "disc": {"D":7,"I":11,"S":8,"C":6},
    "wellbeing_score": 24,
    "resilience_score": 33,
    "recommendations": [
        "Pratique quotidienne de respiration 4-7-8 (5 minutes).",
        "Planification hebdomadaire: sélectionner 3 tâches prioritaires.",
    ]
}
assessment, a_created = AssessmentResult.objects.get_or_create(user=u, defaults=assessment_defaults)
print("Assessment:", "created" if a_created else "exists", assessment.pk)

# Create a demo coaching session
session, s_created = CoachingSession.objects.get_or_create(user=u, title="Session de démonstration", defaults={"theme":"confiance", "description":"Session d'exemple"})
print("Session id:", session.id)

# Add chat history messages (only if none exist for this session)
if not CoachingMessage.objects.filter(session=session).exists():
    CoachingMessage.objects.create(session=session, sender='user', content="Bonjour coach, je me sens un peu tendu aujourd'hui.")
    CoachingMessage.objects.create(session=session, sender='ai', content="Bonjour ! D'accord. Voulez-vous commencer par un exercice de respiration 4-7-8 ?")
    print("Added two demo messages")
else:
    print("Demo messages already exist for session")

# Create example exercises (if none exist)
if not CoachingExercise.objects.filter(title="Respiration 4-7-8").exists():
    CoachingExercise.objects.create(
        title="Respiration 4-7-8",
        description="Exercice de respiration pour réduire le stress",
        exercise_type="breathing",
        theme="stress",
        difficulty_level=1,
        estimated_duration=5,
        instructions="Inspirez 4s, retenez 7s, expirez 8s. Répétez 4 fois.",
        reflection_questions=["Comment vous sentez-vous après l'exercice ?"]
    )
    CoachingExercise.objects.create(
        title="Objectif SMART 15 minutes",
        description="Définir un petit objectif SMART pour la journée",
        exercise_type="smart_goals",
        theme="productivity",
        difficulty_level=2,
        estimated_duration=15,
        instructions="Définissez un objectif SMART pour aujourd'hui (Spécifique, Mesurable, Atteignable, Réaliste, Temporel).",
        reflection_questions=["Cette action est-elle réalisable aujourd'hui ? Pourquoi ?"]
    )
    print("Example exercises created")
else:
    print("Example exercises already exist")

# optional: add a recommendation entry for the user
if not CoachingRecommendation.objects.filter(user=u, title__icontains="Respiration 4-7-8").exists():
    CoachingRecommendation.objects.create(
        user=u,
        session=session,
        recommendation_type='exercise',
        title="Faire respiration 4-7-8",
        description="Exercice de 5 minutes pour calmer",
        priority=4
    )
    print("Recommendation created")
else:
    print("Recommendation already exists")

print("Demo data setup complete. Login with:", username, "password:", password)