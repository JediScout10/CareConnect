# users/management/commands/archive_old_actions.py
from django.core.management.base import BaseCommand
from users.models import UserCompletedAction
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Archives completed actions older than 7 days'

    def handle(self, *args, **options):
        archive_cutoff = timezone.now() - timedelta(days=7)
        
        try:
            old_actions = UserCompletedAction.objects.filter(
                status='completed',
                completed_at__lt=archive_cutoff
            )
            
            count = old_actions.update(status='archived')
            
            logger.info(f"Successfully archived {count} old actions")
            self.stdout.write(
                self.style.SUCCESS(f"Successfully archived {count} old actions")
            )
            
        except Exception as e:
            logger.error(f"Error archiving actions: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Error archiving actions: {str(e)}")
            )