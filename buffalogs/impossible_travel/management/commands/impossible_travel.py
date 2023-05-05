import logging
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from impossible_travel.tasks import exec_process_logs, process_logs, update_risk_level

logger = logging.getLogger()


class Command(BaseCommand):
    help = "Impossible Travel tasks call"

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument("start_date", nargs="?", type=str, help="--start_date")
        parser.add_argument("end_date", nargs="?", type=str, help="--end_date")

    def handle(self, *args, **options):
        """Run the detection manually with the commands: manage.py impossible_travel
        or with the start and end dates, for example: manage.py impossible_travel '2022-11-02 10:00:00' '2022-11-02 10:30:00'
        """
        if options["start_date"] and options["end_date"]:
            try:
                start_date_obj = datetime.strptime(options["start_date"], "%Y-%m-%d %H:%M:%S")
                end_date_obj = datetime.strptime(options["end_date"], "%Y-%m-%d %H:%M:%S")
                self.stdout.write(self.style.SUCCESS("Starting execution..."))
                exec_process_logs(start_date_obj, end_date_obj)
            except ValueError:
                logger.info("Time data does not match format '%Y-%m-%d %H:%M:%S'")
                self.stdout.write(self.style.ERROR("Error"))
        else:
            process_logs()

        update_risk_level()
