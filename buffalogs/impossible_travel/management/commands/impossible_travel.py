from django.core.management.base import BaseCommand
from impossible_travel.tasks import process_logs, update_risk_level


class Command(BaseCommand):
    help = "Impossible Travel tasks call"

    def handle(self, *args, **options):
        process_logs()
        update_risk_level()
