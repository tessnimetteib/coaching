from django.core.management.base import BaseCommand
from coaching.models import CoachingExercise


class Command(BaseCommand):
    help = 'Populate initial coaching exercises'
    
    def handle(self, *args, **kwargs):
        exercises = [
            {
                'title': 'Respiration 4-7-8',
                'description': 'Technique de respiration pour réduire le stress rapidement',
                'exercise_type': 'breathing',
                'theme': 'stress',
                'difficulty_level': 1,
                'estimated_duration': 10,
                'instructions': '''1. Asseyez-vous confortablement avec le dos droit
2. Placez le bout de votre langue contre vos dents de devant
3. Inspirez silencieusement par le nez pendant 4 secondes
4. Retenez votre souffle pendant 7 secondes
5. Expirez complètement par la bouche pendant 8 secondes
6. Répétez le cycle 4 fois''',
                'reflection_questions': [
                    'Comment vous sentez-vous après cet exercice?',
                    'Avez-vous remarqué des changements dans votre niveau de stress?',
                    'À quel moment pourriez-vous intégrer cet exercice?'
                ]
            },
            {
                'title': 'Journal de Gratitude',
                'description': 'Cultiver la reconnaissance pour renforcer le bien-être',
                'exercise_type': 'gratitude',
                'theme': 'confiance',
                'difficulty_level': 1,
                'estimated_duration': 15,
                'instructions': '''1. Trouvez un endroit calme
2. Notez 3 choses pour lesquelles vous êtes reconnaissant aujourd'hui
3. Pour chacune, écrivez pourquoi elle est importante
4. Prenez un moment pour ressentir cette gratitude''',
                'reflection_questions': [
                    'Quelles émotions avez-vous ressenties?',
                    'Comment cette pratique influence votre journée?',
                    'Qu\'avez-vous appris sur vous-même?'
                ]
            },
            {
                'title': 'Technique DESC',
                'description': 'Méthode structurée pour communiquer assertivement',
                'exercise_type': 'cbc',
                'theme': 'assertivité',
                'difficulty_level': 3,
                'estimated_duration': 20,
                'instructions': '''DESC: Décrire, Exprimer, Spécifier, Conséquences

1. Décrire: Décrivez objectivement la situation
2. Exprimer: Exprimez vos sentiments avec des "je"
3. Spécifier: Proposez une solution spécifique
4. Conséquences: Expliquez les conséquences positives

Exercice: Pensez à une situation et préparez votre communication.''',
                'reflection_questions': [
                    'Comment vous êtes-vous senti en préparant cela?',
                    'Qu\'est-ce qui était le plus difficile?',
                    'Comment pensez-vous que l\'autre personne réagira?'
                ]
            },
            {
                'title': 'Visualisation de Réussite',
                'description': 'Technique de visualisation pour renforcer la confiance',
                'exercise_type': 'visualization',
                'theme': 'confiance',
                'difficulty_level': 2,
                'estimated_duration': 15,
                'instructions': '''1. Fermez les yeux et respirez profondément
2. Imaginez une situation future où vous réussissez
3. Visualisez les détails: lieu, personnes, sons, couleurs
4. Ressentez les émotions de cette réussite
5. Remarquez votre posture, votre ton de voix
6. Ancrez cette sensation de confiance''',
                'reflection_questions': [
                    'Quelle situation avez-vous visualisée?',
                    'Quelles émotions avez-vous ressenties?',
                    'Comment utiliser cette énergie maintenant?'
                ]
            },
            {
                'title': 'Scan Corporel Mindfulness',
                'description': 'Pratique de pleine conscience pour gérer le stress',
                'exercise_type': 'mindfulness',
                'theme': 'stress',
                'difficulty_level': 2,
                'estimated_duration': 20,
                'instructions': '''1. Allongez-vous ou asseyez-vous confortablement
2. Fermez les yeux et concentrez-vous sur votre respiration
3. Portez attention sur chaque partie de votre corps:
   - Pieds et orteils
   - Jambes
   - Bassin et abdomen
   - Poitrine et dos
   - Bras et mains
   - Cou et tête
4. Notez les sensations sans jugement
5. Relâchez les tensions identifiées''',
                'reflection_questions': [
                    'Où avez-vous ressenti le plus de tension?',
                    'Avez-vous pu relâcher certaines zones?',
                    'Comment vous sentez-vous maintenant?'
                ]
            },
        ]
        
        created_count = 0
        for exercise_data in exercises:
            exercise, created = CoachingExercise.objects.get_or_create(
                title=exercise_data['title'],
                defaults=exercise_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {exercise.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully created {created_count} exercises!')
        )