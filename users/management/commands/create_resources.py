from django.core.management.base import BaseCommand
from users.models import Resource

class Command(BaseCommand):
    help = 'Creates initial resources for the chatbot'

    def handle(self, *args, **kwargs):
        # Define resources
        resources = [
            # Breathing techniques
            {
                'title': '4-7-8 Breathing Technique',
                'description': 'A simple breathing exercise to reduce anxiety and stress',
                'resource_type': 'breathing',
                'content': 'Breathe in through your nose for 4 seconds, hold for 7 seconds, then exhale through your mouth for 8 seconds. Repeat 4 times.'
            },
            {
                'title': 'Box Breathing',
                'description': 'A calming breathing technique used by Navy SEALs',
                'resource_type': 'breathing',
                'content': 'Breathe in for 4 seconds, hold for 4 seconds, breathe out for 4 seconds, hold for 4 seconds. Repeat.'
            },
            
            # Journaling prompts
            {
                'title': 'Gratitude Journal',
                'description': 'Focus on the positive aspects of your life',
                'resource_type': 'journaling',
                'content': 'Write down three things you\'re grateful for today and why they matter to you.'
            },
            {
                'title': 'Challenge Reflection',
                'description': 'Process difficult situations',
                'resource_type': 'journaling',
                'content': 'Describe a challenge you\'re facing. What are three possible ways to address it? What would success look like?'
            },
            
            # Stress management
            {
                'title': '5-4-3-2-1 Grounding Technique',
                'description': 'A mindfulness exercise to reduce anxiety',
                'resource_type': 'stress_management',
                'content': 'Name 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste.'
            },
            {
                'title': 'Progressive Muscle Relaxation',
                'description': 'Reduce physical tension in your body',
                'resource_type': 'stress_management',
                'content': 'Tense each muscle group for 5 seconds, then relax for 30 seconds. Start with your feet and work up to your face.'
            },
            
            # Articles
            {
                'title': 'Understanding Anxiety',
                'description': 'Learn about the causes and symptoms of anxiety',
                'resource_type': 'article',
                'content': 'https://www.nimh.nih.gov/health/topics/anxiety-disorders'
            },
            {
                'title': 'Depression: More Than Just Feeling Sad',
                'description': 'Comprehensive guide to depression',
                'resource_type': 'article',
                'content': 'https://www.nimh.nih.gov/health/topics/depression'
            },
            
            # Videos
            {
                'title': 'Guided Meditation for Anxiety',
                'description': '10-minute guided meditation',
                'resource_type': 'video',
                'content': 'https://www.youtube.com/watch?v=O-6f5wQXSu8'
            },
            {
                'title': 'Understanding Stress Response',
                'description': 'How stress affects your body and mind',
                'resource_type': 'video',
                'content': 'https://www.youtube.com/watch?v=3aDXM5H-Fuw'
            },
            
            # Helplines
            {
                'title': 'National Suicide Prevention Lifeline',
                'description': '24/7 support for people in distress',
                'resource_type': 'helpline',
                'content': '1-800-273-8255'
            },
            {
                'title': 'Crisis Text Line',
                'description': 'Text HOME to 741741 to connect with a Crisis Counselor',
                'resource_type': 'helpline',
                'content': 'Text HOME to 741741'
            }
        ]
        
        # Create resources
        created_count = 0
        for resource_data in resources:
            resource, created = Resource.objects.get_or_create(
                title=resource_data['title'],
                defaults={
                    'description': resource_data['description'],
                    'resource_type': resource_data['resource_type'],
                    'content': resource_data['content'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} resources'))