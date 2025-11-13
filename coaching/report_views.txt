import json
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import AssessmentResult
from pathlib import Path

def interpret_big_five(bf_scores):
    """
    bf_scores: dict with values 5..25
    returns dict with label and explanation per trait
    """
    interpretations = {}
    for trait, value in bf_scores.items():
        key = trait.lower()
        if key in ("openness", "ouverture", "ouverture_a_l_experience"):
            label = "Ouverture à l’expérience"
            desc = {
                "Faible": "Préfère les routines, peu d’intérêt pour la nouveauté ou les idées abstraites.",
                "Modéré": "Ouvert(e) à certaines idées nouvelles mais avec prudence.",
                "Élevé": "Très créatif(ve), curieux(se), attiré(e) par l'innovation et les expériences variées."
            }
        elif key in ("conscientiousness", "conscienciosite", "conscienciosité"):
            label = "Conscienciosité"
            desc = {
                "Faible": "Peut manquer de rigueur, difficulté à respecter les délais ou à s’organiser.",
                "Modéré": "Responsable dans les tâches importantes, mais manque parfois de planification.",
                "Élevé": "Très organisé(e), fiable, soucieux(se) de la qualité et de l’efficacité."
            }
        elif key in ("extraversion",):
            label = "Extraversion"
            desc = {
                "Faible": "Préfère travailler seul(e), réservé(e), peu énergique socialement.",
                "Modéré": "A l’aise dans certaines interactions, mais aime aussi la solitude.",
                "Élevé": "Sociable, assertif(ve), prend l’initiative dans les groupes."
            }
        elif key in ("agreeableness", "agreeabilite", "agréabilité"):
            label = "Agréabilité"
            desc = {
                "Faible": "Peut sembler distant(e), critique, peu conciliant(e).",
                "Modéré": "Coopératif(ve), mais peut défendre fermement ses opinions.",
                "Élevé": "Empathique, à l’écoute, privilégie l’harmonie dans les relations."
            }
        elif key in ("stability", "emotional_stability", "stabilité", "stabilité_émotionnelle", "neuroticism"):
            label = "Stabilité émotionnelle"
            desc = {
                "Faible": "Stressé(e), sensible aux critiques, anxieux(se).",
                "Modéré": "Équilibré(e) mais réagit parfois fortement au stress.",
                "Élevé": "Calme, confiant(e), gère bien les émotions et les tensions."
            }
        else:
            label = trait.capitalize()
            desc = {"Faible": "", "Modéré": "", "Élevé": ""}

        # thresholds: 5-11 Faible, 12-18 Modéré, 19-25 Élevé
        try:
            v = int(value)
        except Exception:
            v = 0
        if v <= 11:
            level = "Faible"
        elif v <= 18:
            level = "Modéré"
        else:
            level = "Élevé"

        interpretations[trait] = {
            "label": label,
            "value": v,
            "level": level,
            "explanation": desc.get(level, "")
        }
    return interpretations

def interpret_wellbeing(score):
    if score <= 14:
        return ("Bien‑être faible", "Risque de démotivation ou de surcharge — des actions sont recommandées.")
    if score <= 22:
        return ("Bien‑être modéré", "Points à améliorer ; prioriser actions ciblées.")
    return ("Bien‑être élevé", "Engagement et satisfaction professionnelle élevés.")

def interpret_resilience(score):
    if score <= 19:
        return ("Faible", "Difficultés à gérer émotions et imprévus — renforcer capacités.")
    if score <= 29:
        return ("Modéré", "Bonnes bases, à renforcer pour plus de fluidité.")
    return ("Élevé", "Maîtrise émotionnelle et bonne capacité d’adaptation.")

def interpret_disc(disc_dict):
    # disc_dict: {"D": x, "I": x, "S": x, "C": x}
    primary = None
    if disc_dict:
        items = {k: int(v or 0) for k, v in disc_dict.items()}
        primary = max(items.items(), key=lambda kv: kv[1])[0]
    descs = {
        "D": ("Dominant", "Décideur, orienté résultats, directif. Aime les challenges."),
        "I": ("Influent", "Charismatique, communicatif, inspirant."),
        "S": ("Stable", "Loyal, calme, patient. Privilégie la stabilité."),
        "C": ("Conforme", "Précis, analytique, rigoureux.")
    }
    primary_desc = descs.get(primary, ("", ""))
    return {"primary": primary, "primary_label": primary_desc[0], "primary_explanation": primary_desc[1], "raw": disc_dict or {}}


@login_required
def report_view(request):
    """
    Report page: uses the latest AssessmentResult for the logged-in user if available,
    otherwise loads the static sample_assessment.json (mock).
    """
    # try to fetch persisted assessment
    assessment = None
    try:
        assessment = request.user.assessments.first()
    except Exception:
        assessment = None

    if assessment:
        data = {
            "big_five": assessment.big_five,
            "disc": assessment.disc,
            "wellbeing_score": assessment.wellbeing_score,
            "resilience_score": assessment.resilience_score,
            "recommendations": assessment.recommendations,
            "created_at": assessment.created_at.isoformat(),
        }
    else:
        # fallback to sample JSON in static
        sample_path = Path(settings.BASE_DIR) / "coaching" / "static" / "coaching" / "data" / "sample_assessment.json"
        if sample_path.exists():
            try:
                with open(sample_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        else:
            data = {}

        # ensure keys exist
        data.setdefault("big_five", {"openness": 18, "conscientiousness": 15, "extraversion": 10, "agreeableness": 20, "stability": 12})
        data.setdefault("disc", {"D": 6, "I": 9, "S": 8, "C": 7})
        data.setdefault("wellbeing_score", 21)
        data.setdefault("resilience_score", 28)
        data.setdefault("recommendations", ["Commencer 5 minutes de respiration quotidienne", "Fixer un objectif SMART hebdomadaire"])

    big_five_interpret = interpret_big_five(data.get("big_five", {}))
    wellbeing_label, wellbeing_expl = interpret_wellbeing(data.get("wellbeing_score", 0))
    resilience_label, resilience_expl = interpret_resilience(data.get("resilience_score", 0))
    disc_info = interpret_disc(data.get("disc", {}))

    context = {
        "data_json": json.dumps(data, ensure_ascii=False),
        "big_five": big_five_interpret,
        "wellbeing": {"score": data.get("wellbeing_score", 0), "label": wellbeing_label, "explanation": wellbeing_expl},
        "resilience": {"score": data.get("resilience_score", 0), "label": resilience_label, "explanation": resilience_expl},
        "disc": disc_info,
    }
    return render(request, "coaching/report.html", context)