import logging

from django.core.management.base import BaseCommand
from impossible_travel.models import Config

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Command to update configs in the Config model"

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument("--overwrite", nargs="?", help="Option to overwrite (not append) the new elements to the targeted list")
        parser.add_argument("--ignored_users", nargs="?", type=str, default="", help="List of users to update in the Config model")
        parser.add_argument("--ignored_ips", nargs="?", type=str, default="", help="List of ips to update in the Config model")
        parser.add_argument("--allowed_countries", nargs="?", type=str, default="", help="List of countries to update in the Config model")
        parser.add_argument("--vip_users", nargs="?", type=str, default="", help="List of users to to update in the Config model")

    def handle(self, *args, **options):
        """Update or overwrite the configurations into the Config model"""
        logger = logging.getLogger()
        print(options)
        if not Config.objects.exists():
            self.stdout.write(self.style.ERROR("Error: There is no config to update"))
        else:
            config = Config.objects.all()[0]
            for opt in options:
                if options[opt]:
                    try:
                        self.stdout.write(f"Options:{options[opt]}")
                        if "overwrite" not in options:
                            getattr(config, opt).append(options[opt])
                        else:
                            setattr(config, opt, options[opt].split())
                        config.save()
                        self.stdout.write(self.style.SUCCESS(f"Correctly updated {opt} field. New entire value is: {getattr(config, opt)}"))
                    except AttributeError:
                        pass
