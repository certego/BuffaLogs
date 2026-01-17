from impossible_travel.management.commands.base_command import \
    TaskLoggingCommand
from impossible_travel.tasks import notify_alerts


class Command(TaskLoggingCommand):
    help = "Test notify alerts function"

    def handle(self, *args, **options):
        notify_alerts()
