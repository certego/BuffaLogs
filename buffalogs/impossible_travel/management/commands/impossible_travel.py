from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from impossible_travel.tasks import process_logs, update_risk_level


class Command(BaseCommand):
    help = "Impossible Travel tasks call"

    def handle(self, *args, **options):
        interval = 30
        start_date = timezone.datetime(2023, 2, 22, 15, 0, 0)
        end_date = timezone.datetime(2023, 2, 22, 23, 59, 59)
        current_date = start_date
        while current_date < end_date:
            new_date = current_date + timedelta(minutes=interval)
            process_logs()
            current_date = new_date
            update_risk_level()
