import random
from typing import Dict, Optional


class AICoachEngine:
    """Placeholder AI Coach Engine"""
    
    GREETINGS = [
        "Bonjour! Comment puis-je vous aider?",
        "Ravi de vous revoir!",
        "Hello! Prêt pour une session?",
    ]
    
    @classmethod
    def generate_response(cls, user_message: str, context: Dict = None) -> str:
        """Generate AI response"""
        msg = user_message.lower()
        
        if any(w in msg for w in ['bonjour', 'salut', 'hello']):
            return random.choice(cls.GREETINGS)
        
        if any(w in msg for w in ['stress', 'anxieux']):
            return "Je comprends. Avez-vous essayé la respiration?"
        
        if any(w in msg for w in ['bien', 'mieux']):
            return "Excellent! Qu'est-ce qui a aidé?"
        
        return "Je vous écoute. Dites-m'en plus..."
    
    @classmethod
    def analyze_sentiment(cls, text: str) -> Dict:
        """Basic sentiment analysis"""
        positive = ['bien', 'bon', 'excellent', 'heureux']
        negative = ['mal', 'stress', 'anxieux', 'peur']
        
        text_lower = text.lower()
        pos_count = sum(1 for w in positive if w in text_lower)
        neg_count = sum(1 for w in negative if w in text_lower)
        
        if pos_count > neg_count:
            return {'sentiment': 'positive', 'score': 0.7}
        elif neg_count > pos_count:
            return {'sentiment': 'negative', 'score': 0.3}
        return {'sentiment': 'neutral', 'score': 0.5}