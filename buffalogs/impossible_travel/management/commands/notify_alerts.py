from django.core.management.base import BaseCommand
from impossible_travel.tasks import notify_alerts


class Command(BaseCommand):
    help = "Test notify alerts function"

    def handle(self, *args, **options):
        notify_alerts()
