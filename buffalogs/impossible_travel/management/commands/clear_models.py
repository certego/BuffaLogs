from django.core.management.base import BaseCommand
from impossible_travel.models import Alert, Login, TaskSettings, User


class Command(BaseCommand):
    help = "Clear Alert, Login, User and TaskSettings models"

    def handle(self, *args, **options):
        Alert.objects.all().delete()
        Login.objects.all().delete()
        User.objects.all().delete()
        TaskSettings.objects.all().delete()
