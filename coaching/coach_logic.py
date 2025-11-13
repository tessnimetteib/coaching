from typing import Dict, List, Any, Optional, Tuple
from .models import AssessmentResult
from django.contrib.auth import get_user_model
import re

User = get_user_model()

PARCOURS = {}  # kept minimal for brevity

STATIC_EXERCISES = [
    {"id": "breath_4_7_8", "title": "Respiration 4-7-8", "instructions": "Inspirez 4s, retenez 7s, expirez 8s. Répétez 4 fois."},
    {"id": "smart_goal_15", "title": "Objectif SMART 15 minutes", "instructions": "Définissez un objectif SMART pour aujourd'hui."},
    {"id": "gratitude_3", "title": "Carnet de gratitude (3 items)", "instructions": "Notez 3 choses positives aujourd'hui."}
]

STATIC_RESOURCES = [
    {"title": "Vidéo: Respiration guidée 5 min", "url": "https://example.com/breathing-video"},
    {"title": "Guide: Organiser sa journée (PDF)", "url": "https://example.com/productivity-guide"},
    {"title": "Article: Renforcer sa résilience", "url": "https://example.com/resilience-article"}
]


def get_user_assessment(user: User) -> Optional[AssessmentResult]:
    """Retrieve the first assessment for a user"""
    try:
        return user.assessments.first()
    except Exception:
        return None


def recommend_exercises(assessment: Optional[AssessmentResult], max_items: int = 3) -> List[Dict[str, Any]]:
    """Recommend exercises based on assessment (fallback function)"""
    if not assessment:
        return STATIC_EXERCISES[:max_items]
    bf = assessment.big_five or {}
    stability = int(bf.get("stability", 0) or 0)
    if stability <= 11 or assessment.wellbeing_score <= 14:
        return [STATIC_EXERCISES[0], STATIC_EXERCISES[2]][:max_items]
    return [STATIC_EXERCISES[1], STATIC_EXERCISES[0]][:max_items]


def recommend_resources(assessment: Optional[AssessmentResult], max_items: int = 3) -> List[Dict[str, str]]:
    """Recommend static resources"""
    return STATIC_RESOURCES[:max_items]


def conversational_prompt_for_user(assessment: Optional[AssessmentResult]) -> str:
    """Generate initial conversational prompt (fallback function)"""
    if not assessment:
        return "Bonjour — je suis votre coach NextMind. Dites-moi comment ça va aujourd'hui ?"
    wb = int(assessment.wellbeing_score or 0)
    stability = int(assessment.big_five.get("stability", 0) if assessment.big_five else 0)
    extraversion = int(assessment.big_five.get("extraversion", 0) if assessment.big_five else 0)
    if wb <= 14 or stability <= 11:
        return ("Bonjour — je vois que vous traversez une période délicate. "
                "Souhaitez-vous commencer par un exercice de respiration de 3 à 5 minutes ?")
    if extraversion >= 19:
        return ("Salut ! Prêt(e) à avancer aujourd'hui ? J'ai des exercices courts pour booster votre journée.")
    return ("Bonjour — je suis votre coach NextMind. Comment puis-je vous aider aujourd'hui ?")


def daily_motivation_for_user(assessment: Optional[AssessmentResult]) -> str:
    """Generate daily motivation message"""
    if not assessment:
        return "Chaque jour est une nouvelle opportunité de progresser. Commençons ensemble !"
    
    wb = int(assessment.wellbeing_score or 0)
    stability = int(assessment.big_five.get("stability", 0) if assessment.big_five else 0)
    
    if wb <= 14 or stability <= 11:
        return "Rappelez-vous : chaque petit pas compte. Vous êtes plus fort(e) que vous ne le pensez."
    
    return "Aujourd'hui est une belle journée pour avancer vers vos objectifs. Vous êtes sur la bonne voie !"


def human_coach_summary(assessment: Optional[AssessmentResult]) -> str:
    """Generate summary report for human coach"""
    if not assessment:
        return ("Rapport Coach IA\n\n"
                "L'utilisateur n'a pas encore complété d'évaluation psychologique.\n"
                "Recommandation: Commencer par un diagnostic NextMind complet.")
    
    wb = int(assessment.wellbeing_score or 0)
    bf = assessment.big_five or {}
    stability = int(bf.get("stability", 0) or 0)
    extraversion = int(bf.get("extraversion", 0) or 0)
    openness = int(bf.get("openness", 0) or 0)
    conscientiousness = int(bf.get("conscientiousness", 0) or 0)
    agreeableness = int(bf.get("agreeableness", 0) or 0)
    
    report = "=== RAPPORT COACH IA POUR LE COACH HUMAIN ===\n\n"
    report += f"Bien-être général: {wb}/100\n"
    report += f"Big Five:\n"
    report += f"  - Stabilité émotionnelle: {stability}/30\n"
    report += f"  - Extraversion: {extraversion}/30\n"
    report += f"  - Ouverture: {openness}/30\n"
    report += f"  - Conscienciosité: {conscientiousness}/30\n"
    report += f"  - Agréabilité: {agreeableness}/30\n\n"
    
    report += "POINTS D'ATTENTION:\n"
    if wb <= 14:
        report += "- Bien-être faible: L'utilisateur traverse une période difficile. Prioriser le soutien émotionnel.\n"
    if stability <= 11:
        report += "- Stabilité émotionnelle faible: Exercices de gestion du stress recommandés.\n"
    if extraversion <= 11:
        report += "- Introversion marquée: Favoriser des exercices individuels plutôt que de groupe.\n"
    
    report += "\nRECOMMANDATIONS:\n"
    report += "- Suivi régulier des exercices de respiration et gratitude\n"
    report += "- Objectifs SMART adaptés au profil\n"
    report += "- Séances de coaching personnalisées selon le profil Big Five\n\n"
    
    report += "Ce rapport a été généré automatiquement par l'IA Coach NextMind.\n"
    
    return report


def generate_strict_dialog_reply(user, user_message: str, assessment: Optional[AssessmentResult], current_state: str = "idle") -> Tuple[str, Dict[str, Any], str]:
    """
    Strict static scripted dialog flow following exact scenario.
    Returns (reply_text, actions_dict, new_state)
    
    Flow:
    1. User: "I'm back, I need help" -> Coach: "Oh Tasneem, I'm here for your help."
    2. User: "ok" -> Coach: "I've heard that your tone was overwhelmed..." 
    3. User: "ok thanks" -> Coach: "I have for today exercises for you..."
    4. User: "I'm back" or "done" -> Coach: "Hi Tasneem, thank you for coming back..."
    """
    text = (user_message or "").strip().lower()
    actions: Dict[str, Any] = {"recommend_exercises": [], "recommendation_texts": [], "mark_completed": False}
    
    # Normalize current_state - treat None, empty, or "idle" as the start state
    if not current_state or current_state in ["", "idle", "None"]:
        current_state = "idle"
    
    new_state = current_state
    name = getattr(user, "first_name", None) or getattr(user, "username", "Tasneem")

    # Regex patterns for matching user input
    re_back = re.compile(r"\b(i['']?m\s+back|i\s+am\s+back|i\s+need\s+help|need\s+help)\b", re.I)
    re_ok_first = re.compile(r"^\s*(ok|okay|oui|yes)\s*$", re.I)
    re_ok_thanks = re.compile(r"\b(ok\s*,?\s*thanks?|okay\s*thanks?|merci)\b", re.I)
    re_done = re.compile(r"\b(i['']?m\s+back|done|finished|fini|terminé)\b", re.I)

    # === STEP 1: User says "I'm back, I need help" ===
    # This should work from idle state
    if current_state == "idle" and re_back.search(text):
        reply = f"Oh {name}, I'm here for your help."
        new_state = "waiting_for_ok"
        return reply, actions, new_state

    # === STEP 2: User says "ok" -> Coach explains and suggests exercises ===
    if current_state == "waiting_for_ok" and re_ok_first.search(text):
        reply = ("I've heard that your tone was overwhelmed, it was stressed, and I'm here to help you. "
                 "First, I will suggest things to do for you — please stick to them.")
        new_state = "waiting_for_ok_thanks"
        return reply, actions, new_state

    # === STEP 3: User says "ok thanks" -> Coach assigns exercises ===
    if current_state == "waiting_for_ok_thanks" and re_ok_thanks.search(text):
        reply = ("I have for today exercises for you. Please do them. I will add them in the Exercises section — check it out. "
                 "Then tell me after finishing the exercise, come back to me. I am waiting for you.")
        actions["recommend_exercises"] = ["breath_4_7_8", "gratitude_3"]
        new_state = "waiting_for_done"
        return reply, actions, new_state

    # === STEP 4: User says "I'm back" or "done" -> Coach gives final message and resources ===
    if current_state == "waiting_for_done" and re_done.search(text):
        reply = (f"Hi {name}, thank you for coming back. I have the result of your exercise and I'm so happy that you finished it all. "
                 "Now as we finished our daily exercise, I will give you some resources — please check it out. "
                 "If you need any help, I'm here. You're doing well; after our sessions together the AI will be better and you will feel much better.")
        actions["mark_completed"] = True
        actions["recommendation_texts"].append("Resources: Breathing video; Productivity guide; Resilience article.")
        new_state = "completed"
        return reply, actions, new_state

    # === FALLBACK: Guide user to follow the exact flow ===
    if current_state == "idle":
        reply = f"Hi {name}! To start our coaching session, please say: \"I'm back, I need help\""
    elif current_state == "waiting_for_ok":
        reply = "Please reply with 'ok' to continue."
    elif current_state == "waiting_for_ok_thanks":
        reply = "Please reply with 'ok thanks' so I can assign your exercises."
    elif current_state == "waiting_for_done":
        reply = "Please complete your exercises and come back to say 'I'm back' or 'done'."
    elif current_state == "completed":
        reply = "Great! You've completed today's session. Come back tomorrow to start a new one!"
    else:
        # Unknown state - reset to idle
        reply = f"Hi {name}! To start our coaching session, please say: \"I'm back, I need help\""
        new_state = "idle"
    
    return reply, actions, new_state