import logging

from django.core.management.base import BaseCommand
from impossible_travel.constants import AlertFilterType, UserRiskScoreType
from impossible_travel.models import Config

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Create or Update multiple fields of Config model"

    def add_arguments(self, parser):
        # Optional arguments for fields in Config model
        # example of usage for default values: ./manage.py setup_config
        # example of usage with passed values: ./manage.py setup_config --ignored_users lory.goldoni,Lorena Goldoni --enabled_users Lorygold --ignored_ips 1.2.3.4,5.6.7.8 --allowed_countries Italy,France,Germany --vip_users Lorygold --alert_is_vip_only True --alert_minimum_risk_score Medium --filtered_alerts_types New Device --ignore_mobile_logins True --distance_accepted 200 --vel_accepted 50 --user_max_days 200 --login_max_days 100 --alert_max_days 100 --ip_max_days 100
        parser.add_argument("--ignored_users", nargs="?", type=str, help="List of users to be ignored from the detection")
        parser.add_argument("--enabled_users", nargs="?", type=str, help="List of selected users on which the detection will perform")
        parser.add_argument("--ignored_ips", nargs="?", type=str, help="List of countries to exclude from the detection, because 'trusted' for the customer")
        parser.add_argument("--allowed_countries", nargs="?", help="List of countries from which the logins are always allowed")
        parser.add_argument("--vip_users", nargs="?", help="List of users considered more sensitive")
        parser.add_argument("--alert_is_vip_only", nargs="?", type=bool, help="Flag to send alert only related to the users in the vip_users list")
        parser.add_argument(
            "--alert_minimum_risk_score",
            nargs="?",
            type=str,
            choices=[choice[1] for choice in UserRiskScoreType.choices()],
            help=f"Risk score threshold for alerts. Choices: {[choice[1] for choice in UserRiskScoreType.choices()]}",
        )  # choice[1] get the value of enum
        parser.add_argument(
            "--filtered_alerts_types",
            nargs="?",
            type=str,
            choices=[choice[1] for choice in AlertFilterType.choices()],
            help=f"List of alerts' types to exclude from the alerting. Choices: {[choice[1] for choice in AlertFilterType.choices()]}",
        )
        parser.add_argument("--ignore_mobile_logins", nargs="?", type=bool, help="Flag to ignore mobile devices from the detection")
        parser.add_argument(
            "--distance_accepted", nargs="?", type=int, help="Minimum distance (in Km) between two logins after which the impossible travel detection starts"
        )
        parser.add_argument(
            "--vel_accepted", nargs="?", type=int, help="Minimum velocity (in Km/h) between two logins after which the impossible travel detection starts"
        )
        parser.add_argument("--user_max_days", nargs="?", type=int, help="Days after which the users will be removed from the db")
        parser.add_argument("--login_max_days", nargs="?", type=int, help="Days after which the logins will be removed from the db")
        parser.add_argument("--alert_max_days", nargs="?", type=int, help="Days after which the alerts will be removed from the db")
        parser.add_argument("--ip_max_days", nargs="?", type=int, help="Days after which the IPs will be removed from the db")
        print(parser)

    def handle(self, *args, **options):
        """Setup the configurations into the Config model"""
        logger = logging.getLogger()

        if Config.objects.all().exists():
            config_obj = Config.objects.get(id=1)
        else:
            # if Config object does not exist, create it with default Config model values
            config_obj = Config.objects.create()
        print(options)
        # update field value if some option has been set
        for opt in options:
            print(opt)
        if not options["ignored_users"] and not options["ignored_ips"] and not options["allowed_countries"] and not options["vip_users"]:
            pass
        else:
            for opt in options:
                if opt in ["ignored_users", "ignored_ips", "allowed_countries", "vip_users"]:
                    if not options[opt]:
                        setattr(config_obj, opt, [])
                    else:
                        setattr(config_obj, opt, options[opt].split(","))

        config_obj.save()

        logger.info(
            f"Updated Config values - Ignored users: {config_obj.ignored_users}, Ignored IPs: {config_obj.ignored_ips}, Allowed countries: {config_obj.allowed_countries}, Vip users: {config_obj.vip_users}"
        )
