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
        parser.add_argument("--ignored_users", nargs="?", default=[], help="List of users to filter and to not consider in the detection")
        parser.add_argument("--ignored_ips", nargs="?", default=[], help="List of ips or subnets to not consider in the detection")
        parser.add_argument("--allowed_countries", nargs="?", default=[], help="List of countries from which the logins are always allowed")
        parser.add_argument("--vip_users", nargs="?", default=[], help="List of users to which pay particular attention")

    def handle(self, *args, **options):
        """Setup the configurations into the Config model"""
        logger = logging.getLogger()

        if Config.objects.all().exists():
            config_obj = Config.objects.all()[0]
        else:
            config_obj = Config.objects.create()
        if not options["ignored_users"] and not options["ignored_ips"] and not options["allowed_countries"] and not options["vip_users"]:
            # Set default values
            config_obj.ignored_users = IGNORED_USERS
            config_obj.ignored_ips = IGNORED_IPS
        else:
            for opt in options:
                if opt in ["ignored_users", "ignored_ips", "allowed_countries", "vip_users"]:
                    if not options[opt]:
                        setattr(config_obj, opt, [])
                    else:
                        setattr(config_obj, opt, options[opt].split(","))

        config_obj.save()

        # if Config.objects.all().exists():
        #     config_obj = Config.objects.all()[0]
        #     if not options["ignored_users"] and not options["ignored_ips"] and not options["allowed_countries"] and not options["vip_users"]:
        #         # Set default values
        #         config_obj.ignored_users = IGNORED_USERS
        #         config_obj.ignored_ips = IGNORED_IPS
        #     else:
        #         for opt in options:
        #             if options[opt] and type(options[opt]) is str:
        #                 try:
        #                     setattr(config_obj, opt, options[opt].split(','))
        #                 except AttributeError:
        #                     pass

        # else:
        #     if not options["ignored_users"] and not options["ignored_ips"] and not options["allowed_countries"] and not options["vip_users"]:
        #         config_obj = Config.objects.create(ignored_users=IGNORED_USERS, ignored_ips=IGNORED_IPS)
        #     else:
        #         config_obj = Config.objects.create()
        #         for opt in options:
        #             if options[opt] and type(options[opt]) is str:
        #                 try:
        #                     setattr(config_obj, opt, options[opt].split(','))
        #                 except AttributeError:
        #                     pass
        # config_obj.save()

        logger.info(
            f"Updated Config values - Ignored users: {config_obj.ignored_users}, Ignored IPs: {config_obj.ignored_ips}, Allowed countries: {config_obj.allowed_countries}, Vip users: {config_obj.vip_users}"
        )
