from django.apps import apps
from django.core.management.base import BaseCommand, CommandParser

from impossible_travel.models import Alert, Config, Login, TaskSettings, User


class Command(BaseCommand):
    help = "Clear data on the models"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--model", nargs="?", type=str, help="Model to clear"
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        if options["model"]:
            if options["model"] in ["Config", "config"]:
                choice = input(
                    self.stdout.write(
                        "Are you sure you want to delete the Configurations model? [y/N]"
                    )
                )
                if choice in ["y", "Y"]:
                    Config.objects.all().delete()
                    self.stdout.write(
                        self.style.SUCCESS("Config model is correctly emptied")
                    )
                else:
                    self.stdout.write("Config model isn't emptied")
            else:
                try:
                    Model = apps.get_model(
                        "impossible_travel", options["model"].capitalize()
                    )
                    Model.objects.all().delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{Model} model is correctly emptied"
                        )
                    )
                except LookupError:
                    self.stdout.write(
                        self.style.ERROR(
                            f"{options['model']} model doesn't exist"
                        )
                    )
        else:
            Alert.objects.all().delete()
            Login.objects.all().delete()
            User.objects.all().delete()
            TaskSettings.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(
                    "All the models have been emptied, except the Config model"
                )
            )
