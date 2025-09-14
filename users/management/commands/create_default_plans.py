# users\management\commands\create_default_plans.py
from django.core.management.base import BaseCommand
from users.models import ActionPlan

DEFAULT_PLANS = {
    "Excellent": {
        "title": "Maintain Your Wellness",
        "steps": [
            "Share your positive habits with a friend",
            "Try a new mindfulness activity",
            "Journal about what's working well"
        ]
    },
    "Good": {
        "title": "Boost Your Wellbeing",
        "steps": [
            "10-minute meditation session",
            "Identify one stressor to address",
            "Connect with someone today"
        ]
    },
    "Caution": {
        "title": "Prioritize Your Mental Health",
        "steps": [
            "Practice deep breathing for 5 minutes",
            "Reach out to a support person",
            "Consider professional help options"
        ]
    }
}

class Command(BaseCommand):
    help = 'Creates default action plans'
    
    def handle(self, *args, **options):
        for category, data in DEFAULT_PLANS.items():
            ActionPlan.objects.update_or_create(
                category=category,
                defaults=data
            )
        self.stdout.write(self.style.SUCCESS('Successfully created action plans'))