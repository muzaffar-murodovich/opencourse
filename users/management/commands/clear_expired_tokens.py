from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import TelegramAuthToken


class Command(BaseCommand):
    help = "Delete TelegramAuthToken rows past their 10-minute TTL."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=10)
        deleted, _ = TelegramAuthToken.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired token(s)."))
