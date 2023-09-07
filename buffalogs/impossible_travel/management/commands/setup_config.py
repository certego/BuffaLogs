import logging

from django.core.management.base import BaseCommand
from impossible_travel.models import Config

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Command to setup configs in the Config model"

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument("--ignored_users", nargs="?", action="append", default=[], help="List of users to filter and to not consider in the detection")
        parser.add_argument("--ignored_ips", nargs="?", action="append", default=[], help="List of ips or subnets to not consider in the detection")
        parser.add_argument("--allowed_countries", nargs="?", action="append", default=[], help="List of countries from which the logins are always allowed")
        parser.add_argument("--vip_users", nargs="?", action="append", default=[], help="List of users to which pay particular attention")

    def handle(self, *args, **options):
        """Setup the configurations into the Config model"""
        logger = logging.getLogger()
        if not Config.objects.exists():
            Config.objects.create(
                ignored_users=options["ignored_users"],
                ignored_ips=options["ignored_ips"],
                allowed_countries=options["allowed_countries"],
                vip_users=["vip_users"],
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Configs set correctly:\
                                                \nIgnored users: {options['ignored_users']}\
                                                \nIgnored ips: {options['ignored_ips']}\
                                                \nAllowed countries: {options['allowed_countries']}\
                                                \nVip users: {options['vip_users']}"
                )
            )
        else:
            self.stdout.write(self.style.ERROR("Error: Configs already exist. Use the modify_config or the clear_models commands"))
