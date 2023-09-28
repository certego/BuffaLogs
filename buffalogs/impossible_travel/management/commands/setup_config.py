import logging

from django.core.management.base import BaseCommand
from impossible_travel.models import Config

logger = logging.getLogger()
IGNORED_USERS = ["N/A", "Not Available"]
IGNORED_IPS = ["127.0.0.1"]


class Command(BaseCommand):
    help = "Setup the Configs overwriting them"

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument("--ignored_users", nargs="?", action="append", default=[], help="List of users to filter and to not consider in the detection")
        parser.add_argument("--ignored_ips", nargs="?", action="append", default=[], help="List of ips or subnets to not consider in the detection")
        parser.add_argument("--allowed_countries", nargs="?", action="append", default=[], help="List of countries from which the logins are always allowed")
        parser.add_argument("--vip_users", nargs="?", action="append", default=[], help="List of users to which pay particular attention")

    def handle(self, *args, **options):
        """Setup the configurations into the Config model"""
        logger = logging.getLogger()
        if Config.objects.all().exists():
            config_obj = Config.objects.all()[0]
            if not options["ignored_users"] and not options["ignored_ips"] and not options["allowed_countries"] and not options["vip_users"]:
                # Set default values
                config_obj.ignored_users = IGNORED_USERS
                config_obj.ignored_ips = IGNORED_IPS
            else:
                config_obj.ignored_users = options["ignored_users"]
                config_obj.ignored_ips = options["ignored_ips"]
                config_obj.allowed_countries = options["allowed_countries"]
                config_obj.vip_users = options["vip_users"]
            config_obj.save()
        else:
            if not options["ignored_users"] and not options["ignored_ips"] and not options["allowed_countries"] and not options["vip_users"]:
                Config.objects.create(ignored_users=IGNORED_USERS, ignored_ips=IGNORED_IPS)
            else:
                Config.objects.create(
                    ignored_users=options["ignored_users"],
                    ignored_ips=options["ignored_ips"],
                    allowed_countries=options["allowed_countries"],
                    vip_users=options["vip_users"],
                )

        count_config = Config.objects.all().count()
        config = Config.objects.all()[0]
        print(f"COUNT CONFIGS:{count_config}")
        self.stdout.write(
            self.style.SUCCESS(
                f"Configs set correctly:\
                        \nIgnored users: {config.ignored_users}\
                        \nIgnored ips: {config.ignored_ips}\
                        \nAllowed countries: {config.allowed_countries}\
                        \nVip users: {config.vip_users}"
            )
        )
